#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
from zoneinfo import ZoneInfo

import exchange_calendars as xcals
import pandas as pd

KST = ZoneInfo("Asia/Seoul")
PLAN_SCHEMA = "V3_0815_SHADOW_PLAN_V1"
WATCHLIST_SCHEMA = "V3_0815_SHADOW_WATCHLIST_V1"
BUNDLE_SCHEMA = "V3_0815_SHADOW_BUNDLE_V1"
HANDOFF_SCHEMA = "MARKET_STRUCTURE_V3_HANDOFF_V1"
INDEX_SCHEMA = "MARKET_STRUCTURE_V3_REVIEW_INDEX_V1"
SHARD_SCHEMA = "MARKET_STRUCTURE_V3_REVIEW_SHARD_V1"
ORIGIN = "MACHINE_CONTINUITY_FALLBACK"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: dict) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")


def finite(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(float(v))


def krw(v: float) -> str:
    return f"{int(round(float(v))):,} KRW"


def current_session_state(today: str) -> tuple[bool, str | None]:
    cal = xcals.get_calendar("XKRX")
    ts = pd.Timestamp(dt.datetime.strptime(today, "%Y%m%d").date())
    if not cal.is_session(ts):
        return False, None
    prev = cal.previous_session(ts)
    return True, prev.strftime("%Y%m%d")


def validate_source_bundle(root: Path, expected_source_trade_date: str) -> tuple[dict, dict, list[dict]]:
    handoff = read_json(root / "market-structure-v3-handoff.json")
    index = read_json(root / "market-structure-v3-review-index.json")

    if handoff.get("schemaVersion") != HANDOFF_SCHEMA:
        raise RuntimeError("HANDOFF_SCHEMA_MISMATCH")
    if handoff.get("mode") != "SHADOW_ONLY" or handoff.get("productionWriteAllowed") is not False:
        raise RuntimeError("HANDOFF_MODE_MISMATCH")
    for key in ("status", "freshnessStatus"):
        if handoff.get(key) != "PASS":
            raise RuntimeError(f"HANDOFF_{key.upper()}_NOT_PASS")
    for key in ("canonicalValidated", "reviewPacketValidated", "reviewShardsValidated"):
        if handoff.get(key) is not True:
            raise RuntimeError(f"HANDOFF_{key.upper()}_FALSE")
    if str(handoff.get("tradeDate") or "") != expected_source_trade_date:
        raise RuntimeError(f"HANDOFF_STALE:{handoff.get('tradeDate')}!={expected_source_trade_date}")

    if index.get("schemaVersion") != INDEX_SCHEMA:
        raise RuntimeError("INDEX_SCHEMA_MISMATCH")
    if index.get("mode") != "SHADOW_ONLY" or index.get("productionWriteAllowed") is not False:
        raise RuntimeError("INDEX_MODE_MISMATCH")
    if index.get("status") != "PASS" or index.get("sourceSchemaVersion") != "MARKET_STRUCTURE_V3":
        raise RuntimeError("INDEX_STATUS_OR_SOURCE_MISMATCH")

    for key in ("tradeDate", "generatedAtKst", "methodologyVersion"):
        if index.get(key) != handoff.get(key):
            raise RuntimeError(f"HANDOFF_INDEX_LINK_MISMATCH:{key}")

    coverage = handoff.get("coverage") or {}
    if int(index.get("totalCount") or 0) != int(coverage.get("reviewCount") or 0):
        raise RuntimeError("REVIEW_COUNT_MISMATCH")
    if int(index.get("shardCount") or 0) != int(coverage.get("reviewShardCount") or 0):
        raise RuntimeError("SHARD_COUNT_MISMATCH")
    if (handoff.get("source") or {}).get("reviewIndexPath") != "market-structure-v3-review-index.json":
        raise RuntimeError("REVIEW_INDEX_PATH_MISMATCH")

    metas = index.get("shards") or []
    if len(metas) != int(index.get("shardCount") or 0):
        raise RuntimeError("INDEX_SHARD_META_COUNT_MISMATCH")

    rows: list[dict] = []
    reconstructed: list[str] = []
    for expected_i, meta in enumerate(metas, start=1):
        path = root / str(meta.get("path") or "")
        raw = path.read_bytes()
        if int(meta.get("byteSize") or -1) != len(raw):
            raise RuntimeError(f"SHARD_SIZE_MISMATCH:{path.name}")
        if hashlib.sha256(raw).hexdigest() != meta.get("sha256"):
            raise RuntimeError(f"SHARD_SHA256_MISMATCH:{path.name}")
        shard = json.loads(raw.decode("utf-8"))
        if shard.get("schemaVersion") != SHARD_SCHEMA:
            raise RuntimeError(f"SHARD_SCHEMA_MISMATCH:{path.name}")
        if shard.get("mode") != "SHADOW_ONLY" or shard.get("productionWriteAllowed") is not False or shard.get("status") != "PASS":
            raise RuntimeError(f"SHARD_MODE_OR_STATUS_MISMATCH:{path.name}")
        for key in ("tradeDate", "generatedAtKst", "methodologyVersion"):
            if shard.get(key) != index.get(key):
                raise RuntimeError(f"SHARD_LINK_MISMATCH:{path.name}:{key}")
        if int(shard.get("shardIndex") or 0) != expected_i:
            raise RuntimeError(f"SHARD_INDEX_MISMATCH:{path.name}")
        if int(shard.get("shardCount") or 0) != int(index.get("shardCount") or 0):
            raise RuntimeError(f"SHARD_COUNT_META_MISMATCH:{path.name}")
        if shard.get("codes") != meta.get("codes"):
            raise RuntimeError(f"SHARD_CODES_MISMATCH:{path.name}")
        if int(shard.get("count") or 0) != len(shard.get("deepReviewQueue") or []):
            raise RuntimeError(f"SHARD_ROW_COUNT_MISMATCH:{path.name}")
        rows.extend(shard.get("deepReviewQueue") or [])
        reconstructed.extend(shard.get("codes") or [])

    if reconstructed != (index.get("codes") or []):
        raise RuntimeError("RECONSTRUCTED_CODES_MISMATCH")
    if len(reconstructed) != len(set(reconstructed)):
        raise RuntimeError("DUPLICATE_CODES")
    if len(rows) != int(index.get("totalCount") or 0):
        raise RuntimeError("RECONSTRUCTED_COUNT_MISMATCH")
    return handoff, index, rows


def observed_levels(row: dict) -> tuple[float | None, float | None, float | None, float | None]:
    execution = row.get("execution") or {}
    primary = (row.get("setups") or {}).get("primary") or {}
    trigger = primary.get("triggerLevel")
    if not finite(trigger):
        trigger = execution.get("entryReference")
    invalidation = execution.get("invalidation")
    if not finite(invalidation):
        invalidation = primary.get("invalidationLevel")
    support = execution.get("nearestAcceptedSupport")
    resistance = execution.get("nextResistance")
    return (
        float(trigger) if finite(trigger) else None,
        float(invalidation) if finite(invalidation) else None,
        float(support) if finite(support) else None,
        float(resistance) if finite(resistance) else None,
    )


def eligible(row: dict) -> bool:
    execution = row.get("execution") or {}
    trigger, invalidation, _, _ = observed_levels(row)
    if execution.get("readiness") != "EXECUTABLE":
        return False
    if trigger is None or invalidation is None or invalidation >= trigger:
        return False
    return len(str(row.get("code") or "")) == 6


def candidate_sort_key(row: dict):
    execution = row.get("execution") or {}
    review = row.get("review") or {}
    proximity = execution.get("currentVsEntryPct")
    if not finite(proximity):
        close = (row.get("price") or {}).get("close")
        trigger, _, _, _ = observed_levels(row)
        proximity = abs((float(close) - trigger) / trigger * 100.0) if finite(close) and trigger else 9999.0
    warnings = len(execution.get("warnings") or []) + len((row.get("confirmation") or {}).get("warnings") or [])
    tier = 0 if review.get("reviewTier") == "NOW" else 1
    return (tier, abs(float(proximity)), warnings, str(row.get("code") or ""))


def make_candidate(row: dict) -> tuple[dict, dict]:
    code = str(row.get("code"))
    name = row.get("name") or code
    trigger, invalidation, support, resistance = observed_levels(row)
    assert trigger is not None and invalidation is not None

    if support is not None and invalidation < support <= trigger:
        important_zone = f"{krw(support)} - {krw(trigger)} observed support/trigger zone"
    else:
        important_zone = f"{krw(trigger)} observed structural trigger"

    primary = (row.get("setups") or {}).get("primary") or {}
    family = primary.get("family") or "UNCLASSIFIED"
    state = primary.get("state") or "UNCLASSIFIED"
    machine_warnings = (row.get("execution") or {}).get("warnings") or []
    warning_text = ",".join(map(str, machine_warnings)) if machine_warnings else "none"

    chart = {
        "code": code,
        "name": name,
        "chartState": "PROBE_CANDIDATE",
        "thesis": f"Continuity fallback only: machine-observed {family}/{state} near a traceable decision level; assistant deep review is still required for cutover.",
        "importantZone": important_zone,
        "confirmation": f"Accept/hold above observed trigger {krw(trigger)} after retest/participation; a touch alone is insufficient.",
        "invalidation": invalidation,
        "nextResistance": resistance,
        "chaseJudgement": f"NO_CHASE if price is extended away from observed trigger {krw(trigger)} without a retest/acceptance.",
        "counterargument": f"Degraded machine continuity plan, not independent assistant chart review; machine warnings={warning_text}.",
    }

    plan = {
        "code": code,
        "name": name,
        "planState": "PROBE_PLAN",
        "actionableZone": important_zone,
        "trigger": chart["confirmation"],
        "invalidation": invalidation,
        "noChase": chart["chaseJudgement"],
        "nextResistance": resistance,
        "counterargument": chart["counterargument"],
        "externalEvidence": {
            "companyQuality": {"state": "UNKNOWN"},
            "earningsRevision": {"state": "UNKNOWN"},
            "catalyst": {"state": "UNKNOWN"},
            "industryMacro": {"state": "UNKNOWN"},
            "globalUsLead": {"state": "UNKNOWN"},
            "eventRisk": {"state": "UNKNOWN"},
        },
    }
    if resistance is not None and resistance > trigger > invalidation:
        rr = (resistance - trigger) / (trigger - invalidation)
        if math.isfinite(rr) and rr > 0:
            plan["structuralRR"] = round(rr, 3)
    return chart, plan


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--today", default=None, help="YYYYMMDD; default current KST date")
    ap.add_argument("--max-live-candidates", type=int, default=5)
    ap.add_argument("--plan-output", default="v3-0815-shadow-plan.json")
    ap.add_argument("--watchlist-output", default="v3-0815-shadow-watchlist.json")
    ap.add_argument("--bundle-output", default="v3-0815-shadow-bundle.json")
    args = ap.parse_args()

    root = Path(args.root)
    today = args.today or dt.datetime.now(KST).strftime("%Y%m%d")
    now = dt.datetime.now(KST).isoformat()
    is_open, expected_source = current_session_state(today)

    watchlist_path = root / args.watchlist_output
    bundle_path = root / args.bundle_output
    plan_path = root / args.plan_output

    if not is_open:
        watchlist = {
            "schemaVersion": WATCHLIST_SCHEMA,
            "mode": "SHADOW_ONLY",
            "productionWriteAllowed": False,
            "tradeDate": today,
            "sourceTradeDate": None,
            "status": "MARKET_CLOSED",
            "codes": [],
            "planOrigin": ORIGIN,
            "degradedMode": True,
        }
        bundle = {
            "schemaVersion": BUNDLE_SCHEMA,
            "mode": "SHADOW_ONLY",
            "productionWriteAllowed": False,
            "tradeDate": today,
            "sourceTradeDate": None,
            "status": "MARKET_CLOSED",
            "generatedAtKst": now,
            "planOrigin": ORIGIN,
            "degradedMode": True,
            "assistantDeepReviewCompleted": False,
            "watchlist": {"status": "MARKET_CLOSED", "codes": []},
            "livePlans": [],
        }
        write_json(watchlist_path, watchlist)
        write_json(bundle_path, bundle)
        print(json.dumps({"status": "MARKET_CLOSED", "tradeDate": today}, ensure_ascii=False))
        return

    assert expected_source is not None
    handoff, index, rows = validate_source_bundle(root, expected_source)
    selected = sorted([r for r in rows if eligible(r)], key=candidate_sort_key)[: max(0, args.max_live_candidates)]

    chart_reviews: list[dict] = []
    plans: list[dict] = []
    for row in selected:
        chart, plan = make_candidate(row)
        chart_reviews.append(chart)
        plans.append(plan)
    codes = [p["code"] for p in plans]
    status = "READY" if codes else "VALID_EMPTY"

    plan = {
        "schemaVersion": PLAN_SCHEMA,
        "mode": "SHADOW_ONLY",
        "productionWriteAllowed": False,
        "tradeDate": today,
        "generatedAtKst": now,
        "planOrigin": ORIGIN,
        "degradedMode": True,
        "assistantDeepReviewCompleted": False,
        "source": {
            "tradeDate": expected_source,
            "freshnessStatus": "PASS",
            "methodologyVersion": handoff.get("methodologyVersion"),
            "reviewPacketValidated": True,
            "canonicalValidated": True,
            "reviewShardsValidated": True,
            "workflowRunId": (handoff.get("source") or {}).get("workflowRunId"),
            "coverage": handoff.get("coverage") or {},
        },
        "chartReview": chart_reviews,
        "plans": plans,
        "notes": [
            "MACHINE_CONTINUITY_FALLBACK: created by GitHub Actions so live evidence collection does not depend on assistant connector writes.",
            "This degraded plan is diagnostic only and can never authorize production cutover.",
            "Observed structural levels are preserved; no post-open redesign or wider invalidation is allowed.",
        ],
    }
    watchlist = {
        "schemaVersion": WATCHLIST_SCHEMA,
        "mode": "SHADOW_ONLY",
        "productionWriteAllowed": False,
        "tradeDate": today,
        "sourceTradeDate": expected_source,
        "status": status,
        "codes": codes,
        "planOrigin": ORIGIN,
        "degradedMode": True,
        "sourcePlanGeneratedAt": now,
    }
    bundle = {
        "schemaVersion": BUNDLE_SCHEMA,
        "mode": "SHADOW_ONLY",
        "productionWriteAllowed": False,
        "tradeDate": today,
        "sourceTradeDate": expected_source,
        "status": status,
        "generatedAtKst": now,
        "sourcePlanGeneratedAt": now,
        "planOrigin": ORIGIN,
        "degradedMode": True,
        "assistantDeepReviewCompleted": False,
        "source": {
            "marketStructureTradeDate": expected_source,
            "marketStructureWorkflowRunId": (handoff.get("source") or {}).get("workflowRunId"),
            "marketStructureGeneratedAtKst": handoff.get("generatedAtKst"),
            "methodologyVersion": handoff.get("methodologyVersion"),
            "reviewIndexGeneratedAtKst": index.get("generatedAtKst"),
        },
        "watchlist": {"status": status, "codes": codes},
        "livePlans": plans,
    }

    write_json(plan_path, plan)
    write_json(watchlist_path, watchlist)
    write_json(bundle_path, bundle)

    for p in (plan_path, watchlist_path, bundle_path):
        read_json(p)
    if read_json(bundle_path).get("watchlist", {}).get("codes") != codes:
        raise RuntimeError("BUNDLE_READBACK_CODES_MISMATCH")

    print(json.dumps({
        "status": status,
        "tradeDate": today,
        "sourceTradeDate": expected_source,
        "planOrigin": ORIGIN,
        "degradedMode": True,
        "selectedCount": len(codes),
        "codes": codes,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
