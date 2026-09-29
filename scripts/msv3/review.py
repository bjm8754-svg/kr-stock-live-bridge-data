from __future__ import annotations

import pandas as pd

from .features import rnum
from .execution import rank_key


REVIEW_TIER_ORDER = {"NOW": 3, "SOON": 2, "BACKGROUND": 1}


def _daily_trace(df, cfg):
    n = int(cfg.get("reviewDailyTraceSessions", 120))
    sub = df.iloc[-n:]
    out = []
    for idx, row in sub.iterrows():
        out.append([
            idx.strftime("%Y%m%d"),
            rnum(row["Open"], 2),
            rnum(row["High"], 2),
            rnum(row["Low"], 2),
            rnum(row["Close"], 2),
            rnum(row.get("VOL_RATIO20"), 2),
            rnum(row.get("TV_RATIO20_EST"), 2),
            rnum(row.get("RSI"), 2),
        ])
    return out


def _higher_timeframe_trace(df, rule, periods, ratio_window):
    if len(df) < 2:
        return []
    base = df[["Open","High","Low","Close","Volume","TV_EST"]].copy()
    bars = base.resample(rule).agg({
        "Open":"first",
        "High":"max",
        "Low":"min",
        "Close":"last",
        "Volume":"sum",
        "TV_EST":"sum",
    }).dropna()
    if bars.empty:
        return []

    prior_vol = bars["Volume"].shift(1).rolling(ratio_window, min_periods=max(3, ratio_window//3)).mean()
    prior_tv = bars["TV_EST"].shift(1).rolling(ratio_window, min_periods=max(3, ratio_window//3)).mean()
    bars["VOL_RATIO"] = bars["Volume"] / prior_vol
    bars["TV_RATIO"] = bars["TV_EST"] / prior_tv
    bars = bars.iloc[-int(periods):]

    out = []
    for idx, row in bars.iterrows():
        out.append([
            idx.strftime("%Y%m%d"),
            rnum(row["Open"], 2),
            rnum(row["High"], 2),
            rnum(row["Low"], 2),
            rnum(row["Close"], 2),
            rnum(row.get("VOL_RATIO"), 2),
            rnum(row.get("TV_RATIO"), 2),
        ])
    return out


def _chart_trace(df, cfg):
    """Multi-timeframe evidence for actual assistant chart reading.

    Daily detail supports entry-context reading; weekly/monthly traces preserve the
    larger structure so the assistant does not overfit to a 2-4 month crop.
    """
    return {
        "dailySchema": ["date","open","high","low","close","volumeRatio20","tradingValueRatio20","rsi"],
        "daily": _daily_trace(df, cfg),
        "weeklySchema": ["date","open","high","low","close","volumeRatio","tradingValueRatio"],
        "weekly": _higher_timeframe_trace(
            df, "W-FRI", int(cfg.get("reviewWeeklyTracePeriods", 156)), 20
        ),
        "monthlySchema": ["date","open","high","low","close","volumeRatio","tradingValueRatio"],
        "monthly": _higher_timeframe_trace(
            df, "ME", int(cfg.get("reviewMonthlyTracePeriods", 72)), 12
        ),
    }

def review_tier(row):
    execution = row.get("execution") or {}
    readiness = execution.get("readiness")
    primary = ((row.get("setups") or {}).get("primary") or {})
    state = primary.get("state")

    if readiness == "EXECUTABLE" or state in {
        "BOX_RETEST", "HIGH_RETEST", "TREND_BRIDGE_RETEST", "LEVEL_RETEST"
    }:
        return "NOW"
    if readiness == "WATCH_TRIGGER" or state in {
        "BREAKOUT_PRESSURE", "HIGH_BREAKOUT", "BOX_BREAKOUT_PENDING",
        "SPRING_RECLAIM_PENDING", "SPRING_CONFIRMED", "BASE_BREAKOUT",
    }:
        return "SOON"
    return "BACKGROUND"


def build_review_context(df, structure, setups, confirmation, execution, cfg):
    primary = (setups or {}).get("primary") or {}
    core_levels = [
        lv for lv in (structure.get("levels") or [])
        if lv.get("importance") == "CORE"
    ]

    return {
        "assistantReviewRequired": True,
        "machineScope": "PREFILTER_AND_EVIDENCE_ONLY",
        "machineReadiness": execution.get("readiness"),
        "reviewTier": review_tier({
            "execution": execution,
            "setups": setups,
        }),
        "hypothesis": {
            "family": primary.get("family"),
            "state": primary.get("state"),
            "evidence": primary.get("evidence") or [],
        },
        "coreLevelCount": len(core_levels),
        "questions": [
            "Is the machine-identified important price genuinely meaningful in the full chart context?",
            "Is the detected setup a real structure or only a threshold-shaped approximation?",
            "Is current price located where upside/downside asymmetry is attractive rather than chased?",
            "Do close acceptance/rejection, volume and time support the same interpretation?",
            "Does a higher-level chart context invalidate or downgrade the machine hypothesis?",
        ],
        "chartTrace": _chart_trace(df, cfg),
    }


def select_deep_review_queue(candidates, cfg):
    """Select a diverse review queue without an aggregate quality score.

    The machine only compresses the universe. Final chart judgement is deferred to the
    assistant review layer. Family caps prevent one easily-detected pattern from
    monopolizing the queue.
    """
    limit = int(cfg.get("maxDeepReviewCandidates", 36))
    family_cap = int(cfg.get("maxDeepReviewPerFamily", 10))

    buckets = {"NOW": [], "SOON": [], "BACKGROUND": []}
    for row in candidates:
        buckets.setdefault(review_tier(row), []).append(row)

    for tier in buckets:
        buckets[tier].sort(key=rank_key, reverse=True)

    selected = []
    family_counts = {}
    seen = set()

    for tier in ("NOW", "SOON", "BACKGROUND"):
        pool = buckets.get(tier) or []
        while pool and len(selected) < limit:
            progressed = False
            families = []
            for row in pool:
                family = (((row.get("setups") or {}).get("primary") or {}).get("family") or "UNCLASSIFIED")
                if family not in families:
                    families.append(family)
            for family in families:
                if family_counts.get(family, 0) >= family_cap:
                    continue
                pick = next((
                    row for row in pool
                    if (((row.get("setups") or {}).get("primary") or {}).get("family") or "UNCLASSIFIED") == family
                    and row.get("code") not in seen
                ), None)
                if pick is None:
                    continue
                selected.append(pick)
                seen.add(pick.get("code"))
                family_counts[family] = family_counts.get(family, 0) + 1
                pool.remove(pick)
                progressed = True
                if len(selected) >= limit:
                    break
            if not progressed:
                break

    return selected
