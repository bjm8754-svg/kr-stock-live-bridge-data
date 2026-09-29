#!/usr/bin/env python3
import json
from pathlib import Path

import numpy as np
import pandas as pd

from msv3.engine import analyze_frame
from msv3.execution import build_execution_plan
from msv3.features import add_indicators, rsi_context
from msv3.levels import attach_roles, classify_role, discover_trend_bridge, merge_levels
from msv3.setups import detect_box_setup, detect_high_trend

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

print("Market Structure V3 self-tests: PASS")
