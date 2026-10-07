#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

SCHEMA = "V3_0815_SHADOW_BUNDLE_V1"
ORIGINS = {"MACHINE_CONTINUITY_FALLBACK", "ASSISTANT_DEEP_REVIEW"}
LIVE_STATES = {"ATTACK_PLAN", "PROBE_PLAN"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--trade-date", default=None)
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

    out = {"status": "PASS" if not errors else "FAIL", "errorCount": len(errors), "errors": errors[:100]}
    print(json.dumps(out, ensure_ascii=False))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
