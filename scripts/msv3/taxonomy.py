from __future__ import annotations

# Categorical precedence only. These numbers are internal sort indexes, not a score and
# are never emitted as candidate quality.
SETUP_STATE_ORDER = (
    "SPRING_CONFIRMED",
    "BOX_RETEST",
    "HIGH_RETEST",
    "TREND_BRIDGE_RETEST",
    "BOX_BREAKOUT_ACCEPTED",
    "LEVEL_RETEST",
    "HIGH_BREAKOUT",
    "BREAKOUT_PRESSURE",
    "BOX_BREAKOUT_PENDING",
    "SPRING_RECLAIM_PENDING",
    "BASE_BREAKOUT",
    "BASE_RECOVERY",
    "HIGH_BASE",
    "BOX_BUILDING",
    "TREND_BRIDGE_ACTIVE",
)

MATURE_EXECUTION_STATES = {
    "BOX_RETEST", "HIGH_RETEST", "TREND_BRIDGE_RETEST", "LEVEL_RETEST",
}

PENDING_STATES = {
    "SPRING_RECLAIM_PENDING", "SPRING_CONFIRMED",
    "BOX_BREAKOUT_PENDING", "BOX_BREAKOUT_ACCEPTED",
    "HIGH_BREAKOUT", "BREAKOUT_PRESSURE", "BASE_BREAKOUT",
}

READINESS_ORDER = {"EXECUTABLE": 4, "WATCH_TRIGGER": 3, "RADAR": 2, "REJECT": 0}

def setup_priority(state):
    try:
        return len(SETUP_STATE_ORDER) - SETUP_STATE_ORDER.index(state)
    except ValueError:
        return 0
