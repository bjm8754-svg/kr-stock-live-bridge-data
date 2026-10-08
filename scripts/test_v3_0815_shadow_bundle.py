#!/usr/bin/env python3
import json
import pathlib
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent
VALIDATOR = ROOT / "validate_v3_0815_shadow_bundle.py"

base = {
    "schemaVersion": "V3_0815_SHADOW_BUNDLE_V1",
    "mode": "SHADOW_ONLY",
    "productionWriteAllowed": False,
    "tradeDate": "20261007",
    "sourceTradeDate": "20261006",
    "status": "READY",
    "generatedAtKst": "2026-10-07T07:55:00+09:00",
    "planOrigin": "MACHINE_CONTINUITY_FALLBACK",
    "degradedMode": True,
    "assistantDeepReviewCompleted": False,
    "watchlist": {"status": "READY", "codes": ["000001"]},
    "livePlans": [{
        "code": "000001",
        "planState": "PROBE_PLAN",
        "actionableZone": "100 KRW observed structural trigger",
        "trigger": "hold 100",
        "invalidation": 90,
        "noChase": "no chase without retest",
        "counterargument": "fallback",
    }],
}

def run(obj, ok):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)
        p = f.name
    r = subprocess.run(["python", str(VALIDATOR), p, "--trade-date", "20261007"], capture_output=True, text=True)
    assert (r.returncode == 0) == ok, (r.returncode, r.stdout, r.stderr)

run(base, True)

bad = json.loads(json.dumps(base))
bad["degradedMode"] = False
run(bad, False)

bad = json.loads(json.dumps(base))
bad["watchlist"]["codes"] = ["000002"]
run(bad, False)

closed = {
    "schemaVersion": "V3_0815_SHADOW_BUNDLE_V1",
    "mode": "SHADOW_ONLY",
    "productionWriteAllowed": False,
    "tradeDate": "20261007",
    "sourceTradeDate": None,
    "status": "MARKET_CLOSED",
    "generatedAtKst": "2026-10-07T07:55:00+09:00",
    "planOrigin": "MACHINE_CONTINUITY_FALLBACK",
    "degradedMode": True,
    "assistantDeepReviewCompleted": False,
    "watchlist": {"status": "MARKET_CLOSED", "codes": []},
    "livePlans": [],
}
run(closed, True)
# Assistant deep-review quality gate: evidence-less READY bundles must fail closed.
assistant = json.loads(json.dumps(base))
assistant["planOrigin"] = "ASSISTANT_DEEP_REVIEW"
assistant["degradedMode"] = False
assistant["assistantDeepReviewCompleted"] = True
assistant["livePlans"][0]["externalEvidence"] = {
    "companyQuality": {"state": "MIXED"},
    "earningsRevision": {"state": "UNKNOWN", "reason": "No reliable revision observation"},
    "catalyst": {"state": "NONE_IDENTIFIED"},
    "industryMacro": {"state": "NEUTRAL"},
    "globalUsLead": {"state": "NOT_MATERIAL"},
    "eventRisk": {"state": "MODERATE"},
}
assistant["overnightDelta"] = {
    "verifiedEvidenceCount": 1,
    "evidence": [{
        "sourceType": "COMPANY_IR",
        "sourceDate": "2026-10-06",
        "observationDate": "2026-10-07",
        "sourceUrl": "https://example.com/ir/sample",
        "summary": "Verification fixture for external evidence schema",
    }],
}
run(assistant, True)

missing_evidence = json.loads(json.dumps(assistant))
missing_evidence["overnightDelta"]["evidence"] = []
missing_evidence["overnightDelta"]["verifiedEvidenceCount"] = 0
run(missing_evidence, False)

all_unknown = json.loads(json.dumps(assistant))
all_unknown["livePlans"][0]["externalEvidence"] = {
    key: {"state": "UNKNOWN", "reason": "Source unavailable"}
    for key in assistant["livePlans"][0]["externalEvidence"]
}
run(all_unknown, False)

unknown_without_reason = json.loads(json.dumps(assistant))
unknown_without_reason["livePlans"][0]["externalEvidence"]["earningsRevision"] = {"state": "UNKNOWN"}
run(unknown_without_reason, False)

bad_count = json.loads(json.dumps(assistant))
bad_count["overnightDelta"]["verifiedEvidenceCount"] = 2
run(bad_count, False)

print("V3 08:15 shadow bundle validator tests: PASS")
