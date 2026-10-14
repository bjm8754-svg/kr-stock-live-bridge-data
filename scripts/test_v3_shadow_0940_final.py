#!/usr/bin/env python3
"""Deterministic SHADOW final evaluator regression tests (no network/writes)."""
import copy
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from v3_shadow_0940_final import calculate

DAY = "20261013"
SHA = "frozen-sha"
CODE = "005930"
LANES = ("companyQuality", "earningsRevision", "catalyst",
         "industryMacro", "globalUsLead", "eventRisk")
RULES = {
    "confirmationMode": "CLOSE_ABOVE_N_CONSECUTIVE_SNAPSHOTS",
    "triggerPrice": 100,
    "holdMinutes": 3,
    "maxChasePct": 10,
}
PLAN = {
    "code": CODE, "name": "Synthetic", "planState": "PROBE_PLAN",
    "invalidation": 90, "executionRules": RULES,
    "externalEvidence": {lane: {"state": "NEUTRAL"} for lane in LANES},
}
SOURCE = {
    "bundleSha": SHA,
    "planOrigin": "ASSISTANT_DEEP_REVIEW",
    "degradedMode": False,
    "sourcePlanGeneratedAt": "2026-10-13T08:20:00+09:00",
    "assistantDeepReviewCompleted": True,
    "sourceTradeDate": "20261012",
    "watchlist": {"status": "READY", "codes": [CODE]},
    "livePlans": [PLAN],
}


def fixture(prices=None):
    prices = prices if prices is not None else [101.0] * 41
    assert len(prices) == 41
    scans = {"0935": {"status": "PASS"}}
    def one(end):
        rows = [{
            "atKst": f"{DAY} 09{i:02d}",
            "stocks": {CODE: {"currentPrice": prices[i], "marketStatus": "OPEN"}},
        } for i in range(end + 1)]
        return {
            "schemaVersion": "V3_SHADOW_LIVE_CAPTURE_V1",
            "mode": "SHADOW_ONLY", "productionWriteAllowed": False,
            "tradeDate": DAY, "status": "PASS", "codes": [CODE],
            "history": {"count": len(rows), "from": rows[0]["atKst"],
                        "to": rows[-1]["atKst"], "rows": rows},
            "scanDiagnostics": {"0935": {"status": "PASS"}},
            "marketScans": scans,
            "sourcePlan": copy.deepcopy(SOURCE),
        }
    return one(35), one(40)


def run(pair):
    return calculate(*pair, DAY, 123456, SHA)


good = run(fixture())
assert good["cycleStatus"] == "PASS"
assert good["evaluationAt0935"][0]["evaluation"] == "CONFIRMED"
assert good["perCandidateEvaluation"][0]["finalEvaluation"] == "CONFIRMED"
assert good["productionWriteAllowed"] is False

fb = fixture()
for c in fb:
    c["sourcePlan"]["planOrigin"] = "MACHINE_CONTINUITY_FALLBACK"
    c["sourcePlan"]["degradedMode"] = True
    c["sourcePlan"]["assistantDeepReviewCompleted"] = False
    c["sourcePlan"]["livePlans"][0]["externalEvidence"] = {
        lane: {"state": "UNKNOWN"} for lane in LANES
    }
assert run(fb)["cycleStatus"] == "PARTIAL"

prose = fixture()
for c in prose:
    c["sourcePlan"]["livePlans"][0].pop("executionRules")
out = run(prose)
assert out["cycleStatus"] == "PARTIAL"
assert out["perCandidateEvaluation"][0]["finalEvaluation"] == "DATA_FAIL"

invalid = [101.0] * 41
invalid[4] = 89.0
out = run(fixture(invalid))
assert out["evaluationAt0935"][0]["evaluation"] == "INVALIDATED"
assert out["perCandidateEvaluation"][0]["finalEvaluation"] == "INVALIDATED"

chase = [112.0] * 41
out = run(fixture(chase))
assert out["perCandidateEvaluation"][0]["finalEvaluation"] == "NO_CHASE"

not_confirmed = [97.0] * 41
out = run(fixture(not_confirmed))
assert out["perCandidateEvaluation"][0]["finalEvaluation"] == "NOT_CONFIRMED"

missing = fixture()
for capture in missing:
    capture["history"]["rows"][5]["stocks"][CODE]["currentPrice"] = None
out = run(missing)
assert out["perCandidateEvaluation"][0]["finalEvaluation"] == "DATA_FAIL"
assert out["cycleStatus"] == "PARTIAL"

drift = fixture()
drift[1]["sourcePlan"]["livePlans"][0]["trigger"] = "changed after freeze"
try:
    run(drift)
    raise AssertionError("sourcePlan drift undetected")
except ValueError as exc:
    assert "sourcePlanMismatch" in str(exc)

stale = fixture()
stale[1]["tradeDate"] = "20261012"
try:
    run(stale)
    raise AssertionError("stale artifact undetected")
except ValueError as exc:
    assert "tradeDate" in str(exc)

bad_prefix = fixture()
bad_prefix[1]["history"]["rows"][1]["stocks"][CODE]["currentPrice"] = 111
try:
    run(bad_prefix)
    raise AssertionError("09:35/09:40 inconsistent frozen history")
except ValueError as exc:
    assert "historyPrefixMismatch" in str(exc)

empty = fixture()
for x in empty:
    x["status"] = "MARKET_CLOSED"
    x["codes"] = []
    x["history"] = {"count": 0, "rows": [], "from": None, "to": None}
    x["marketScans"] = {}
    x["scanDiagnostics"] = {}
    x["sourcePlan"]["watchlist"] = {"status": "MARKET_CLOSED", "codes": []}
    x["sourcePlan"]["livePlans"] = []
assert run(empty)["cycleStatus"] == "MARKET_CLOSED"

print("V3 SHADOW 09:40 final evaluator tests: PASS")
