#!/usr/bin/env python3
import json
from pathlib import Path

import numpy as np
import pandas as pd

from msv3.engine import analyze_frame
from msv3.execution import build_execution_plan
from msv3.features import add_indicators, rsi_context
from msv3.levels import attach_roles, classify_role, discover_trend_bridge, merge_levels
from msv3.setups import detect_box_setup, detect_high_trend, detect_bridge_setup, detect_level_retest
from msv3.review import build_review_context, select_deep_review_queue

ROOT = Path(__file__).resolve().parents[1]
cfg = json.loads((ROOT / "market-structure-v3-config.json").read_text(encoding="utf-8"))


# 1) Role state is separate from the level itself.
idx = pd.bdate_range("2026-01-01", periods=3)
level = {
    "line":105.0, "zoneLow":100.0, "zoneHigh":110.0,
    "kinds":["GENERIC_LEVEL"], "evidence":["SYNTH"], "evidenceCount":3, "strength":3.0,
    "importance":"CORE",
}
decision_df = pd.DataFrame({
    "Open":[95.0,97.0,103.0], "High":[99.0,99.0,108.0], "Low":[94.0,95.0,101.0],
    "Close":[97.0,98.0,105.0], "Volume":[1e6,1e6,1e6],
}, index=idx)
assert classify_role(decision_df, level)["state"] == "DECISION_ZONE"

failed_df = pd.DataFrame({
    "Open":[112.0,111.0,111.0], "High":[114.0,113.0,113.0], "Low":[111.0,110.0,97.0],
    "Close":[112.0,112.0,98.0], "Volume":[1e6,1e6,1.2e6],
}, index=idx)
failed = classify_role(failed_df, level)
assert failed["state"] == "FAILED_BREAKOUT"
assert "FAILED_BREAKOUT" in failed["warnings"]

# Weak supporting swing-like levels may still have a failed-breakout role state, but
# they must not emit a hard structure warning by themselves.
supporting_level = dict(level)
supporting_level["importance"] = "SUPPORTING"
supporting_failed = classify_role(failed_df, supporting_level)
assert supporting_failed["state"] == "FAILED_BREAKOUT"
assert "FAILED_BREAKOUT" not in supporting_failed["warnings"]

accepted_df = pd.DataFrame({
    "Open":[111.0,112.0,113.0], "High":[113.0,114.0,115.0], "Low":[110.5,111.0,112.0],
    "Close":[112.0,113.0,114.0], "Volume":[1e6,1e6,1e6],
}, index=idx)
assert classify_role(accepted_df, level)["state"] == "ACCEPTED_SUPPORT"


# 2) Spring is a reclaim state, not an automatic prediction.
box = {
    "startDate":"20260101","endDate":"20260201","sessions":30,"endLag":1,
    "upper":110.0,"lower":100.0,"boxClose":105.0,"rangePct":10.0,
    "upperTouches":3,"lowerTouches":3,
}
spring_df = pd.DataFrame({
    "Open":[104.0,103.0,101.0], "High":[106.0,105.0,104.0], "Low":[101.0,100.5,95.0],
    "Close":[103.0,102.0,102.0], "Volume":[1e6,1e6,1e6],
}, index=idx)
spring = detect_box_setup(spring_df, box, cfg)
assert spring["family"] == "SPRING"
assert spring["state"] == "SPRING_RECLAIM_PENDING"


# 3) Confirmed spring requires the next close to preserve the reclaim.
spring_confirm_df = pd.DataFrame({
    "Open":[103.0,101.0,102.0], "High":[105.0,104.0,106.0], "Low":[100.5,95.0,101.0],
    "Close":[102.0,102.0,105.0], "Volume":[1e6,1e6,1.2e6],
}, index=idx)
spring2 = detect_box_setup(spring_confirm_df, box, cfg)
assert spring2["state"] == "SPRING_CONFIRMED"


# 4) Trend bridge requires impulse -> pause -> same-direction resume.
bidx = pd.bdate_range("2025-01-01", periods=80)
close = np.full(80, 100.0)
close[:40] = np.linspace(80,100,40)
close[40:46] = np.linspace(100,116,6)  # impulse
close[46:50] = [115,114,115,115]      # pause
close[50:60] = np.linspace(116,130,10) # resume
close[60:] = np.linspace(128,122,20)
bridge_raw = pd.DataFrame({
    "Open":close*0.995, "High":close*1.015, "Low":close*0.985, "Close":close,
    "Volume":np.full(80,1_000_000),
}, index=bidx)
bridge_df = add_indicators(bridge_raw, cfg)
bridge = discover_trend_bridge(bridge_df, cfg)
assert bridge is not None
assert bridge["impulsePct"] >= cfg["bridgeMinImpulsePct"]
assert bridge["direction"] == "UP"

# Falling impulse -> pause -> falling resume is retained as resistance evidence,
# but it must not manufacture a bullish trend-bridge setup.
dclose = np.full(80, 120.0)
dclose[:40] = np.linspace(140,120,40)
dclose[40:46] = np.linspace(120,102,6)
dclose[46:50] = [103,104,103,103]
dclose[50:60] = np.linspace(102,88,10)
dclose[60:] = np.linspace(90,95,20)
down_raw = pd.DataFrame({
    "Open":dclose*1.005, "High":dclose*1.015, "Low":dclose*0.985, "Close":dclose,
    "Volume":np.full(80,1_000_000),
}, index=bidx)
down_df = add_indicators(down_raw, cfg)
down_bridge = discover_trend_bridge(down_df, cfg)
assert down_bridge is not None
assert down_bridge["direction"] == "DOWN"
assert detect_bridge_setup(down_df, down_bridge, [], cfg) is None


# 5) High-trend continuation is state-based, not merely high-distance.
hidx = pd.bdate_range("2024-01-01", periods=180)
hclose = np.linspace(60,100,180)
hclose[-20:] = np.linspace(98,103,20)
high_raw = pd.DataFrame({
    "Open":hclose*0.997, "High":hclose*1.01, "Low":hclose*0.99, "Close":hclose,
    "Volume":np.full(180,2_000_000),
}, index=hidx)
high_df = add_indicators(high_raw, cfg)
high_setup = detect_high_trend(high_df, cfg)
assert high_setup is not None
assert high_setup["family"] == "HIGH_TREND_CONTINUATION"
assert high_setup["state"] in ("BREAKOUT_PRESSURE","HIGH_BREAKOUT","HIGH_RETEST","HIGH_BASE")

# High-level retest must be reachable: reference high is fixed before the recent base.
rt_close = np.concatenate([
    np.linspace(60.0, 100.0, 160),
    np.array([98.0,99.0,99.5,100.0,100.2,99.8,100.5,101.0,102.0,103.0,
              103.0,102.5,103.5,104.0,103.5,103.0,102.5,102.0,102.5,102.5])
])
rt_raw = pd.DataFrame({
    "Open":rt_close*0.997, "High":rt_close*1.01, "Low":rt_close*0.99, "Close":rt_close,
    "Volume":np.full(180,2_000_000),
}, index=hidx)
rt_df = add_indicators(rt_raw, cfg)
rt_setup = detect_high_trend(rt_df, cfg)
assert rt_setup is not None
assert rt_setup["state"] == "HIGH_RETEST"


# 6) RSI 70/30 never creates an automatic trigger.
r = rsi_context(high_df, cfg)
assert r["priceFirst"] is True
assert r["auto7030Trigger"] is False


# 7) Unaccepted levels cannot become execution support/invalidation.
roles = attach_roles(decision_df, [level])
setup_bundle = {
    "primary":{
        "family":"BOX","state":"BOX_BUILDING","evidence":["SYNTH"],
        "triggerLevel":110.0,"invalidationLevel":None,"maturity":45,
    },
    "all":[],
}
confirmation = {"warnings":[]}
money = {"avg20TradingValueEstimated":20_000_000_000}
plan = build_execution_plan(decision_df, roles, setup_bundle, confirmation, money, cfg)
assert plan["nearestAcceptedSupport"] is None
assert plan["invalidation"] is None
assert plan["readiness"] == "RADAR"

# Generic role-reversal execution requires a CORE level with ACCEPTED_SUPPORT.
supporting_accepted = dict(level)
supporting_accepted["importance"] = "SUPPORTING"
supporting_accepted["role"] = {"state":"ACCEPTED_SUPPORT","warnings":[]}
assert detect_level_retest(accepted_df, [supporting_accepted], cfg) is None

core_accepted = dict(level)
core_accepted["importance"] = "CORE"
core_accepted["role"] = {"state":"ACCEPTED_SUPPORT","warnings":[]}
level_retest = detect_level_retest(accepted_df, [core_accepted], cfg)
assert level_retest is not None
assert level_retest["state"] == "LEVEL_RETEST"

# A spring reclaim and an accepted breakout are information states, not chase entries.
pending_money = {"avg20TradingValueEstimated":20_000_000_000}
spring_bundle = {"primary":{
    "family":"SPRING","state":"SPRING_CONFIRMED","evidence":["SYNTH"],
    "triggerLevel":100.0,"invalidationLevel":95.0,
},"all":[]}
spring_plan = build_execution_plan(spring_confirm_df, [], spring_bundle, {"warnings":[]}, pending_money, cfg)
assert spring_plan["readiness"] == "WATCH_TRIGGER"

box_accept_bundle = {"primary":{
    "family":"BOX_BREAKOUT","state":"BOX_BREAKOUT_ACCEPTED","evidence":["SYNTH"],
    "triggerLevel":100.0,"invalidationLevel":95.0,
},"all":[]}
box_accept_plan = build_execution_plan(accepted_df, [], box_accept_bundle, {"warnings":[]}, pending_money, cfg)
assert box_accept_plan["readiness"] == "WATCH_TRIGGER"


# 8) End-to-end schema contains no aggregate score field.
eidx = pd.bdate_range("2023-01-02", periods=700)
ec = np.linspace(50,120,700)
eraw = pd.DataFrame({
    "Open":ec*0.995, "High":ec*1.015, "Low":ec*0.985, "Close":ec,
    "Volume":np.full(700,1_500_000),
}, index=eidx)
out = analyze_frame(
    {"code":"000000","name":"SYNTH_CASE","market":"KOSPI","amount":50_000_000_000,"marcap":1_000_000_000_000},
    eraw,
    cfg,
)
assert out["status"] == "OK"
assert out["schemaVersion"] == "MARKET_STRUCTURE_V3"
assert "score" not in out
assert "actionScore" not in out
assert out["confirmation"]["rsi"]["auto7030Trigger"] is False
assert out["review"]["assistantReviewRequired"] is True
assert out["review"]["machineScope"] == "PREFILTER_AND_EVIDENCE_ONLY"
assert len(out["review"]["chartTrace"]) <= cfg["reviewTraceSessions"]
assert out["review"]["traceSchema"] == ["date","open","high","low","close","volumeRatio20","tradingValueRatio20","rsi"]

# Machine output may propose structure, but every surfaced candidate still requires
# assistant deep review; the scanner is not the final chart-judgement authority.
review_rows = []
for i, family in enumerate(("BOX_BREAKOUT","HIGH_TREND_CONTINUATION","ROLE_REVERSAL","SPRING")):
    row = {
        "code": f"SYNTH_{i}",
        "money": {"avg20TradingValueEstimated": 20_000_000_000 + i},
        "execution": {"readiness": "WATCH_TRIGGER", "structuralRR": 2.0},
        "setups": {"primary": {"family": family, "state": "BOX_BREAKOUT_PENDING"}, "all": []},
        "review": {"assistantReviewRequired": True},
    }
    review_rows.append(row)
queue = select_deep_review_queue(review_rows, {**cfg, "maxDeepReviewCandidates": 3, "maxDeepReviewPerFamily": 1})
assert len(queue) == 3
assert all((x.get("review") or {}).get("assistantReviewRequired") is True for x in queue)

# Shorter-history listings are analyzable without a separate legacy/new-listing doctrine.
short_cfg = dict(cfg)
short_cfg["minHistoryRows"] = 60
sidx = pd.bdate_range("2026-01-02", periods=80)
sc = np.linspace(80.0,100.0,80)
sraw = pd.DataFrame({
    "Open":sc*0.997, "High":sc*1.01, "Low":sc*0.99, "Close":sc,
    "Volume":np.full(80,1_000_000),
}, index=sidx)
short_out = analyze_frame(
    {"code":"000000","name":"SYNTH_SHORT_HISTORY","market":"KOSDAQ","amount":20_000_000_000,"marcap":500_000_000_000},
    sraw,
    short_cfg,
)
assert short_out["status"] == "OK"

print("Market Structure V3 self-tests: PASS")
