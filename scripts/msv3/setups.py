from __future__ import annotations

import pandas as pd

from .features import pct, rnum


SETUP_MATURITY = {
    "SPRING_CONFIRMED": 100,
    "BOX_RETEST": 95,
    "HIGH_RETEST": 92,
    "TREND_BRIDGE_RETEST": 90,
    "BOX_BREAKOUT_ACCEPTED": 88,
    "HIGH_BREAKOUT": 86,
    "LEVEL_RETEST": 84,
    "BREAKOUT_PRESSURE": 75,
    "BOX_BREAKOUT_PENDING": 72,
    "SPRING_RECLAIM_PENDING": 70,
    "BASE_BREAKOUT": 68,
    "BASE_RECOVERY": 55,
    "HIGH_BASE": 52,
    "BOX_BUILDING": 45,
    "TREND_BRIDGE_ACTIVE": 40,
}


def _setup(family, state, evidence, trigger=None, invalidation=None, source=None):
    return {
        "family": family,
        "state": state,
        "evidence": list(evidence),
        "triggerLevel": rnum(trigger, 2),
        "invalidationLevel": rnum(invalidation, 2),
        "source": source,
        "maturity": SETUP_MATURITY.get(state, 0),
    }


def detect_box_setup(df, box, cfg):
    if not box or len(df) < 3:
        return None
    cur, prev = df.iloc[-1], df.iloc[-2]
    close = float(cur["Close"])
    upper, lower, box_close = float(box["upper"]), float(box["lower"]), float(box["boxClose"])
    retest_tol = float(cfg.get("boxRetestTolerancePct", 2.0)) / 100.0

    # Spring: support failure attempt followed by close reclaim. Confirmation asks the
    # next bar to preserve the reclaim rather than assuming one wick guarantees reversal.
    if float(cur["Low"]) < lower and close > lower:
        return _setup(
            "SPRING",
            "SPRING_RECLAIM_PENDING",
            ["BOX_LOWER_UNDERSHOOT", "CLOSE_RECLAIM"],
            trigger=lower,
            invalidation=float(cur["Low"]),
            source=box["endDate"],
        )
    if float(prev["Low"]) < lower and float(prev["Close"]) > lower and close > lower:
        return _setup(
            "SPRING",
            "SPRING_CONFIRMED",
            ["PRIOR_LOWER_UNDERSHOOT", "PRIOR_CLOSE_RECLAIM", "NEXT_CLOSE_HOLD"],
            trigger=lower,
            invalidation=float(prev["Low"]),
            source=box["endDate"],
        )

    if close > upper:
        if (
            float(prev["Close"]) > upper
            and float(cur["Low"]) <= upper*(1+retest_tol)
            and close >= upper
        ):
            return _setup(
                "BOX_BREAKOUT",
                "BOX_RETEST",
                ["BOX_CLOSE_BREAKOUT", "ROLE_REVERSAL_RETEST", "RETEST_CLOSE_HOLD"],
                trigger=upper,
                invalidation=box_close,
                source=box["endDate"],
            )
        if float(prev["Close"]) > upper:
            return _setup(
                "BOX_BREAKOUT",
                "BOX_BREAKOUT_ACCEPTED",
                ["MULTI_CLOSE_ABOVE_BOX", "BOX_RESISTANCE_CLEARED"],
                trigger=upper,
                invalidation=box_close,
                source=box["endDate"],
            )
        return _setup(
            "BOX_BREAKOUT",
            "BOX_BREAKOUT_PENDING",
            ["FIRST_CLOSE_ABOVE_BOX"],
            trigger=upper,
            invalidation=box_close,
            source=box["endDate"],
        )

    if lower <= close <= upper:
        return _setup(
            "BOX",
            "BOX_BUILDING",
            ["TIME_ACCEPTANCE", "REPEATED_UPPER_REACTION", "REPEATED_LOWER_REACTION"],
            trigger=upper,
            invalidation=lower,
            source=box["endDate"],
        )
    return None


def detect_high_trend(df, cfg):
    if len(df) < 130:
        return None
    cur = df.iloc[-1]
    for k in ("MA20", "MA60", "MA120"):
        if pd.isna(cur.get(k)):
            return None

    close = float(cur["Close"])
    ma20, ma60, ma120 = float(cur["MA20"]), float(cur["MA60"]), float(cur["MA120"])
    if not (close >= ma20 >= ma60 >= ma120):
        return None

    high_lb = int(cfg.get("continuationHighLookbackSessions", 120))
    base_n = int(cfg.get("continuationBaseLookbackSessions", 20))
    prior = df.iloc[-high_lb-1:-1]
    recent = df.iloc[-base_n:]
    prior_high = float(prior["High"].max())
    near_pct = float(cfg.get("continuationNearHighPct", 8.0))
    if close < prior_high*(1-near_pct/100.0):
        return None

    rlo, rhi = float(recent["Low"].min()), float(recent["High"].max())
    if rlo <= 0:
        return None
    range_pct = (rhi/rlo-1.0)*100.0
    compressed = range_pct <= float(cfg.get("continuationMaxBaseRangePct", 14.0))
    edge = max(3, min(5, base_n//4))
    rising_lows = float(recent["Low"].iloc[-edge:].min()) >= float(recent["Low"].iloc[:edge].min())
    touch_tol = float(cfg.get("continuationHighPressureTolerancePct", 4.0))/100.0
    touches = int((recent["High"] >= prior_high*(1-touch_tol)).sum())
    min_touches = int(cfg.get("continuationMinHighPressureTouches", 3))

    money = float(cur.get("TV_RATIO20_EST") or 0)
    vol = float(cur.get("VOL_RATIO20") or 0)
    breakout_money = (
        money >= float(cfg.get("continuationBreakoutTurnoverRatio20", 1.3))
        or vol >= float(cfg.get("continuationBreakoutVolumeRatio20", 1.3))
    )

    if close > prior_high and breakout_money:
        # If the previous close was already above the old high and today's low revisits it,
        # treat it as a high-level retest instead of another breakout event.
        prev = df.iloc[-2]
        if float(prev["Close"]) > prior_high and float(cur["Low"]) <= prior_high*(1+touch_tol) and close >= prior_high:
            state = "HIGH_RETEST"
        else:
            state = "HIGH_BREAKOUT"
    elif compressed and rising_lows and touches >= min_touches:
        state = "BREAKOUT_PRESSURE"
    elif compressed:
        state = "HIGH_BASE"
    else:
        return None

    return _setup(
        "HIGH_TREND_CONTINUATION",
        state,
        [
            "MA20_GE_MA60_GE_MA120",
            "HIGH_LEVEL_ACCEPTANCE",
            "COMPRESSED_RANGE" if compressed else "RANGE_NOT_COMPRESSED",
            "RISING_LOWS" if rising_lows else "LOWS_NOT_RISING",
            f"UPPER_TESTS_{touches}",
        ],
        trigger=prior_high,
        invalidation=float(recent["Low"].min()),
        source=f"{high_lb}D_HIGH",
    )


def detect_base_reversal(df, cfg):
    if len(df) < 260:
        return None
    cur = df.iloc[-1]
    lookback = int(cfg.get("baseReversalLookbackSessions", 252))
    base_n = int(cfg.get("baseReversalBaseSessions", 60))
    hist = df.iloc[-lookback:]
    prior_high = float(hist["High"].max())
    low = float(hist["Low"].min())
    if prior_high <= 0:
        return None
    decline = (1.0-low/prior_high)*100.0
    if decline < float(cfg.get("baseReversalMinPriorDeclinePct", 25.0)):
        return None

    base = df.iloc[-base_n:]
    blo, bhi = float(base["Low"].min()), float(base["High"].max())
    if blo <= 0:
        return None
    base_range = (bhi/blo-1.0)*100.0
    if base_range > float(cfg.get("baseReversalMaxBaseRangePct", 35.0)):
        return None

    close = float(cur["Close"])
    ma120 = cur.get("MA120")
    ma240 = cur.get("MA240")
    above120 = pd.notna(ma120) and close > float(ma120)
    above240 = pd.notna(ma240) and close > float(ma240)
    if not above120:
        return None

    prior_base_high = float(df["High"].iloc[-base_n:-1].max())
    if close > prior_base_high:
        state = "BASE_BREAKOUT"
    elif above240 or close >= prior_base_high*0.95:
        state = "BASE_RECOVERY"
    else:
        return None

    return _setup(
        "BASE_REVERSAL",
        state,
        [
            f"PRIOR_DECLINE_{rnum(decline,1)}PCT",
            f"BASE_RANGE_{rnum(base_range,1)}PCT",
            "ABOVE_MA120",
            "ABOVE_MA240" if above240 else "BELOW_MA240",
        ],
        trigger=prior_base_high,
        invalidation=blo,
        source=f"{base_n}D_BASE",
    )


def detect_bridge_setup(df, bridge, levels, cfg):
    if not bridge:
        return None
    close = float(df["Close"].iloc[-1])
    line = float(bridge["close"])
    zone_low, zone_high = float(bridge["zoneLow"]), float(bridge["zoneHigh"])
    tol = float(cfg.get("bridgeRetestTolerancePct", 2.0))/100.0

    # Find the merged level carrying TREND_BRIDGE evidence, if present.
    role = None
    for lv in levels:
        if "TREND_BRIDGE" in (lv.get("kinds") or []):
            role = (lv.get("role") or {}).get("state")
            break

    if close >= line and float(df["Low"].iloc[-1]) <= zone_high*(1+tol):
        if role in ("ACCEPTED_SUPPORT", "SUPPORT_CANDIDATE", "SPRING_RECLAIM", "DECISION_ZONE"):
            return _setup(
                "TREND_BRIDGE",
                "TREND_BRIDGE_RETEST",
                ["PRIOR_IMPULSE", "PAUSE", "RESUME", f"ROLE_{role}"],
                trigger=line,
                invalidation=zone_low,
                source=bridge["date"],
            )

    if close > zone_high:
        return _setup(
            "TREND_BRIDGE",
            "TREND_BRIDGE_ACTIVE",
            ["PRIOR_IMPULSE", "PAUSE", "RESUME"],
            trigger=line,
            invalidation=zone_low,
            source=bridge["date"],
        )
    return None


def detect_level_retest(df, levels, cfg):
    """Generic role-reversal retest for strong multi-evidence levels."""
    close = float(df["Close"].iloc[-1])
    low = float(df["Low"].iloc[-1])
    tol = float(cfg.get("levelRetestTolerancePct", 2.0))/100.0
    candidates = []
    for lv in levels:
        role = (lv.get("role") or {}).get("state")
        if role not in ("ACCEPTED_SUPPORT", "SUPPORT_CANDIDATE"):
            continue
        if int(lv.get("evidenceCount") or 0) < int(cfg.get("levelRetestMinEvidenceCount", 2)):
            continue
        line = float(lv["line"])
        if close >= line and low <= float(lv["zoneHigh"])*(1+tol):
            candidates.append(lv)
    if not candidates:
        return None
    lv = min(candidates, key=lambda z: abs(close/float(z["line"])-1.0))
    return _setup(
        "ROLE_REVERSAL",
        "LEVEL_RETEST",
        ["MULTI_EVIDENCE_LEVEL", f"ROLE_{lv['role']['state']}", "RETEST_CLOSE_HOLD"],
        trigger=float(lv["line"]),
        invalidation=float(lv["zoneLow"]),
        source="|".join(lv.get("kinds") or []),
    )


def detect_setups(df, box, bridge, levels, cfg):
    setups = []
    for fn, args in (
        (detect_box_setup, (df, box, cfg)),
        (detect_high_trend, (df, cfg)),
        (detect_base_reversal, (df, cfg)),
        (detect_bridge_setup, (df, bridge, levels, cfg)),
        (detect_level_retest, (df, levels, cfg)),
    ):
        x = fn(*args)
        if x:
            setups.append(x)

    setups.sort(key=lambda x: x.get("maturity",0), reverse=True)
    return {
        "primary": setups[0] if setups else None,
        "all": setups,
    }


def confirmation_context(df, money, rsi, primary_setup, cfg):
    tvr = float(money.get("tradingValueRatio20Estimated") or 0)
    vr = float(money.get("volumeRatio20") or 0)
    if tvr >= 2.0 and vr >= 2.0:
        money_state = "EXPANDING_STRONG"
    elif tvr >= 1.3 or vr >= 1.3:
        money_state = "EXPANDING"
    elif tvr <= 0.8 and vr <= 0.9:
        money_state = "DRY"
    else:
        money_state = "NORMAL"

    # Pullback supply is descriptive, not a trigger by itself.
    pullback_state = "UNAVAILABLE"
    if len(df) >= 6:
        recent = df.iloc[-5:]
        prev = df.iloc[-10:-5] if len(df) >= 10 else None
        if prev is not None and len(prev):
            rtv = float(recent["TV_EST"].mean())
            ptv = float(prev["TV_EST"].mean())
            if ptv > 0:
                ratio = rtv/ptv
                pullback_state = "CONTRACTING" if ratio <= float(cfg.get("pullbackMoneyContractionRatio",0.8)) else "NOT_CONTRACTING"

    warnings = []
    if rsi.get("divergence") == "BEARISH_DIVERGENCE":
        warnings.append("RSI_BEARISH_DIVERGENCE")
    if primary_setup and primary_setup["state"] in ("BREAKOUT_PRESSURE","HIGH_BREAKOUT","BOX_BREAKOUT_PENDING") and rsi.get("direction") == "WEAKENING":
        warnings.append("RSI_MOMENTUM_WEAKENING")

    return {
        "moneyState": money_state,
        "pullbackMoneyState": pullback_state,
        "rsi": rsi,
        "warnings": warnings,
    }
