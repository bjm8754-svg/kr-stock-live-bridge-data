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

def run(obj, ok, source_root=None):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)
        p = f.name
    cmd = ["python", str(VALIDATOR), p, "--trade-date", "20261007"]
    if source_root is not None:
        cmd += ["--source-root", str(source_root)]
    r = subprocess.run(cmd, capture_output=True, text=True)
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
# Assistant schema-only test fixtures. URLs here test syntax; not page truth.
assistant = json.loads(json.dumps(base))
assistant["planOrigin"] = "ASSISTANT_DEEP_REVIEW"
assistant["degradedMode"] = False
assistant["assistantDeepReviewCompleted"] = True
assistant["sourcePlanGeneratedAt"] = assistant["generatedAtKst"]
assistant["livePlans"][0]["executionRules"] = {
    "triggerPrice": 100, "confirmationMode": "CLOSE_ABOVE_N_CONSECUTIVE_SNAPSHOTS",
    "holdMinutes": 3, "maxChasePct": 5,
}
assistant["livePlans"][0]["externalEvidence"] = {
    "companyQuality": {"state": "MIXED", "evidenceIds": ["co1"]},
    "earningsRevision": {"state": "UNKNOWN", "reason": "Revision report could not be verified", "checkedSources": ["broker research", "DART"]},
    "catalyst": {"state": "UNKNOWN", "reason": "Announcement relevance unresolved", "checkedSources": ["KRX KIND"]},
    "industryMacro": {"state": "NEUTRAL", "evidenceIds": ["macro1"]},
    "globalUsLead": {"state": "NEUTRAL", "evidenceIds": ["macro1"]},
    "eventRisk": {"state": "MODERATE", "evidenceIds": ["macro1"]},
}
assistant["overnightDelta"] = {
    "verifiedEvidenceCount": 2,
    "evidence": [
        {
            "id": "co1", "scope": "CANDIDATE", "code": "000001", "lanes": ["companyQuality"],
            "sourceType": "COMPANY_IR", "sourceDate": "2026-10-06",
            "observationDate": "2026-10-07", "sourceUrl": "https://dart.fss.or.kr/",
            "summary": "Schema test fixture, not a verified live company conclusion",
        },
        {
            "id": "macro1", "scope": "GLOBAL", "code": None,
            "lanes": ["industryMacro", "globalUsLead", "eventRisk"],
            "sourceType": "MARKET_DATA", "sourceDate": "2026-10-07",
            "observationDate": "2026-10-07", "sourceUrl": "https://www.nasdaq.com/",
            "summary": "Schema test fixture, not a verified live macro conclusion",
        },
    ],
}
run(assistant, True)

missing_evidence = json.loads(json.dumps(assistant))
missing_evidence["overnightDelta"]["evidence"] = []
missing_evidence["overnightDelta"]["verifiedEvidenceCount"] = 0
run(missing_evidence, False)

all_unknown = json.loads(json.dumps(assistant))
all_unknown["livePlans"][0]["externalEvidence"] = {
    key: {"state": "UNKNOWN", "reason": "Source unavailable", "checkedSources": ["DART"]}
    for key in assistant["livePlans"][0]["externalEvidence"]
}
run(all_unknown, False)

unknown_without_reason = json.loads(json.dumps(assistant))
unknown_without_reason["livePlans"][0]["externalEvidence"]["earningsRevision"] = {"state": "UNKNOWN"}
run(unknown_without_reason, False)

bad_count = json.loads(json.dumps(assistant))
bad_count["overnightDelta"]["verifiedEvidenceCount"] = 3
run(bad_count, False)

missing_candidate = json.loads(json.dumps(assistant))
missing_candidate["overnightDelta"]["evidence"][0]["scope"] = "GLOBAL"
missing_candidate["overnightDelta"]["evidence"][0]["code"] = None
run(missing_candidate, False)

wrong_candidate = json.loads(json.dumps(assistant))
wrong_candidate["overnightDelta"]["evidence"][0]["code"] = "000002"
run(wrong_candidate, False)

dangling = json.loads(json.dumps(assistant))
dangling["livePlans"][0]["externalEvidence"]["companyQuality"]["evidenceIds"] = ["no-such-source"]
run(dangling, False)

mismatched_lane = json.loads(json.dumps(assistant))
mismatched_lane["livePlans"][0]["externalEvidence"]["companyQuality"]["evidenceIds"] = ["macro1"]
run(mismatched_lane, False)

late = json.loads(json.dumps(assistant))
late["generatedAtKst"] = "2026-10-07T08:42:37+09:00"
run(late, False)

placeholder_url = json.loads(json.dumps(assistant))
placeholder_url["overnightDelta"]["evidence"][0]["sourceUrl"] = "https://example.com/article"
run(placeholder_url, False)

no_execution_rules = json.loads(json.dumps(assistant))
no_execution_rules["livePlans"][0].pop("executionRules")
run(no_execution_rules, False)

unverifiable_trigger = json.loads(json.dumps(assistant))
unverifiable_trigger["livePlans"][0]["executionRules"]["triggerPrice"] = "hold above 100"
run(unverifiable_trigger, False)

invalid_hold = json.loads(json.dumps(assistant))
invalid_hold["livePlans"][0]["executionRules"]["holdMinutes"] = 0
run(invalid_hold, False)

invalid_chase = json.loads(json.dumps(assistant))
invalid_chase["livePlans"][0]["executionRules"]["maxChasePct"] = "unknown"
run(invalid_chase, False)

# KRX KOSPI/KOSDAQ ordinary-share quote ticks (2023 harmonised schedule).
# Reject numeric-but-untradeable levels: never silently round or change
# the assistant's frozen trigger/invalidation.
def with_execution_prices(trigger, invalidation):
    plan = json.loads(json.dumps(assistant))
    plan["livePlans"][0]["executionRules"]["triggerPrice"] = trigger
    plan["livePlans"][0]["invalidation"] = invalidation
    return plan


# Valid quote prices across every band, including band transitions.
for trigger, invalidation in (
    (100, 99), (1999, 1998), (2000, 1999),
    (4995, 4990), (5000, 4995), (19990, 19980),
    (20000, 19990), (49950, 49900), (50000, 49950),
    (199900, 199800), (200000, 199900),
    (499500, 499000), (500000, 499500),
    (1000000, 999000),
):
    run(with_execution_prices(trigger, invalidation), True)

# Each of the rejected trigger prices is a numeric input but cannot be
# submitted as an actual KRX ordinary-share limit order.
for trigger, invalidation in (
    (2001, 1999), (5001, 4995), (20001, 19990),
    (50050, 49950), (200100, 199900), (500500, 499500),
    (98133, 97200), (97211.5, 97000),
):
    run(with_execution_prices(trigger, invalidation), False)

# Invalidations must be tradable quote levels too; cannot be negative,
# fractional, a boolean, or silently represented by an unusable price.
for stop in (97211.5, 97211, 97050, -100, 0, True, "97000"):
    run(with_execution_prices(98100, stop), False)

# A valid tick does not make a structurally inverted stop legitimate.
run(with_execution_prices(98100, 98100), False)
run(with_execution_prices(98100, 98200), False)

# Cross-file independent EOD provenance gating, absent from schema-only fixtures.
with tempfile.TemporaryDirectory() as tmp:
    root = pathlib.Path(tmp)
    eod_date = "20261006"
    index_created = "2026-10-06T17:10:00+09:00"
    method = "MARKET_STRUCTURE_V3_SYNTHETIC_TEST"
    run_id = 99900011
    index = {
        "schemaVersion": "MARKET_STRUCTURE_V3_REVIEW_INDEX_V1",
        "mode": "SHADOW_ONLY", "productionWriteAllowed": False,
        "status": "PASS", "tradeDate": eod_date,
        "generatedAtKst": index_created, "methodologyVersion": method,
        "totalCount": 2, "codes": ["000001", "000002"],
    }
    handoff = {
        "schemaVersion": "MARKET_STRUCTURE_V3_HANDOFF_V1",
        "mode": "SHADOW_ONLY", "productionWriteAllowed": False,
        "status": "PASS", "tradeDate": eod_date,
        "generatedAtKst": index_created, "methodologyVersion": method,
        "source": {"workflowRunId": run_id},
    }
    eod = {
        "schemaVersion": "V3_EOD_DEEP_REVIEW_V1",
        "mode": "SHADOW_ONLY", "productionWriteAllowed": False,
        "status": "PASS", "assistantDeepReviewCompleted": True,
        "sourceTradeDate": eod_date, "sourceWorkflowRunId": run_id,
        "sourceIndexGeneratedAtKst": index_created, "methodologyVersion": method,
        "reviewCount": 2, "codes": index["codes"],
        "reviews": [
            {"code": "000001", "chartState": "PROBE_CANDIDATE", "thesis": "candidate"},
            {"code": "000002", "chartState": "REJECT", "thesis": "rejected"},
        ],
        "batches": [
            {"batchIndex": 1, "count": 1, "reviewedAtKst": "2026-10-06T19:00:00+09:00"},
            {"batchIndex": 2, "count": 1, "reviewedAtKst": "2026-10-06T19:01:00+09:00"},
            {"batchIndex": 3, "count": 0, "reviewedAtKst": "2026-10-06T19:02:00+09:00"},
        ],
    }

    def write_eod():
        for name, obj in (
            ("market-structure-v3-review-index.json", index),
            ("market-structure-v3-handoff.json", handoff),
            ("v3-eod-deep-review.json", eod),
        ):
            (root / name).write_text(json.dumps(obj), encoding="utf-8")

    source_linked = json.loads(json.dumps(assistant))
    source_linked["source"] = {
        "marketStructureTradeDate": eod_date,
        "marketStructureWorkflowRunId": run_id,
        "reviewIndexGeneratedAtKst": index_created,
        "methodologyVersion": method,
    }
    write_eod()
    run(source_linked, True, root)

    # An EOD chart REJECT can never become a valid 08:15 assistant plan.
    reject_revival = json.loads(json.dumps(source_linked))
    reject_revival["watchlist"]["codes"] = ["000002"]
    reject_revival["livePlans"][0]["code"] = "000002"
    reject_revival["overnightDelta"]["evidence"][0]["code"] = "000002"
    run(reject_revival, False, root)

    # If the EOD merged source is from a different day, block.
    eod["sourceTradeDate"] = "20261003"
    write_eod()
    run(source_linked, False, root)
    eod["sourceTradeDate"] = eod_date

    # EOD analysis completed after 08:15 cannot support a retroactive plan.
    eod["batches"][2]["reviewedAtKst"] = "2026-10-07T09:53:00+09:00"
    write_eod()
    run(source_linked, False, root)
    eod["batches"][2]["reviewedAtKst"] = "2026-10-06T19:02:00+09:00"

    # False source workflow identifier must be detected.
    wrong_source = json.loads(json.dumps(source_linked))
    wrong_source["source"]["marketStructureWorkflowRunId"] = run_id + 1
    write_eod()
    run(wrong_source, False, root)

    # No independent merged EOD, no claim of full assistant review.
    (root / "v3-eod-deep-review.json").unlink()
    run(source_linked, False, root)

print("V3 08:15 shadow bundle validator tests: PASS")
