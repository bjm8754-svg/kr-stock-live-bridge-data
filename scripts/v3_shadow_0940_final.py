#!/usr/bin/env python3
"""Read-only 09:35/09:40 evidence evaluation. Produces SHADOW JSON only.

Does not scrape, re-plan, change production, or silently interpret prose trade
rules. The caller owns a single-file GitHub commit and remote read-back.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
from pathlib import Path

SCHEMA = "V3_0940_SHADOW_EVAL_V1"
CAPTURE_SCHEMA = "V3_SHADOW_LIVE_CAPTURE_V1"
STATES = {"CONFIRMED", "NOT_CONFIRMED", "INVALIDATED", "NO_CHASE", "DATA_FAIL"}
KST = dt.timezone(dt.timedelta(hours=9))


def require(condition, why):
    if not condition:
        raise ValueError(why)


def numeric(value):
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and value > 0)


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_capture(d, day, end, source_hash):
    label = f"capture-09{end:02d}"
    require(d.get("schemaVersion") == CAPTURE_SCHEMA, f"{label}:schema")
    require(d.get("mode") == "SHADOW_ONLY" and d.get("productionWriteAllowed") is False, f"{label}:isolation")
    require(d.get("tradeDate") == day, f"{label}:tradeDate")
    require((d.get("sourcePlan") or {}).get("bundleSha") == source_hash, f"{label}:frozenBundleSha")
    status = d.get("status")
    require(status in {"PASS", "VALID_EMPTY", "MARKET_CLOSED"}, f"{label}:status={status}")
    codes = d.get("codes")
    src = d.get("sourcePlan") or {}
    require(isinstance(codes, list) and codes == (src.get("watchlist") or {}).get("codes"), f"{label}:watchlistCodes")
    require(isinstance(src.get("livePlans"), list) and
            [x.get("code") for x in src["livePlans"]] == codes, f"{label}:livePlanOrder")
    history = d.get("history") or {}
    rows = history.get("rows")
    require(isinstance(rows, list), f"{label}:historyRows")
    if status == "PASS":
        require(len(codes) > 0 and history.get("count") == end + 1 and len(rows) == end + 1, f"{label}:historyCount")
        expected = [f"{day} 09{i:02d}" for i in range(end + 1)]
        require([x.get("atKst") for x in rows] == expected, f"{label}:historySequence")
        require((d.get("scanDiagnostics") or {}).get("0935", {}).get("status") == "PASS", f"{label}:scanStatus")
        require(list(sorted((d.get("marketScans") or {}).keys())) == ["0935"], f"{label}:oneFullMarketScan")
    else:
        require(not codes and history.get("count") == 0 and not rows, f"{label}:emptyHistory")
        require(not (d.get("marketScans") or {}), f"{label}:emptyScan")
    return src


def price_rows(rows, code):
    values = []
    for row in rows:
        stock = (row.get("stocks") or {}).get(code) or {}
        if stock.get("marketStatus") != "OPEN":
            return None  # PREOPEN, CLOSE and halt snapshots are not intraday evidence.
        p = stock.get("currentPrice")
        # Do not infer a price from previous minutes, indexes, or a different code.
        if not numeric(p):
            return None
        values.append(float(p))
    return values


def eval_path(prices, plan):
    if not prices:
        return "DATA_FAIL", "MISSING_OR_INVALID_MINUTE_PRICE", {}
    raw_inv = plan.get("invalidation")
    if not numeric(raw_inv):
        return "DATA_FAIL", "NO_NUMERIC_INVALIDATION", {}
    inv = float(raw_inv)
    if any(p <= inv for p in prices):
        return "INVALIDATED", "OBSERVED_SNAPSHOT_AT_OR_BELOW_FROZEN_INVALIDATION", {
            "observedMin": min(prices), "invalidation": inv
        }
    rules = plan.get("executionRules")
    if not isinstance(rules, dict):
        return "DATA_FAIL", "UNSTRUCTURED_TRIGGER_OR_NO_CHASE", {
            "observedMin": min(prices), "invalidation": inv
        }
    trigger = rules.get("triggerPrice")
    hold = rules.get("holdMinutes")
    chase = rules.get("maxChasePct")
    mode = rules.get("confirmationMode")
    if not (numeric(trigger) and type(hold) is int and 1 <= hold <= 36
            and isinstance(chase, (int, float)) and not isinstance(chase, bool)
            and math.isfinite(chase) and 0 <= chase <= 100
            and mode == "CLOSE_ABOVE_N_CONSECUTIVE_SNAPSHOTS"):
        return "DATA_FAIL", "INVALID_EXECUTION_RULES", {}
    require(inv < float(trigger), "invalidationNotBelowTrigger")
    window = prices[-hold:] if len(prices) >= hold else []
    confirmed = len(window) == hold and all(p >= float(trigger) for p in window)
    extended = (prices[-1] - float(trigger)) / float(trigger) * 100 > float(chase)
    detail = {
        "observedMin": min(prices), "observedMax": max(prices),
        "last": prices[-1], "triggerPrice": float(trigger), "invalidation": inv,
        "holdMinutes": hold, "maxChasePct": chase,
    }
    if extended:
        return "NO_CHASE", "EXCEEDED_FROZEN_MAX_CHASE_DISTANCE", detail
    if confirmed:
        return "CONFIRMED", "FROZEN_SNAPSHOT_HOLD_RULE_MET", detail
    return "NOT_CONFIRMED", "FROZEN_SNAPSHOT_HOLD_RULE_NOT_MET", detail


def calculate(c35, c40, day, run_id, source_hash):
    s35 = validate_capture(c35, day, 35, source_hash)
    s40 = validate_capture(c40, day, 40, source_hash)
    require(c35.get("status") == c40.get("status"), "captureStatusMismatch")
    require(c35.get("codes") == c40.get("codes"), "captureCodesMismatch")
    for key in ("bundleSha", "planOrigin", "degradedMode", "sourcePlanGeneratedAt",
                "watchlist", "livePlans", "sourceTradeDate", "assistantDeepReviewCompleted"):
        require(s35.get(key) == s40.get(key), f"sourcePlanMismatch:{key}")
    require((c35.get("history") or {}).get("rows") ==
            (c40.get("history") or {}).get("rows", [])[:36], "historyPrefixMismatch")
    require((c35.get("marketScans") or {}) == (c40.get("marketScans") or {}), "marketScanMismatch")
    origin = s40.get("planOrigin")
    degraded = s40.get("degradedMode")
    require(origin in {"MACHINE_CONTINUITY_FALLBACK", "ASSISTANT_DEEP_REVIEW"}, "invalidOrigin")
    require(type(degraded) is bool and
            ((origin == "MACHINE_CONTINUITY_FALLBACK") == degraded), "originDegradedMismatch")
    plan_time = s40.get("sourcePlanGeneratedAt")
    status = c40["status"]
    at35, deltas, evaluated = [], [], []
    all_quality = True
    for plan in s40["livePlans"]:
        code = plan["code"]
        p35 = price_rows(c35["history"]["rows"], code)
        p40 = price_rows(c40["history"]["rows"], code)
        e35, why35, detail35 = eval_path(p35, plan)
        e40, why40, detail40 = eval_path(p40, plan)
        at35.append({"code": code, "evaluation": e35, "reason": why35, "detail": detail35})
        deltas.append({
            "code": code, "price0935": p35[-1] if p35 else None,
            "price0940": p40[-1] if p40 else None,
            "priceDelta": round(p40[-1] - p35[-1], 4) if p35 and p40 else None,
            "evaluation0935": e35, "evaluation0940": e40
        })
        evaluated.append({"code": code, "name": plan.get("name"), "finalEvaluation": e40, "reason": why40, "detail": detail40})
        evidence = plan.get("externalEvidence") or {}
        lanes = ("companyQuality", "earningsRevision", "catalyst", "industryMacro", "globalUsLead", "eventRisk")
        # The user contract disallows a candidate with ALL six axes UNKNOWN;
        # one genuinely unverified axis is not by itself a full-cycle failure.
        if not isinstance(evidence, dict):
            all_quality = False
        else:
            states = [evidence.get(k) for k in lanes]
            if any(not isinstance(v, dict) or not v.get("state") for v in states):
                all_quality = False
            elif all(v["state"] == "UNKNOWN" for v in states):
                all_quality = False
            elif any(v["state"] != "UNKNOWN" and not v.get("evidenceIds") for v in states):
                all_quality = False
    if status == "MARKET_CLOSED":
        cycle = "MARKET_CLOSED"
    elif status == "VALID_EMPTY":
        cycle = "PARTIAL"
    elif origin != "ASSISTANT_DEEP_REVIEW" or degraded or not all_quality:
        cycle = "PARTIAL"
    elif any(x["finalEvaluation"] == "DATA_FAIL" for x in evaluated):
        cycle = "PARTIAL"
    elif not s40.get("assistantDeepReviewCompleted"):
        cycle = "PARTIAL"
    else:
        cycle = "PASS"
    return {
        "schemaVersion": SCHEMA,
        "mode": "SHADOW_ONLY",
        "productionWriteAllowed": False,
        "tradeDate": day,
        "evaluatedThroughKst": f"{day} 0940",
        "sourcePlanGeneratedAt": plan_time,
        "sourceBundleSha": source_hash,
        "planOrigin": origin,
        "degradedMode": degraded,
        "captureRunId": run_id,
        "historyCount": (c40.get("history") or {}).get("count"),
        "evaluationAt0935": at35,
        "delta0935to0940": deltas,
        "perCandidateEvaluation": evaluated,
        "cycleStatus": cycle,
        "externalEvidenceComplete": all_quality if status == "PASS" else None,
        "productionCutoverReviewEligible": cycle == "PASS",
        "evaluationMethod": "FROZEN_STRUCTURED_RULES_SNAPSHOT_ONLY_V1",
        "limitations": [
            "Minute price snapshots do not establish intraminute high/low events.",
            "Prose-only triggers and chase conditions are DATA_FAIL, never guessed.",
            "No intraday news can be independently inferred from price snapshots.",
        ],
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--capture-0935", required=True)
    p.add_argument("--capture-0940", required=True)
    p.add_argument("--trade-date", required=True)
    p.add_argument("--capture-run-id", required=True, type=int)
    p.add_argument("--source-bundle-sha", required=True)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    result = calculate(read(a.capture_0935), read(a.capture_0940), a.trade_date,
                       a.capture_run_id, a.source_bundle_sha)
    target = Path(a.output)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    require(read(target) == result, "localReadBackMismatch")
    print(json.dumps({"tradeDate": a.trade_date, "cycleStatus": result["cycleStatus"],
                      "candidateCount": len(result["perCandidateEvaluation"]),
                      "origin": result["planOrigin"], "productionWriteAllowed": False}))


if __name__ == "__main__":
    main()
