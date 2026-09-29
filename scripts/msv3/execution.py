from __future__ import annotations

from .features import pct, rnum
from .taxonomy import MATURE_EXECUTION_STATES, PENDING_STATES, READINESS_ORDER, setup_priority


def _valid_below(v, close):
    try:
        v = float(v)
    except Exception:
        return False
    return 0 < v < close


def build_execution_plan(df, levels, setup_bundle, confirmation, money, cfg):
    close = float(df["Close"].iloc[-1])
    primary = (setup_bundle or {}).get("primary")
    setup_state = (primary or {}).get("state")
    family = (primary or {}).get("family")

    entry_reference = None
    try:
        raw_entry = (primary or {}).get("triggerLevel")
        if raw_entry is not None and float(raw_entry) > 0:
            entry_reference = float(raw_entry)
    except Exception:
        entry_reference = None

    accepted_supports = []
    overhead = []
    for lv in levels or []:
        if lv.get("importance") != "CORE":
            continue
        role = (lv.get("role") or {}).get("state")
        if role in ("ACCEPTED_SUPPORT", "SPRING_RECLAIM"):
            if float(lv["zoneLow"]) < close:
                accepted_supports.append(lv)
        if float(lv["zoneLow"]) > close and role in (
            "RESISTANCE_CANDIDATE",
            "ACCEPTED_RESISTANCE",
            "DECISION_ZONE",
        ):
            overhead.append(lv)

    accepted_supports.sort(key=lambda x: float(x["zoneHigh"]), reverse=True)
    overhead.sort(key=lambda x: float(x["zoneLow"]))

    nearest_support = accepted_supports[0] if accepted_supports else None
    next_resistance = overhead[0] if overhead else None

    invalidation = None
    invalidation_source = None
    if primary and _valid_below(primary.get("invalidationLevel"), close):
        invalidation = float(primary["invalidationLevel"])
        invalidation_source = f"SETUP_{family}_{setup_state}"
    elif nearest_support and _valid_below(nearest_support.get("zoneLow"), close):
        invalidation = float(nearest_support["zoneLow"])
        invalidation_source = "ACCEPTED_STRUCTURAL_LEVEL"

    reward_target = float(next_resistance["zoneLow"]) if next_resistance else None

    # Structural risk/reward must use the planned entry reference, not today's close.
    # Current-vs-entry distance is preserved separately so assistant review can judge
    # whether a valid structure has already become a chase.
    risk_reference = entry_reference if entry_reference is not None else close
    current_vs_entry_pct = pct(close, entry_reference) if entry_reference is not None else None
    valid_plan_invalidation = (
        invalidation is not None
        and risk_reference is not None
        and float(invalidation) < float(risk_reference)
    )
    risk_pct = -pct(invalidation, risk_reference) if valid_plan_invalidation else None
    reward_pct = (
        pct(reward_target, risk_reference)
        if reward_target is not None and risk_reference is not None and reward_target > risk_reference
        else None
    )
    rr = None
    if risk_pct is not None and reward_pct is not None and risk_pct > 0 and reward_pct > 0:
        rr = reward_pct / risk_pct

    warnings = list(confirmation.get("warnings") or [])
    for lv in levels or []:
        warnings.extend((lv.get("role") or {}).get("warnings") or [])
    warnings = sorted(set(warnings))

    avg20 = float(money.get("avg20TradingValueEstimated") or 0)
    liquid = avg20 >= float(cfg.get("minAvg20TradingValueKrw", 10_000_000_000))
    hard_warning = any(x in warnings for x in ("FAILED_BREAKOUT", "SUPPORT_BREAK"))

    if family in ("SPRING", "TREND_BRIDGE", "ROLE_REVERSAL") or setup_state in ("BOX_RETEST", "HIGH_RETEST"):
        mode = "PREPLANNED_LEVEL_MODE"
    else:
        mode = "CONFIRMATION_MODE"

    readiness = "RADAR"
    reason = "STRUCTURE_NOT_MATURE"
    if not primary:
        readiness = "REJECT"
        reason = "NO_SETUP"
    elif hard_warning:
        readiness = "REJECT"
        reason = "STRUCTURE_FAILURE_WARNING"
    elif not liquid:
        readiness = "RADAR"
        reason = "INSUFFICIENT_NORMAL_LIQUIDITY"
    elif setup_state in MATURE_EXECUTION_STATES:
        if not valid_plan_invalidation:
            readiness = "WATCH_TRIGGER"
            reason = "MATURE_SETUP_WITHOUT_VALID_INVALIDATION"
        elif rr is not None and rr < float(cfg.get("minExecutableStructuralRR", 1.15)):
            readiness = "RADAR"
            reason = "STRUCTURAL_RR_TOO_LOW"
        else:
            readiness = "EXECUTABLE"
            reason = "MATURE_STRUCTURE_WITH_VALID_INVALIDATION"
    elif setup_state in PENDING_STATES:
        readiness = "WATCH_TRIGGER"
        reason = "PENDING_CONFIRMATION_OR_RETEST"
    else:
        readiness = "RADAR"
        reason = "EARLY_STRUCTURE"

    # RSI stays descriptive. It never overrides a valid price-structure execution state.
    return {
        "readiness": readiness,
        "reason": reason,
        "mode": mode,
        "evaluationReference": rnum(close, 2),
        "entryReference": rnum(entry_reference, 2),
        "currentVsEntryPct": rnum(current_vs_entry_pct, 2),
        "invalidation": rnum(invalidation, 2),
        "invalidationSource": invalidation_source,
        "nearestAcceptedSupport": rnum((nearest_support or {}).get("line"), 2),
        "nextResistance": rnum(reward_target, 2),
        "riskPct": rnum(risk_pct, 2),
        "rewardPct": rnum(reward_pct, 2),
        "structuralRR": rnum(rr, 2),
        "warnings": warnings,
    }


def rank_key(row):
    """Deterministic categorical ranking without an aggregate score."""
    primary = ((row.get("setups") or {}).get("primary") or {})
    state_priority = setup_priority(primary.get("state"))
    money = row.get("money") or {}
    avg20 = float(money.get("avg20TradingValueEstimated") or 0)
    rr = ((row.get("execution") or {}).get("structuralRR"))
    rr = float(rr) if rr is not None else -1.0
    return (
        READINESS_ORDER.get((row.get("execution") or {}).get("readiness"), 0),
        state_priority,
        rr,
        avg20,
    )
