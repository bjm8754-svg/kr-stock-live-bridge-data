from __future__ import annotations

import math
from collections import defaultdict

import numpy as np
import pandas as pd

from .features import pct, rnum


def _level(price, low, high, kind, evidence, strength=1.0, date=None):
    return {
        "price": rnum(price, 2),
        "zoneLow": rnum(low, 2),
        "zoneHigh": rnum(high, 2),
        "kind": kind,
        "evidence": list(evidence),
        "strength": float(strength),
        "date": date,
    }


def discover_event_levels(df, cfg):
    """Strong event-candle levels from observable relative money/volume."""
    if len(df) < 30:
        return []
    lookback = int(cfg.get("eventLookbackSessions", 252))
    sub = df.iloc[-lookback:-1] if len(df) > 1 else df.iloc[0:0]
    min_ret = float(cfg.get("eventMinReturnPct", 8.0))
    min_tvr = float(cfg.get("eventMinTradingValueRatio20", 2.0))
    min_vr = float(cfg.get("eventMinVolumeRatio20", 2.0))
    min_close_loc = float(cfg.get("eventMinCloseLocation", 0.65))
    pad = float(cfg.get("eventLevelPaddingPct", 0.5)) / 100.0
    out = []

    mask = (
        (sub["Close"] > sub["Open"])
        & (sub["DAY_RETURN_PCT"] >= min_ret)
        & (sub["TV_RATIO20_EST"] >= min_tvr)
        & (sub["VOL_RATIO20"] >= min_vr)
        & (sub["CLOSE_LOC"] >= min_close_loc)
    ).fillna(False)

    for idx, row in sub[mask].tail(int(cfg.get("eventMaxLevels", 12))).iterrows():
        close = float(row["Close"])
        open_ = float(row["Open"])
        lo, hi = sorted((open_, close))
        out.append(_level(
            close, close*(1-pad), close*(1+pad),
            "EVENT_CLOSE",
            ["MONEY_EXPANSION", "VOLUME_EXPANSION", "STRONG_CLOSE"],
            strength=3.0,
            date=idx.strftime("%Y%m%d"),
        ))
        out.append(_level(
            (lo+hi)/2.0, lo, hi,
            "EVENT_BODY",
            ["EVENT_OPEN_CLOSE_RANGE"],
            strength=2.0,
            date=idx.strftime("%Y%m%d"),
        ))
    return out


def discover_recent_box(df, cfg):
    """Find one recent time-accepted box without using future bars.

    A box is treated as a range, not a line. The compressed-candle close is the final
    close of the box window; this is kept separate from upper/lower boundaries.
    """
    if len(df) < 25:
        return None
    windows = [int(x) for x in cfg.get("boxWindowCandidates", [20, 30, 40, 60])]
    max_range = float(cfg.get("boxMaxRangePct", 18.0))
    edge_tol = float(cfg.get("boxEdgeTouchTolerancePct", 2.0)) / 100.0
    min_touches = int(cfg.get("boxMinEdgeTouches", 2))
    max_end_lag = int(cfg.get("boxMaxEndLagSessions", 5))

    best = None
    n = len(df)
    for lag in range(1, max_end_lag + 1):
        end = n - lag
        if end <= 0:
            continue
        for w in windows:
            start = end - w
            if start < 0:
                continue
            seg = df.iloc[start:end]
            lo = float(seg["Low"].min())
            hi = float(seg["High"].max())
            if lo <= 0:
                continue
            range_pct = (hi / lo - 1.0) * 100.0
            if range_pct > max_range:
                continue
            upper_touches = int((seg["High"] >= hi*(1-edge_tol)).sum())
            lower_touches = int((seg["Low"] <= lo*(1+edge_tol)).sum())
            if upper_touches < min_touches or lower_touches < min_touches:
                continue

            compressed_close = float(seg["Close"].iloc[-1])
            score_key = (w, upper_touches + lower_touches, -range_pct, -lag)
            candidate = {
                "startDate": seg.index[0].strftime("%Y%m%d"),
                "endDate": seg.index[-1].strftime("%Y%m%d"),
                "sessions": w,
                "endLag": lag,
                "upper": rnum(hi, 2),
                "lower": rnum(lo, 2),
                "boxClose": rnum(compressed_close, 2),
                "rangePct": rnum(range_pct, 2),
                "upperTouches": upper_touches,
                "lowerTouches": lower_touches,
                "_key": score_key,
            }
            if best is None or score_key > best["_key"]:
                best = candidate
    if best:
        best.pop("_key", None)
    return best


def box_levels(box, cfg):
    if not box:
        return []
    pad = float(cfg.get("boxLevelPaddingPct", 0.4)) / 100.0
    out = []
    for price, kind, strength in (
        (box["upper"], "BOX_UPPER", 3.0),
        (box["boxClose"], "BOX_CLOSE", 2.5),
        (box["lower"], "BOX_LOWER", 3.0),
    ):
        p = float(price)
        out.append(_level(
            p, p*(1-pad), p*(1+pad), kind,
            [f"BOX_{box['sessions']}_SESSIONS", "REPEATED_REACTION"],
            strength=strength,
            date=box["endDate"],
        ))
    return out


def discover_trend_bridge(df, cfg):
    """Find latest impulse -> short pause -> same-direction resume bridge."""
    if len(df) < 40:
        return None
    lookback = int(cfg.get("bridgeLookbackSessions", 160))
    impulse_n = int(cfg.get("bridgeImpulseSessions", 5))
    min_impulse = float(cfg.get("bridgeMinImpulsePct", 12.0))
    pause_min = int(cfg.get("bridgePauseMinSessions", 2))
    pause_max = int(cfg.get("bridgePauseMaxSessions", 8))
    pause_range_max = float(cfg.get("bridgePauseMaxRangePct", 8.0))
    resume_n = int(cfg.get("bridgeResumeLookaheadSessions", 10))
    resume_pct = float(cfg.get("bridgeMinResumePct", 5.0))
    start_scan = max(impulse_n, len(df)-lookback)
    latest = None

    # Stop early enough so the resume is fully observable.
    for pause_start in range(start_scan, len(df)-pause_min-resume_n):
        before = float(df["Close"].iloc[pause_start-impulse_n])
        impulse_end = float(df["Close"].iloc[pause_start-1])
        impulse = pct(impulse_end, before)
        if impulse is None or impulse < min_impulse:
            continue

        for plen in range(pause_min, pause_max+1):
            pause_end = pause_start + plen
            if pause_end + resume_n > len(df):
                break
            pause = df.iloc[pause_start:pause_end]
            plo, phi = float(pause["Low"].min()), float(pause["High"].max())
            if plo <= 0:
                continue
            prange = (phi/plo - 1.0)*100.0
            if prange > pause_range_max:
                continue
            bridge_close = float(pause["Close"].iloc[-1])
            after = df.iloc[pause_end:pause_end+resume_n]
            if float(after["Close"].max()) < bridge_close*(1+resume_pct/100.0):
                continue
            latest = {
                "date": pause.index[-1].strftime("%Y%m%d"),
                "close": rnum(bridge_close, 2),
                "zoneLow": rnum(plo, 2),
                "zoneHigh": rnum(phi, 2),
                "pauseSessions": plen,
                "impulsePct": rnum(impulse, 2),
                "pauseRangePct": rnum(prange, 2),
            }
    return latest


def bridge_levels(bridge, cfg):
    if not bridge:
        return []
    return [
        _level(
            bridge["close"], bridge["zoneLow"], bridge["zoneHigh"],
            "TREND_BRIDGE",
            ["IMPULSE", "PAUSE", "SAME_DIRECTION_RESUME"],
            strength=3.0,
            date=bridge["date"],
        )
    ]


def discover_trade_density_levels(df, cfg):
    """Price-volume-time concentration zones.

    This is a generic proxy for prices where meaningful transaction value accumulated
    over time. It does not infer who traded or why.
    """
    if len(df) < 40:
        return []
    lookback = int(cfg.get("densityLookbackSessions", 180))
    bins = int(cfg.get("densityBins", 24))
    top_n = int(cfg.get("densityTopBins", 4))
    min_sessions = int(cfg.get("densityMinSessions", 4))
    sub = df.iloc[-lookback:-1].copy()
    if len(sub) < 20:
        return []
    pmin = float(sub["Low"].min())
    pmax = float(sub["High"].max())
    if pmin <= 0 or pmax <= pmin:
        return []

    edges = np.linspace(pmin, pmax, bins + 1)
    inds = np.digitize(sub["Close"].values, edges) - 1
    out = []
    stats = []
    for bi in range(bins):
        mask = inds == bi
        n = int(mask.sum())
        if n < min_sessions:
            continue
        seg = sub.loc[mask]
        tv = float(seg["TV_EST"].sum())
        if tv <= 0:
            continue
        center = float(np.average(seg["Close"], weights=seg["TV_EST"]))
        stats.append((tv, n, center, float(edges[bi]), float(edges[bi+1])))

    for tv, n, center, lo, hi in sorted(stats, reverse=True)[:top_n]:
        out.append(_level(
            center, lo, hi,
            "TRADE_DENSITY",
            ["TRADING_VALUE_CONCENTRATION", "TIME_ACCEPTANCE", f"SESSIONS_{n}"],
            strength=2.5,
            date=sub.index[-1].strftime("%Y%m%d"),
        ))
    return out


def discover_swing_levels(df, cfg):
    if len(df) < 20:
        return []
    lookback = int(cfg.get("swingLookbackSessions", 180))
    half = int(cfg.get("swingHalfWindow", 3))
    sub = df.iloc[-lookback:-1]
    pad = float(cfg.get("swingLevelPaddingPct", 0.5)) / 100.0
    out = []
    for i in range(half, len(sub)-half):
        h = float(sub["High"].iloc[i])
        l = float(sub["Low"].iloc[i])
        if h >= float(sub["High"].iloc[i-half:i+half+1].max()):
            out.append(_level(h, h*(1-pad), h*(1+pad), "SWING_HIGH", ["LOCAL_REACTION_HIGH"], 1.0, sub.index[i].strftime("%Y%m%d")))
        if l <= float(sub["Low"].iloc[i-half:i+half+1].min()):
            out.append(_level(l, l*(1-pad), l*(1+pad), "SWING_LOW", ["LOCAL_REACTION_LOW"], 1.0, sub.index[i].strftime("%Y%m%d")))
    return out[-int(cfg.get("swingMaxLevels", 20)):]


def merge_levels(levels, cfg):
    """Merge nearby price evidence into zones while preserving provenance."""
    if not levels:
        return []
    tol = float(cfg.get("levelMergeTolerancePct", 1.25)) / 100.0
    xs = sorted([x for x in levels if x.get("price")], key=lambda z: float(z["price"]))
    clusters = []
    for x in xs:
        p = float(x["price"])
        if not clusters:
            clusters.append([x])
            continue
        center = np.average(
            [float(y["price"]) for y in clusters[-1]],
            weights=[max(0.1, float(y.get("strength",1))) for y in clusters[-1]],
        )
        if abs(p/center-1.0) <= tol:
            clusters[-1].append(x)
        else:
            clusters.append([x])

    out = []
    for c in clusters:
        weights = [max(0.1, float(x.get("strength",1))) for x in c]
        center = float(np.average([float(x["price"]) for x in c], weights=weights))
        kinds = sorted(set(x["kind"] for x in c))
        evidence = sorted(set(e for x in c for e in x.get("evidence",[])))
        special_kinds = {
            "EVENT_CLOSE", "EVENT_BODY",
            "BOX_UPPER", "BOX_CLOSE", "BOX_LOWER",
            "TREND_BRIDGE", "TRADE_DENSITY",
        }
        importance = "CORE" if (
            any(k in special_kinds for k in kinds)
            or (len(c) >= int(cfg.get("coreLevelMinEvidenceCount", 3))
                and sum(weights) >= float(cfg.get("coreLevelMinStrength", 3.0)))
        ) else "SUPPORTING"
        out.append({
            "line": rnum(center, 2),
            "zoneLow": rnum(min(float(x["zoneLow"]) for x in c), 2),
            "zoneHigh": rnum(max(float(x["zoneHigh"]) for x in c), 2),
            "kinds": kinds,
            "evidence": evidence,
            "evidenceCount": len(c),
            "strength": rnum(sum(weights), 2),
            "importance": importance,
            "dates": sorted(set(x["date"] for x in c if x.get("date")))[-5:],
        })
    return out


def classify_role(df, level):
    if not level or len(df) < 3:
        return {"state":"NONE","warnings":[]}
    lo, hi = float(level["zoneLow"]), float(level["zoneHigh"])
    cur = df.iloc[-1]
    prev = df.iloc[-2]
    prev2 = df.iloc[-3]
    c = float(cur["Close"])
    p1 = float(prev["Close"])
    p2 = float(prev2["Close"])
    h = float(cur["High"])
    l = float(cur["Low"])
    warnings = []

    decision_relevant = level.get("importance") == "CORE"

    if h > hi and c < lo:
        state = "FAILED_BREAKOUT"
        if decision_relevant:
            warnings.append("FAILED_BREAKOUT")
    elif l < lo and c > hi:
        state = "SPRING_RECLAIM"
    elif lo <= c <= hi:
        state = "DECISION_ZONE"
    elif c > hi:
        if p1 > hi and p2 > hi:
            state = "ACCEPTED_SUPPORT"
        elif p1 <= hi:
            state = "BREAKOUT_PENDING"
        else:
            state = "SUPPORT_CANDIDATE"
    else:
        if p1 < lo and p2 < lo:
            state = "ACCEPTED_RESISTANCE"
        elif p1 >= lo:
            state = "BREAKDOWN_PENDING"
        else:
            state = "RESISTANCE_CANDIDATE"

    if decision_relevant and h > hi and c < hi and "FAILED_BREAKOUT" not in warnings:
        warnings.append("UPPER_REJECTION")
    if decision_relevant and l < lo and c > lo:
        warnings.append("LOWER_RECLAIM")

    return {
        "state": state,
        "warnings": warnings,
        "distancePct": rnum(pct(c, level["line"]), 2),
        "decisionRelevant": decision_relevant,
    }


def attach_roles(df, levels):
    out = []
    for lv in levels:
        x = dict(lv)
        x["role"] = classify_role(df, lv)
        out.append(x)
    return out


def nearest_levels(levels, close):
    below = [x for x in levels if float(x["zoneHigh"]) <= close]
    above = [x for x in levels if float(x["zoneLow"]) >= close]
    below.sort(key=lambda x: float(x["zoneHigh"]), reverse=True)
    above.sort(key=lambda x: float(x["zoneLow"]))
    return {
        "below": below[0] if below else None,
        "above": above[0] if above else None,
    }
