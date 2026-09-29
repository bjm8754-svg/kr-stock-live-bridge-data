from __future__ import annotations

import math

import pandas as pd

from .execution import build_execution_plan, rank_key
from .features import add_indicators, money_context, rnum, rsi_context
from .levels import (
    attach_roles,
    box_levels,
    bridge_levels,
    discover_event_levels,
    discover_recent_box,
    discover_trade_density_levels,
    discover_swing_levels,
    discover_trend_bridge,
    merge_levels,
)
from .setups import confirmation_context, detect_setups
from .review import build_review_context, select_deep_review_queue


def _trim_levels(levels, close, cfg, pinned_prices=None):
    """Keep the output compact without changing detection.

    Preserve nearest levels on each side plus high-evidence zones and all special
    box/bridge/event zones. Candidate logic already ran on the full level set.
    """
    max_out = int(cfg.get("maxOutputLevels", 16))
    if len(levels) <= max_out:
        return levels

    def distance(x):
        return abs(float(x["line"]) / close - 1.0)

    special = [
        x for x in levels
        if any(k.startswith(("BOX_", "TREND_BRIDGE", "EVENT_", "TRADE_DENSITY")) for k in (x.get("kinds") or []))
    ]
    evidence = sorted(levels, key=lambda x: (int(x.get("evidenceCount") or 0), float(x.get("strength") or 0)), reverse=True)
    near = sorted(levels, key=distance)

    pins = [float(x) for x in (pinned_prices or []) if x is not None]
    pinned = []
    for lv in levels:
        line = float(lv["line"])
        if any(abs(line-p) <= max(0.03, abs(p)*0.0005) for p in pins):
            pinned.append(lv)

    keep, seen = [], set()
    for group in (pinned, special, near[:8], evidence[:8]):
        for x in group:
            key = (x.get("zoneLow"), x.get("zoneHigh"), tuple(x.get("kinds") or []))
            if key in seen:
                continue
            seen.add(key)
            keep.append(x)
            if len(keep) >= max_out:
                return sorted(keep, key=lambda z: float(z["line"]))
    return sorted(keep, key=lambda z: float(z["line"]))


def analyze_frame(meta, raw_df, cfg):
    need = ["Open", "High", "Low", "Close", "Volume"]
    if raw_df is None:
        return {"status": "NO_DATA", **meta}
    if any(c not in raw_df.columns for c in need):
        return {"status": "BAD_SCHEMA", "columns": list(raw_df.columns), **meta}

    df = raw_df[need].dropna().copy()
    if len(df) < int(cfg.get("minHistoryRows", 260)):
        return {"status": "INSUFFICIENT_HISTORY", "rows": len(df), **meta}

    df = add_indicators(df, cfg)
    cur = df.iloc[-1]
    close = float(cur["Close"])

    box = discover_recent_box(df, cfg)
    bridge = discover_trend_bridge(df, cfg)

    raw_levels = []
    raw_levels.extend(discover_event_levels(df, cfg))
    raw_levels.extend(discover_trade_density_levels(df, cfg))
    raw_levels.extend(box_levels(box, cfg))
    raw_levels.extend(bridge_levels(bridge, cfg))
    raw_levels.extend(discover_swing_levels(df, cfg))

    merged = merge_levels(raw_levels, cfg)
    roles = attach_roles(df, merged)

    rsi = rsi_context(df, cfg)
    money = money_context(df, meta.get("amount"))
    setups = detect_setups(df, box, bridge, roles, cfg)
    confirmation = confirmation_context(df, money, rsi, setups.get("primary"), cfg)
    execution = build_execution_plan(df, roles, setups, confirmation, money, cfg)

    review = build_review_context(
        df,
        {"box": box, "trendBridge": bridge, "levels": roles},
        setups,
        confirmation,
        execution,
        cfg,
    )

    ma = {}
    for p in cfg.get("maPeriods", [20, 60, 120, 240, 600]):
        v = cur.get(f"MA{int(p)}")
        ma[str(int(p))] = rnum(v, 2) if pd.notna(v) else None

    warnings = list(execution.get("warnings") or [])
    data_warnings = []
    if not math.isfinite(close) or close <= 0:
        data_warnings.append("INVALID_CLOSE")
    if money.get("quality") == "ESTIMATED":
        data_warnings.append("CURRENT_TRADING_VALUE_ESTIMATED")

    output_levels = _trim_levels(
        roles,
        close,
        cfg,
        pinned_prices=[
            execution.get("nearestAcceptedSupport"),
            execution.get("nextResistance"),
            execution.get("entryReference"),
        ],
    )

    return {
        "status": "OK",
        "schemaVersion": "MARKET_STRUCTURE_V3",
        "methodologyVersion": cfg["methodologyVersion"],
        "code": meta["code"],
        "name": meta["name"],
        "market": meta.get("market"),
        "tradeDate": df.index[-1].strftime("%Y%m%d"),
        "price": {
            "open": rnum(cur["Open"], 2),
            "high": rnum(cur["High"], 2),
            "low": rnum(cur["Low"], 2),
            "close": rnum(cur["Close"], 2),
            "closeLocation": rnum(cur.get("CLOSE_LOC"), 3),
            "atrPct": rnum(cur.get("ATR_PCT"), 2),
        },
        "ma": ma,
        "money": money,
        "structure": {
            "box": box,
            "trendBridge": bridge,
            "levels": output_levels,
        },
        "setups": setups,
        "confirmation": confirmation,
        "execution": execution,
        "review": review,
        "warnings": warnings,
        "dataWarnings": data_warnings,
        "rows": len(df),
    }


def is_discovery_candidate(row, cfg):
    if row.get("status") != "OK":
        return False
    primary = ((row.get("setups") or {}).get("primary"))
    if not primary:
        return False
    avg20 = float((row.get("money") or {}).get("avg20TradingValueEstimated") or 0)
    if avg20 < float(cfg.get("minAvg20TradingValueKrw", 10_000_000_000)):
        return False
    return (row.get("execution") or {}).get("readiness") != "REJECT"


def build_output(rows, errors, cfg, generated_at_kst):
    ok = [x for x in rows if x.get("status") == "OK"]
    dates = {}
    for x in ok:
        td = x.get("tradeDate")
        dates[td] = dates.get(td, 0) + 1
    trade_date = max(dates, key=dates.get) if dates else None
    current = [x for x in ok if x.get("tradeDate") == trade_date]
    candidates = [x for x in current if is_discovery_candidate(x, cfg)]
    candidates.sort(key=rank_key, reverse=True)

    executable = [x for x in candidates if (x.get("execution") or {}).get("readiness") == "EXECUTABLE"]
    watch = [x for x in candidates if (x.get("execution") or {}).get("readiness") == "WATCH_TRIGGER"]
    radar = [x for x in candidates if (x.get("execution") or {}).get("readiness") == "RADAR"]

    deep_review = select_deep_review_queue(candidates, cfg)

    warning_rows = [
        x for x in current
        if any(w in (x.get("warnings") or []) for w in ("FAILED_BREAKOUT", "SUPPORT_BREAK"))
    ]
    warning_rows.sort(key=rank_key, reverse=True)

    candidate_ratio = len(candidates) / max(1, len(current))
    error_ratio = len(errors) / max(1, len(rows) + len(errors))
    current_ratio = len(current) / max(1, len(ok))
    status = "PASS"
    if (
        error_ratio > float(cfg.get("maxErrorRatioForPass", 0.01))
        or current_ratio < float(cfg.get("minCurrentTradeDateRatioForPass", 0.99))
        or candidate_ratio > float(cfg.get("maxCandidateRatioForPass", 0.30))
    ):
        status = "PARTIAL"

    def compact(x, include_review_trace=False):
        review = x.get("review") or {}
        review_out = {
            "assistantReviewRequired": review.get("assistantReviewRequired"),
            "machineScope": review.get("machineScope"),
            "machineReadiness": review.get("machineReadiness"),
            "reviewTier": review.get("reviewTier"),
            "hypothesis": review.get("hypothesis"),
            "coreLevelCount": review.get("coreLevelCount"),
            "questions": review.get("questions"),
        }
        if include_review_trace:
            review_out["traceSchema"] = review.get("traceSchema")
            review_out["chartTrace"] = review.get("chartTrace")

        return {
            "code": x["code"],
            "name": x["name"],
            "market": x.get("market"),
            "tradeDate": x.get("tradeDate"),
            "price": x.get("price"),
            "money": x.get("money"),
            "setups": x.get("setups"),
            "confirmation": x.get("confirmation"),
            "execution": x.get("execution"),
            "review": review_out,
            "structure": x.get("structure"),
            "ma": x.get("ma"),
            "warnings": x.get("warnings"),
        }

    max_out = int(cfg.get("maxCandidatesPerSection", 75))
    return {
        "status": status,
        "schemaVersion": "MARKET_STRUCTURE_V3",
        "methodologyVersion": cfg["methodologyVersion"],
        "generatedAtKst": generated_at_kst,
        "tradeDate": trade_date,
        "philosophy": {
            "core": "price-volume-time -> important levels -> role state -> close acceptance/rejection -> setup family -> confirmation -> execution",
            "aggregateScore": False,
            "hiddenIntentInference": False,
            "rsiRole": "confirmation/warning only",
            "legacyYbmRole": "not a governing architecture; reusable ideas may survive only as generic structure evidence",
            "machineRole": "universe compression and evidence packaging only; final chart judgement requires assistant deep review",
        },
        "coverage": {
            "universeProcessed": len(rows) + len(errors),
            "ok": len(ok),
            "currentTradeDate": len(current),
            "errors": len(errors),
            "errorRatio": round(error_ratio, 4),
            "currentTradeDateRatio": round(current_ratio, 4),
            "candidateRatio": round(candidate_ratio, 4),
            "tradeDateCounts": dates,
        },
        "counts": {
            "candidates": len(candidates),
            "executable": len(executable),
            "watchTrigger": len(watch),
            "radar": len(radar),
            "structureWarnings": len(warning_rows),
            "deepReviewQueue": len(deep_review),
        },
        "executable": [compact(x) for x in executable[:max_out]],
        "watchTrigger": [compact(x) for x in watch[:max_out]],
        "radar": [compact(x) for x in radar[:max_out]],
        "deepReviewQueue": [compact(x, include_review_trace=True) for x in deep_review],
        "structureWarnings": [compact(x) for x in warning_rows[:max_out]],
        "sourceBoundary": {
            "studyDerived": [
                "important prices arise from observable price/volume/time history",
                "support/resistance is a role, not a permanent label",
                "close acceptance/rejection is more important than intraday penetration alone",
                "box upper/close/lower must remain distinct",
                "spring is a failed support-break attempt followed by reclaim, not an automatic rally guarantee",
                "trend-bridge levels require impulse-pause-resume context; a small candle alone is not a level",
                "RSI is secondary confirmation and divergence evidence; 70/30 are not automatic triggers",
            ],
            "implementationInference": [
                "all numeric windows/tolerances",
                "box compactness and touch thresholds",
                "event candle relative money/volume thresholds",
                "trend-bridge impulse/pause/resume thresholds",
                "continuation compression/high-pressure thresholds",
                "categorical readiness mapping and structural R/R threshold",
            ],
        },
        "errors": errors[:100],
    }
