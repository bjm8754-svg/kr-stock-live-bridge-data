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

print("V2 self-tests: PASS")
