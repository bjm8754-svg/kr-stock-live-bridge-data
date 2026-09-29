from __future__ import annotations

import pandas as pd

from .features import rnum
from .execution import rank_key


REVIEW_TIER_ORDER = {"NOW": 3, "SOON": 2, "BACKGROUND": 1}


def _bar_trace(df, cfg):
    """Compact recent OHLCV trace for assistant chart reading.

    This is evidence, not a machine interpretation. It lets the later review layer
    reconstruct the recent chart shape without forcing every visual/context judgement
    into hard-coded detectors.
    """
    n = int(cfg.get("reviewTraceSessions", 90))
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
        "traceSchema": ["date","open","high","low","close","volumeRatio20","tradingValueRatio20","rsi"],
        "chartTrace": _bar_trace(df, cfg),
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
