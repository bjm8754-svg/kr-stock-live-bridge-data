#!/usr/bin/env python3
import json
import pathlib
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent
ASSEMBLER = ROOT / "assemble_v3_eod_deep_review.py"
VALIDATOR = ROOT / "validate_v3_eod_deep_review.py"

with tempfile.TemporaryDirectory() as td:
    p = pathlib.Path(td)
    codes = [f"{i:06d}" for i in range(1, 25)]
    handoff = {
        "schemaVersion": "MARKET_STRUCTURE_V3_HANDOFF_V1",
        "mode": "SHADOW_ONLY",
        "productionWriteAllowed": False,
        "status": "PASS",
        "tradeDate": "20261007",
        "generatedAtKst": "2026-10-07T17:00:00+09:00",
        "methodologyVersion": "MARKET_STRUCTURE_V3_2026-09-29",
        "source": {"workflowRunId": 123},
    }
    index = {
        "schemaVersion": "MARKET_STRUCTURE_V3_REVIEW_INDEX_V1",
        "mode": "SHADOW_ONLY",
        "productionWriteAllowed": False,
        "status": "PASS",
        "tradeDate": "20261007",
        "generatedAtKst": "2026-10-07T17:00:00+09:00",
        "methodologyVersion": "MARKET_STRUCTURE_V3_2026-09-29",
        "totalCount": len(codes),
        "codes": codes,
    }
    (p/"market-structure-v3-handoff.json").write_text(json.dumps(handoff), encoding="utf-8")
    (p/"market-structure-v3-review-index.json").write_text(json.dumps(index), encoding="utf-8")

    for bi in range(1,4):
        expected = codes[(bi-1)*12:bi*12]
        reviews = []
        for code in expected:
            reviews.append({
                "code": code,
                "chartState": "WATCH",
                "thesis": "synthetic independent review",
                "importantZone": "100-102",
                "confirmation": "hold 102",
                "invalidation": 99,
                "nextResistance": 110,
                "chaseJudgement": "NO_CHASE",
                "counterargument": "synthetic",
            })
        batch = {
            "schemaVersion": "V3_EOD_DEEP_REVIEW_BATCH_V1",
            "mode": "SHADOW_ONLY",
            "productionWriteAllowed": False,
            "status": "PASS",
            "sourceTradeDate": "20261007",
            "sourceWorkflowRunId": 123,
            "sourceIndexGeneratedAtKst": "2026-10-07T17:00:00+09:00",
            "methodologyVersion": "MARKET_STRUCTURE_V3_2026-09-29",
            "reviewedAtKst": "2026-10-07T18:00:00+09:00",
            "batchIndex": bi,
            "batchCount": 3,
            "candidateCodes": expected,
            "reviews": reviews,
        }
        (p/f"v3-eod-deep-review-batch-{bi}.json").write_text(json.dumps(batch), encoding="utf-8")

    r = subprocess.run(["python", str(ASSEMBLER), "--root", str(p)], capture_output=True, text=True)
    assert r.returncode == 0, (r.stdout, r.stderr)
    r = subprocess.run(["python", str(VALIDATOR), str(p/"v3-eod-deep-review.json"), "--source-trade-date", "20261007"], capture_output=True, text=True)
    assert r.returncode == 0, (r.stdout, r.stderr)

    bad = json.loads((p/"v3-eod-deep-review-batch-2.json").read_text(encoding="utf-8"))
    bad["candidateCodes"] = list(reversed(bad["candidateCodes"]))
    (p/"v3-eod-deep-review-batch-2.json").write_text(json.dumps(bad), encoding="utf-8")
    r = subprocess.run(["python", str(ASSEMBLER), "--root", str(p), "--allow-incomplete"], capture_output=True, text=True)
    assert r.returncode == 0 and '"status": "INCOMPLETE"' in r.stdout, (r.stdout, r.stderr)

print("V3 EOD deep-review contract tests: PASS")
