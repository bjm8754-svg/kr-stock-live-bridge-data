#!/usr/bin/env python3
import datetime as dt
from zoneinfo import ZoneInfo

from validate_market_structure_v3_freshness import validate

KST = ZoneInfo("Asia/Seoul")


def base_scan(trade_date="20260929"):
    return {
        "status": "PASS",
        "tradeDate": trade_date,
        "generatedAtKst": "2026-09-30T00:31:52+09:00",
        "methodologyVersion": "MARKET_STRUCTURE_V3_2026-09-29",
    }


# After midnight / before market: latest completed KRX session is prior calendar day.
now = dt.datetime(2026, 9, 30, 8, 15, tzinfo=KST)
sources = {"005930": "20260929", "000660": "20260929", "035420": "20260929"}
out = validate(base_scan(), sources, now)
assert out["status"] == "PASS", out
assert out["expectedCompletedTradeDate"] == "20260929"

# A truly stale scan must still fail as stale.
out = validate(base_scan("20260928"), sources, now)
assert out["status"] == "STALE", out
assert out["reasons"] == ["SCAN_TRADE_DATE_STALE"]

# A scan ahead of the latest completed session is invalid.
out = validate(base_scan("20260930"), sources, now)
assert out["status"] == "FAIL", out
assert "SCAN_TRADE_DATE_AHEAD_OF_COMPLETED_SESSION" in out["reasons"]

# Two agreeing references are sufficient; one dissenting source must not flip the session.
sources = {"005930": "20260929", "000660": "20260929", "035420": "20260928"}
out = validate(base_scan(), sources, now)
assert out["status"] == "PASS", out
assert out["referenceConsensusCount"] == 2

# Wrong methodology remains a hard failure.
bad = base_scan()
bad["methodologyVersion"] = "YBM_SWING_V2_2026-09-23"
out = validate(bad, sources, now)
assert out["status"] == "FAIL", out
assert "SCAN_METHODOLOGY_UNEXPECTED" in out["reasons"]

print("Market Structure V3 freshness tests: PASS")
