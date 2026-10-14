#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

SCHEMA = "V3_0815_SHADOW_BUNDLE_V1"
ORIGINS = {"MACHINE_CONTINUITY_FALLBACK", "ASSISTANT_DEEP_REVIEW"}
LIVE_STATES = {"ATTACK_PLAN", "PROBE_PLAN"}


def validate_eod_provenance(d: dict, source_root: Path, errors: list[str]) -> None:
    """Fail closed unless a FULL assistant bundle uses the current independent EOD.

    This does NOT assert that external news was actually inspected. It only
    proves that today's proposed codes originate in a completed, linked EOD
    review and that the review predates the alleged assistant premarket plan.
    """
    from datetime import datetime, timedelta

    names = (
        "market-structure-v3-handoff.json",
        "market-structure-v3-review-index.json",
        "v3-eod-deep-review.json",
    )
    try:
        handoff, index, eod = [
            json.loads((source_root / name).read_text(encoding="utf-8"))
            for name in names
        ]
    except (OSError, ValueError, TypeError) as exc:
        errors.append(f"assistant source EOD unavailable/invalid:{type(exc).__name__}:{exc}")
        return

    if handoff.get("schemaVersion") != "MARKET_STRUCTURE_V3_HANDOFF_V1":
        errors.append("assistant EOD handoff schema invalid")
    if index.get("schemaVersion") != "MARKET_STRUCTURE_V3_REVIEW_INDEX_V1":
        errors.append("assistant EOD review index schema invalid")
    if eod.get("schemaVersion") != "V3_EOD_DEEP_REVIEW_V1":
        errors.append("assistant merged EOD schema invalid")

    for label, obj in (("handoff", handoff), ("index", index), ("merged EOD", eod)):
        if obj.get("mode") != "SHADOW_ONLY" or obj.get("productionWriteAllowed") is not False:
            errors.append(f"assistant {label} isolation invalid")
        if obj.get("status") != "PASS":
            errors.append(f"assistant {label} not PASS")

    source_date = index.get("tradeDate")
    generated_index = index.get("generatedAtKst")
    method = index.get("methodologyVersion")
    run_id = (handoff.get("source") or {}).get("workflowRunId")
    src = d.get("source") or {}
    links = (
        (handoff.get("tradeDate"), source_date, "handoff.tradeDate"),
        (handoff.get("generatedAtKst"), generated_index, "handoff.generatedAtKst"),
        (handoff.get("methodologyVersion"), method, "handoff.methodologyVersion"),
        (eod.get("sourceTradeDate"), source_date, "eod.sourceTradeDate"),
        (eod.get("sourceIndexGeneratedAtKst"), generated_index, "eod.indexGeneratedAtKst"),
        (eod.get("sourceWorkflowRunId"), run_id, "eod.workflowRunId"),
        (eod.get("methodologyVersion"), method, "eod.methodologyVersion"),
        (d.get("sourceTradeDate"), source_date, "bundle.sourceTradeDate"),
        (src.get("marketStructureTradeDate"), source_date, "bundle.source.marketStructureTradeDate"),
        (src.get("reviewIndexGeneratedAtKst"), generated_index, "bundle.source.reviewIndexGeneratedAtKst"),
        (src.get("marketStructureWorkflowRunId"), run_id, "bundle.source.marketStructureWorkflowRunId"),
        (src.get("methodologyVersion"), method, "bundle.source.methodologyVersion"),
    )
    for actual, expected, label in links:
        if actual is None or expected is None or actual != expected:
            errors.append(f"assistant EOD source mismatch:{label}")

    if eod.get("assistantDeepReviewCompleted") is not True:
        errors.append("assistant merged EOD deep review incomplete")
    codes = index.get("codes")
    reviewed_codes = eod.get("codes")
    reviews = eod.get("reviews")
    if not isinstance(codes, list) or not isinstance(reviewed_codes, list) or codes != reviewed_codes:
        errors.append("assistant EOD/index code order mismatch")
        return
    if not isinstance(reviews, list) or len(reviews) != len(codes) or eod.get("reviewCount") != len(codes):
        errors.append("assistant EOD review count invalid")
        return
    if not (len(codes) <= 36 and len(codes) == len(set(codes))):
        errors.append("assistant EOD index codes invalid")
    if index.get("totalCount") != len(codes):
        errors.append("assistant EOD index count mismatch")
    eligible = set()
    for i, (code, row) in enumerate(zip(codes, reviews)):
        if not isinstance(row, dict) or row.get("code") != code:
            errors.append(f"assistant EOD review[{i}] code mismatch")
            continue
        state = row.get("chartState")
        if state in {"ATTACK_CANDIDATE", "PROBE_CANDIDATE"}:
            eligible.add(code)
        elif state not in {"WATCH", "REJECT"}:
            errors.append(f"assistant EOD review[{i}] invalid chartState")

    selected = (d.get("watchlist") or {}).get("codes") or []
    for code in selected:
        if code not in eligible:
            errors.append(f"assistant plan code not approved by independent EOD review:{code}")

    try:
        bundle_time = datetime.fromisoformat(d.get("generatedAtKst"))
        if bundle_time.tzinfo is None or bundle_time.utcoffset() != timedelta(hours=9):
            raise ValueError("bundle time must be KST")
        if not isinstance(source_date, str) or source_date >= d.get("tradeDate", ""):
            raise ValueError("source EOD must precede tradeDate")
        batches = eod.get("batches")
        if not isinstance(batches, list) or len(batches) != 3:
            raise ValueError("merged EOD batches must equal 3")
        if sum(b.get("count", -1) for b in batches) != len(codes):
            raise ValueError("merged EOD batch coverage mismatch")
        for i, batch in enumerate(batches, start=1):
            if batch.get("batchIndex") != i:
                raise ValueError("batch index mismatch")
            t = datetime.fromisoformat(batch.get("reviewedAtKst"))
            if t.tzinfo is None or t.utcoffset() != timedelta(hours=9) or t > bundle_time:
                raise ValueError(f"batch-{i} reviewed later than premarket bundle")
    except (TypeError, ValueError) as exc:
        errors.append(f"assistant EOD temporal linkage invalid:{exc}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--trade-date", default=None)
    ap.add_argument("--source-root", default=None, help="verify full assistant plan against independently merged EOD files")
    args = ap.parse_args()

    d = json.loads(Path(args.path).read_text(encoding="utf-8"))
    errors: list[str] = []

    if d.get("schemaVersion") != SCHEMA:
        errors.append("wrong schemaVersion")
    if d.get("mode") != "SHADOW_ONLY":
        errors.append("mode must be SHADOW_ONLY")
    if d.get("productionWriteAllowed") is not False:
        errors.append("productionWriteAllowed must be false")
    if args.trade_date and d.get("tradeDate") != args.trade_date:
        errors.append(f"tradeDate mismatch:{d.get('tradeDate')}!={args.trade_date}")

    status = d.get("status")
    if status not in {"READY", "VALID_EMPTY", "MARKET_CLOSED"}:
        errors.append(f"invalid status={status}")

    origin = d.get("planOrigin")
    if origin not in ORIGINS:
        errors.append(f"invalid planOrigin={origin}")
    degraded = d.get("degradedMode")
    deep = d.get("assistantDeepReviewCompleted")
    if origin == "MACHINE_CONTINUITY_FALLBACK":
        if degraded is not True:
            errors.append("fallback must degradedMode=true")
        if deep is not False:
            errors.append("fallback must assistantDeepReviewCompleted=false")
    if origin == "ASSISTANT_DEEP_REVIEW":
        if degraded is not False:
            errors.append("assistant bundle must degradedMode=false")
        if deep is not True:
            errors.append("assistant bundle must assistantDeepReviewCompleted=true")

    wl = d.get("watchlist") or {}
    codes = wl.get("codes") or []
    plans = d.get("livePlans") or []
    if wl.get("status") != status:
        errors.append("watchlist.status mismatch bundle.status")
    if not isinstance(codes, list) or not isinstance(plans, list):
        errors.append("codes/livePlans must be arrays")
        codes, plans = [], []

    norm = [str(x) for x in codes]
    if any(len(c) != 6 or not c.isdigit() for c in norm):
        errors.append("invalid code")
    if len(norm) != len(set(norm)):
        errors.append("duplicate code")

    if status == "MARKET_CLOSED":
        if norm or plans:
            errors.append("MARKET_CLOSED must have empty codes/livePlans")
        if d.get("sourceTradeDate") is not None:
            errors.append("MARKET_CLOSED sourceTradeDate must be null")
    elif status == "VALID_EMPTY":
        if norm or plans:
            errors.append("VALID_EMPTY must have empty codes/livePlans")
        if not d.get("sourceTradeDate"):
            errors.append("VALID_EMPTY sourceTradeDate missing")
    elif status == "READY":
        if not norm:
            errors.append("READY must have codes")
        if not d.get("sourceTradeDate"):
            errors.append("READY sourceTradeDate missing")
        plan_codes = [str((p or {}).get("code") or "") for p in plans]
        if plan_codes != norm:
            errors.append("livePlans codes must exact-match watchlist codes/order")
        for i, p in enumerate(plans):
            if p.get("planState") not in LIVE_STATES:
                errors.append(f"livePlans[{i}] invalid planState={p.get('planState')}")
            for key in ("actionableZone", "trigger", "invalidation", "noChase", "counterargument"):
                if p.get(key) in (None, ""):
                    errors.append(f"livePlans[{i}] missing {key}")

    # Full assistant plans must be backed by candidate-linked, dated sources.
    # Schema validation cannot prove a web page was actually opened; the assistant
    # must still retrieve and inspect each source before claiming it as evidence.
    if origin == "ASSISTANT_DEEP_REVIEW" and status == "READY":
        from datetime import datetime, timedelta
        from urllib.parse import urlsplit

        lanes = {
            "companyQuality": {"SUPPORTIVE", "MIXED", "ADVERSE", "UNKNOWN"},
            "earningsRevision": {"UP_REVISION", "STABLE", "DOWN_REVISION", "UNKNOWN"},
            "catalyst": {"ACTIVE", "UPCOMING", "NONE_IDENTIFIED", "UNKNOWN"},
            "industryMacro": {"TAILWIND", "NEUTRAL", "HEADWIND", "UNKNOWN"},
            "globalUsLead": {"CONFIRMING", "NEUTRAL", "CONTRADICTING", "NOT_MATERIAL", "UNKNOWN"},
            "eventRisk": {"LOW", "MODERATE", "HIGH", "UNKNOWN"},
        }
        delta = d.get("overnightDelta") or {}
        evidence = delta.get("evidence")
        verified_count = delta.get("verifiedEvidenceCount")
        if not isinstance(evidence, list) or not evidence:
            errors.append("assistant READY requires overnightDelta.evidence source ledger")
            evidence = []
        if type(verified_count) is not int or verified_count != len(evidence) or verified_count < 1:
            errors.append("overnightDelta.verifiedEvidenceCount must match evidence ledger")

        by_id = {}
        candidate_sources = {code: set() for code in norm}
        global_sources = set()
        for j, item in enumerate(evidence):
            label = f"overnightDelta.evidence[{j}]"
            if not isinstance(item, dict):
                errors.append(f"{label} must be object")
                continue
            evidence_id = item.get("id")
            if not isinstance(evidence_id, str) or not evidence_id.strip() or evidence_id in by_id:
                errors.append(f"{label} missing/duplicate id")
                continue
            by_id[evidence_id] = item
            for field in ("sourceType", "sourceDate", "observationDate", "sourceUrl", "summary"):
                value = item.get(field)
                if not isinstance(value, str) or not value.strip():
                    errors.append(f"{label} missing {field}")
            for field in ("sourceDate", "observationDate"):
                value = item.get(field)
                try:
                    dt = datetime.strptime(value, "%Y-%m-%d").date()
                    if dt.strftime("%Y-%m-%d") != value:
                        raise ValueError("noncanonical date")
                    if d.get("tradeDate") and dt.strftime("%Y%m%d") > d["tradeDate"]:
                        errors.append(f"{label} {field} after tradeDate")
                except (ValueError, TypeError):
                    errors.append(f"{label} invalid {field}")
            url = item.get("sourceUrl")
            parsed = urlsplit(url) if isinstance(url, str) else None
            if not parsed or parsed.scheme != "https" or not parsed.hostname or parsed.hostname in {"localhost", "example.com"}:
                errors.append(f"{label} sourceUrl must be real https source (not a placeholder)")
            ev_lanes = item.get("lanes")
            if not isinstance(ev_lanes, list) or not ev_lanes or len(ev_lanes) != len(set(ev_lanes)):
                errors.append(f"{label} lanes must be nonempty unique list")
                ev_lanes = []
            elif any(lane not in lanes for lane in ev_lanes):
                errors.append(f"{label} contains invalid lane")
            scope = item.get("scope")
            code = item.get("code")
            if scope == "CANDIDATE" and code in candidate_sources:
                candidate_sources[code].add(evidence_id)
            elif scope == "GLOBAL" and code in (None, ""):
                global_sources.add(evidence_id)
                if any(lane not in {"industryMacro", "globalUsLead", "eventRisk"} for lane in ev_lanes):
                    errors.append(f"{label} GLOBAL cannot support candidate-specific fundamentals")
            else:
                errors.append(f"{label} invalid scope/code linkage")
        if not global_sources:
            errors.append("assistant READY missing GLOBAL macro/US/event research evidence")

        for i, plan in enumerate(plans):
            code = str(plan.get("code") or "") if isinstance(plan, dict) else ""
            ext = plan.get("externalEvidence") if isinstance(plan, dict) else None
            if not candidate_sources.get(code):
                errors.append(f"livePlans[{i}] no candidate-specific external research source")
            if not isinstance(ext, dict):
                errors.append(f"livePlans[{i}] missing externalEvidence")
                continue
            known = 0
            for lane, allowed in lanes.items():
                datum = ext.get(lane)
                state = datum.get("state") if isinstance(datum, dict) else None
                if state not in allowed:
                    errors.append(f"livePlans[{i}].externalEvidence.{lane} invalid/missing state")
                    continue
                if state == "UNKNOWN":
                    for field in ("reason", "checkedSources"):
                        if field == "reason" and (not isinstance(datum.get(field), str) or not datum[field].strip()):
                            errors.append(f"livePlans[{i}].externalEvidence.{lane} UNKNOWN requires reason")
                        if field == "checkedSources" and (
                            not isinstance(datum.get(field), list) or not datum[field]
                            or not all(isinstance(z, str) and z.strip() for z in datum[field])
                        ):
                            errors.append(f"livePlans[{i}].externalEvidence.{lane} UNKNOWN requires checkedSources")
                    continue
                known += 1
                ids = datum.get("evidenceIds")
                if not isinstance(ids, list) or not ids or not all(isinstance(z, str) for z in ids):
                    errors.append(f"livePlans[{i}].externalEvidence.{lane} missing evidenceIds")
                    continue
                for source_id in ids:
                    item = by_id.get(source_id)
                    if not item:
                        errors.append(f"livePlans[{i}].externalEvidence.{lane} dangling evidenceId={source_id}")
                        continue
                    if lane not in item.get("lanes", []):
                        errors.append(f"livePlans[{i}].externalEvidence.{lane} unsupported by evidenceId={source_id}")
                    if item.get("scope") == "CANDIDATE" and item.get("code") != code:
                        errors.append(f"livePlans[{i}].externalEvidence.{lane} wrong candidate evidenceId={source_id}")
                    if item.get("scope") == "GLOBAL" and lane not in {"industryMacro", "globalUsLead", "eventRisk"}:
                        errors.append(f"livePlans[{i}].externalEvidence.{lane} global evidence cannot support company claims")
            # Machine evaluation must never infer a numeric threshold or time
            # rule from assistant prose after the session has opened.
            rules = plan.get("executionRules") if isinstance(plan, dict) else None
            if not isinstance(rules, dict):
                errors.append(f"livePlans[{i}] missing executionRules")
            else:
                trig = rules.get("triggerPrice")
                inv = plan.get("invalidation")
                hold = rules.get("holdMinutes")
                chase = rules.get("maxChasePct")
                def valid_number(v):
                    import math
                    return isinstance(v, (float, int)) and not isinstance(v, bool) and math.isfinite(v)
                if not (valid_number(trig) and valid_number(inv) and 0 < inv < trig):
                    errors.append(f"livePlans[{i}] executionRules trigger/invalidation invalid")
                if type(hold) is not int or not 1 <= hold <= 36:
                    errors.append(f"livePlans[{i}] executionRules holdMinutes invalid")
                if not valid_number(chase) or not 0 <= chase <= 100:
                    errors.append(f"livePlans[{i}] executionRules maxChasePct invalid")
                if rules.get("confirmationMode") != "CLOSE_ABOVE_N_CONSECUTIVE_SNAPSHOTS":
                    errors.append(f"livePlans[{i}] unsupported confirmationMode")
            if known == 0:
                errors.append(f"livePlans[{i}] all external evidence UNKNOWN: incomplete deep review")

        # No retrospective "08:15 completed" claim for a substantially late plan.
        generated = d.get("generatedAtKst")
        try:
            ts = datetime.fromisoformat(generated)
            if ts.tzinfo is None or ts.utcoffset() != timedelta(hours=9) or ts.strftime("%Y%m%d") != d.get("tradeDate"):
                raise ValueError("timestamp date/timezone mismatch")
            if d.get("sourcePlanGeneratedAt") != generated:
                errors.append("sourcePlanGeneratedAt must equal generatedAtKst")
            if ts.hour > 8 or (ts.hour == 8 and ts.minute > 30):
                errors.append("assistant READY generated after 08:30 KST deadline")
        except (TypeError, ValueError):
            errors.append("assistant READY generatedAtKst must be valid KST timestamp")

    if origin == "ASSISTANT_DEEP_REVIEW" and status in {"READY", "VALID_EMPTY"} and args.source_root:
        validate_eod_provenance(d, Path(args.source_root), errors)

    out = {"status": "PASS" if not errors else "FAIL", "errorCount": len(errors), "errors": errors[:100]}
    print(json.dumps(out, ensure_ascii=False))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
