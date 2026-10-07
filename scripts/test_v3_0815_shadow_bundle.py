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
print("V3 08:15 shadow bundle validator tests: PASS")
