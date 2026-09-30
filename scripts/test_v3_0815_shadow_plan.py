#!/usr/bin/env python3
import json
import pathlib
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent
VALIDATOR = ROOT / "validate_v3_0815_shadow_plan.py"

base = {
    "schemaVersion": "V3_0815_SHADOW_PLAN_V1",
    "mode": "SHADOW_ONLY",
    "productionWriteAllowed": False,
    "source": {
        "freshnessStatus": "PASS",
        "methodologyVersion": "MARKET_STRUCTURE_V3_2026-09-29",
        "tradeDate": "20260929",
        "reviewPacketValidated": True,
        "canonicalValidated": True,
    },
    "chartReview": [{
        "code": "000001",
        "name": "SYNTH",
        "chartState": "ATTACK_CANDIDATE",
        "thesis": "accepted support retest",
        "importantZone": "100-102",
        "confirmation": "close holds 102",
        "invalidation": 99.0,
        "nextResistance": 112.0,
        "chaseJudgement": "NO_CHASE",
        "counterargument": "overhead supply",
    }],
    "plans": [{
        "code": "000001",
        "name": "SYNTH",
        "planState": "PROBE_PLAN",
        "actionableZone": "100-102",
        "trigger": "hold 102",
        "invalidation": 99.0,
        "noChase": "above 106 no new entry",
        "nextResistance": 112.0,
        "structuralRR": 2.0,
        "counterargument": "overhead supply",
        "externalEvidence": {
            "companyQuality": {"state": "UNKNOWN"},
            "earningsRevision": {"state": "UNKNOWN"},
            "catalyst": {"state": "UNKNOWN"},
            "industryMacro": {"state": "NEUTRAL"},
            "globalUsLead": {"state": "NOT_MATERIAL"},
            "eventRisk": {"state": "UNKNOWN"},
        },
    }],
}


def run(d, ok):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False)
        p = f.name
    r = subprocess.run(["python", str(VALIDATOR), p], capture_output=True, text=True)
    assert (r.returncode == 0) == ok, (r.returncode, r.stdout, r.stderr)


run(base, True)

bad = json.loads(json.dumps(base))
bad["plans"][0]["actionScore"] = 88
run(bad, False)

bad = json.loads(json.dumps(base))
bad["productionWriteAllowed"] = True
run(bad, False)

bad = json.loads(json.dumps(base))
bad["chartReview"][0]["chartState"] = "REJECT"
run(bad, False)

print("V3 08:15 shadow plan validator tests: PASS")
