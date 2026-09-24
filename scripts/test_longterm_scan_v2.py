#!/usr/bin/env python3
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("scan", ROOT / "scripts" / "longterm_scan.py")
scan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scan)
cfg = json.loads((ROOT / "longterm-scan-config.json").read_text(encoding="utf-8"))

# numpy scalar JSON regression: previous V1 full scan failed here.
assert scan.json_default(np.bool_(True)) is True
assert scan.json_default(np.int64(7)) == 7

# Core-line clustering should merge nearby round/reference levels.
clusters = scan.cluster_levels(
    [(9960, 4.0, "DEOYANGBONG_CLOSE"), (10000, 1.0, "ROUND_FIGURE"), (10020, 2.0, "SWING_HIGH")],
    1.5,
)
assert len(clusters) == 1
assert 9950 <= clusters[0]["line"] <= 10020
assert clusters[0]["sourceCount"] == 3

# Jindol requires absolute money + relative money + volume + close acceptance.
j = scan.classify_breakout(True, 150_000_000_000, 2.0, 2.2, 0.8, 0.9, cfg)
g = scan.classify_breakout(True, 80_000_000_000, 2.0, 2.2, 0.8, 0.9, cfg)
g2 = scan.classify_breakout(True, 150_000_000_000, 2.0, 2.2, 0.8, 0.4, cfg)
assert j == "JINDOL_CONFIRMED"
assert g == "GADOL_RISK"
assert g2 == "GADOL_RISK"

# New-listing track must be analyzable without MA600.
idx = pd.bdate_range("2026-01-02", periods=120)
base = np.linspace(10000, 11800, 120)
df = pd.DataFrame({
    "Open": base * 0.995,
    "High": base * 1.02,
    "Low": base * 0.98,
    "Close": base,
    "Volume": np.full(120, 500_000),
}, index=idx)
# Add an observable strong reference candle late in the series.
df.iloc[95, df.columns.get_loc("Open")] = 10000
df.iloc[95, df.columns.get_loc("Close")] = 11600
df.iloc[95, df.columns.get_loc("High")] = 11800
df.iloc[95, df.columns.get_loc("Low")] = 9900
df.iloc[95, df.columns.get_loc("Volume")] = 12_000_000
meta = {"code":"999999","name":"SYNTH","market":"KOSDAQ","amount":120_000_000_000,"marcap":1_000_000_000_000}
out = scan.analyze_frame(meta, df, cfg)
assert out["status"] == "OK"
assert out["track"] == "NEW_LISTING"
assert out["abc"]["state"] == "NOT_APPLICABLE_LONG_MA"

# Agreed V2 feature contract: analyzer must emit all structural/timing fields.
required_v2_fields = (
    "abc", "deoyangbong", "coreResistance", "cloud", "money",
    "breakoutClass", "preJindol", "retestOk", "retestSupply",
    "reacceleration", "yangEumYang", "newListingSetup", "entryPlan", "ma",
)
for field in required_v2_fields:
    assert field in out, field
for ma_key in ("20", "60", "120", "240", "480", "600", "1000"):
    assert ma_key in out["ma"], ma_key

# Final output must be serializable with numpy/pandas values.
json.dumps(out, ensure_ascii=False, default=scan.json_default)
# Operational briefing layer must not promote a plain weak breakout warning.
weak = {
    "signal":"GADOL_RISK",
    "money":{"avg20TradingValueEstimated":20_000_000_000,"tradingValue":50_000_000_000,
             "tradingValueRatio20Estimated":2.0,"volumeRatio20":2.0},
    "abc":{"score":90,"bPlus":True},
    "deoyangbong":{"latestPrior":{"tradingValueEstimated":150_000_000_000}},
    "coreResistance":{"score":12},
    "distanceToCorePct":1.0,
    "retestSupply":{"supplyDry":True},
}
assert not scan.is_qualified_candidate(weak, cfg)

# Selection-memory invariant: action score depends only on current observable fields.
sample = {
    "signal":"PRE_JINDOL",
    "abc":{"score":90,"bPlus":True},
    "money":{"tradingValue":120_000_000_000,"tradingValueRatio20Estimated":1.6,
             "volumeRatio20":1.7,"relativeToPriorReferenceMoney":0.9},
    "coreResistance":{"score":12,"sourceCount":3},
    "cloud":{"state":"ABOVE"},
    "entryPlan":{"structuralRR":2.1,"distanceToSupportPct":5.0},
    "retestSupply":{"supplyDry":False},
    "closeLocation":0.72,
    "distanceToCorePct":1.0,
    "breakCoreResistance":False,
    "reacceleration":False,
    "yangEumYang":False,
}
s1 = scan.compute_action_score(sample, cfg)
sample["yesterdayRejected"] = True
sample["previousRank"] = 999
sample["wasBriefed"] = False
s2 = scan.compute_action_score(sample, cfg)
assert s1 == s2
assert s1["selectionMemoryUsed"] is False
assert s1["briefingTier"] in ("ACTION_NOW", "WATCH_TRIGGER", "RADAR")


# Chart-grade invariant: completed-daily chart quality must be independent of timing/action fields.
chart_sample = {
    "signal":"PRE_JINDOL",
    "track":"LONG_HISTORY",
    "abc":{"state":"C_ACTIVE","score":100,"bPlus":True},
    "cloud":{"state":"ABOVE"},
    "coreResistance":{"score":14,"sourceCount":4},
    "deoyangbong":{"today":False,"latestPrior":{
        "open":10000,"close":12000,"high":12200,"low":9800,
        "tradingValueEstimated":350_000_000_000}},
    "money":{"tradingValue":50_000_000_000},
    "close":11800,
    "low":11600,
    "newListingSetup":False,
    "dataWarnings":[],
    "entryPlan":{"structuralRR":0.2,"distanceToSupportPct":20.0},
    "distanceToCorePct":25.0,
}
cg1 = scan.compute_chart_grade(chart_sample, cfg)
chart_sample["entryPlan"] = {"structuralRR":9.0,"distanceToSupportPct":0.5}
chart_sample["distanceToCorePct"] = 0.1
chart_sample["previousRank"] = 1
chart_sample["wasBriefed"] = True
cg2 = scan.compute_chart_grade(chart_sample, cfg)
assert cg1 == cg2
assert cg1["grade"] == "S"
assert cg1["timingInputsUsed"] is False
assert cg1["selectionMemoryUsed"] is False



# Chart-grade must accept a completed current reference candle even when there is no prior one.
current_ref_sample = {
    "signal":"DEOYANGBONG_C_TRIGGER",
    "track":"LONG_HISTORY",
    "abc":{"state":"C_ACTIVE","score":100,"bPlus":True},
    "cloud":{"state":"ABOVE"},
    "coreResistance":{"score":14,"sourceCount":4},
    "deoyangbong":{"today":True,"latestPrior":None},
    "money":{"tradingValue":350_000_000_000},
    "newListingSetup":False,
    "dataWarnings":[],
}
cg3 = scan.compute_chart_grade(current_ref_sample, cfg)
assert cg3["grade"] == "S"
assert cg3["referenceMoneySource"] == "CURRENT_COMPLETED_REFERENCE"

# Old audit warnings must not permanently veto a chart; only current DATA_WARNING is a hard block.
old_warning_sample = dict(current_ref_sample)
old_warning_sample["dataWarnings"] = ["HIST_PRICE_JUMP>35:20230102"]
cg4 = scan.compute_chart_grade(old_warning_sample, cfg)
assert cg4["grade"] == "S"

current_warning_sample = dict(current_ref_sample)
current_warning_sample["signal"] = "DATA_WARNING"
cg5 = scan.compute_chart_grade(current_warning_sample, cfg)
assert cg5["grade"] == "BELOW_B_PLUS"
assert cg5["eligible"] is False



# Reference-candle integrity: a deeply failed old anchor cannot preserve S/A indefinitely.
failed_ref_sample = {
    "signal":"PRE_JINDOL",
    "track":"LONG_HISTORY",
    "abc":{"state":"C_ACTIVE","score":100,"bPlus":True},
    "cloud":{"state":"ABOVE"},
    "coreResistance":{"score":14,"sourceCount":4},
    "deoyangbong":{"today":False,"latestPrior":{
        "open":10000,"close":12000,"high":12200,"low":9800,
        "tradingValueEstimated":350_000_000_000}},
    "money":{"tradingValue":50_000_000_000},
    "close":9000,"low":8900,
    "newListingSetup":False,
    "dataWarnings":[],
}
cg_failed = scan.compute_chart_grade(failed_ref_sample, cfg)
assert cg_failed["referenceState"] == "FAILED"
assert cg_failed["grade"] == "BELOW_B_PLUS"

damaged_ref_sample = dict(failed_ref_sample)
damaged_ref_sample["close"] = 10000
cg_damaged = scan.compute_chart_grade(damaged_ref_sample, cfg)
assert cg_damaged["referenceState"] == "DAMAGED"
assert cg_damaged["grade"] == "B_PLUS"



# A fresh current reference must replace an older larger-money anchor for structural grading.
fresh_over_old = {
    "signal":"DEOYANGBONG_C_TRIGGER",
    "track":"LONG_HISTORY",
    "abc":{"state":"C_ACTIVE","score":100,"bPlus":True},
    "cloud":{"state":"ABOVE"},
    "coreResistance":{"score":14,"sourceCount":4},
    "deoyangbong":{"today":True,"latestPrior":{
        "open":20000,"close":23000,"high":23500,"low":19500,
        "tradingValueEstimated":600_000_000_000}},
    "money":{"tradingValue":150_000_000_000},
    "close":12000,"low":10500,
    "newListingSetup":False,
    "dataWarnings":[],
}
cg_fresh = scan.compute_chart_grade(fresh_over_old, cfg)
assert cg_fresh["referenceMoneySource"] == "CURRENT_COMPLETED_REFERENCE"
assert cg_fresh["referenceMoneyKrw"] == 150_000_000_000
assert cg_fresh["referenceState"] == "CURRENT"
assert cg_fresh["grade"] == "S"




# Fresh structural discovery must not be permanently vetoed by a stale/failed old reference.
# This path is capped at B+: S/A still require a usable strong reference.
fresh_discovery = {
    "signal":"GADOL_RISK",
    "track":"LONG_HISTORY",
    "abc":{"state":"C_RECOVERY_NONCLASSIC_BASE","score":60,"bPlus":False},
    "cloud":{"state":"INSIDE"},
    "coreResistance":{"score":8,"sourceCount":2},
    "deoyangbong":{"today":False,"latestPrior":{
        "open":10000,"close":11000,"high":11200,"low":9000,
        "tradingValueEstimated":350_000_000_000}},
    "money":{"tradingValue":45_000_000_000,
             "tradingValueRatio20Estimated":3.0,"volumeRatio20":3.0},
    "close":7000,"low":6800,"newListingSetup":False,"dataWarnings":[],
}
cg_fresh_discovery = scan.compute_chart_grade(fresh_discovery, cfg)
assert cg_fresh_discovery["referenceState"] == "FAILED"
assert cg_fresh_discovery["grade"] == "B_PLUS"

weak_fresh_discovery = dict(fresh_discovery)
weak_fresh_discovery["money"] = {
    "tradingValue":20_000_000_000,
    "tradingValueRatio20Estimated":1.0,
    "volumeRatio20":1.0,
}
assert scan.compute_chart_grade(weak_fresh_discovery, cfg)["grade"] == "BELOW_B_PLUS"

# Entry plan must preserve support roles instead of collapsing every structural level.
entry_cur = {"Close": 10000}
entry_core = {
    "zoneLow": 9600, "line": 9700,
    "alternatives": [{"zoneLow": 10500, "line": 10600, "sources": ["SWING_HIGH"]}],
}
entry_ma = {"240": 9300, "480": 9000, "600": 8800, "1000": 8200}
entry_prior = {"open": 9000, "close": 9400, "low": 8600}
entry_recent = {"open": 9700, "close": 9800, "low": 9500}
ep = scan.build_structural_entry_plan(entry_cur, entry_core, entry_ma, entry_prior, entry_recent, cfg)
assert ep["nearestSupport"] == 9800
assert ep["supportSource"] == "RECENT_REFERENCE_CLOSE"
assert ep["supportHierarchy"]["primaryReferenceSupport"] == 9800
assert ep["supportHierarchy"]["primaryReferenceSource"] == "RECENT_REFERENCE_CLOSE"
assert ep["supportHierarchy"]["referenceLowInvalidationCandidate"] == 9500
assert ep["supportHierarchy"]["coreSupport"] == 9700
assert ep["supportHierarchy"]["longMaSupport"] == 9300
assert ep["nextResistance"] == 10500

# Compact canonical must stay chart-first and exclude bulky resistance alternatives.
compact_sample = dict(current_ref_sample)
compact_sample.update({
    "market":"KOSDAQ","tradeDate":"20260923","close":12000,"open":10500,"high":12200,"low":10400,
    "dayChangePct":12.0,"closeLocation":0.9,
    "chartGrade":scan.compute_chart_grade(current_ref_sample, cfg),
    "abc":{"state":"C_ACTIVE","score":100,"bPlus":True},
    "ma":{"20":11000,"60":10000,"120":9500,"240":9000,"480":8500,"600":8000,"1000":7000},
    "coreResistance":{"line":11500,"zoneLow":11400,"zoneHigh":11600,"score":14,"touches":3,
                      "sourceCount":4,"sources":["SWING_HIGH"],"distanceFromReferencePct":2.0,
                      "alternatives":[{"line":13000}]},
    "distanceToCorePct":-4.0,"breakCoreResistance":True,"breakoutClass":"JINDOL_CONFIRMED",
    "preJindol":False,"retestOk":False,"retestSupply":{"supplyDry":False},
    "reacceleration":False,"yangEumYang":False,"recentReferenceCandle":None,
    "entryPlan":{"nearestSupport":11500,"nextResistance":13000,"structuralRR":2.0},
    "actionScore":{"total":70},"dataWarnings":[],
})
cc = scan.compact_chart_candidate(compact_sample)
assert "setupCoreResistance" in cc and "referenceCandleAnchor" in cc and "retestAnchor" in cc
assert "alternatives" not in (cc["setupCoreResistance"] or {})
bo = scan.build_brief_output({
    "status":"PASS","generatedAtKst":"x","tradeDate":"20260923","methodologyVersion":"x",
    "primaryLogic":"x","coverage":{},"counts":{},"notes":[],
    "chartCandidates":[compact_sample],"briefingCandidates":[],"qualifiedPool":[],"riskWarnings":[]
})
assert bo["schemaVersion"] == "YBM_BRIEF_V2"
assert bo["role"]["primary"].startswith("completed-daily CHART")

print("V2 self-tests: PASS")
