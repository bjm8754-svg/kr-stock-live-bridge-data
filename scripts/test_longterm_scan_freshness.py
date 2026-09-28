#!/usr/bin/env python3
import datetime as dt
import importlib.util
from pathlib import Path
from zoneinfo import ZoneInfo

P=Path(__file__).with_name("validate_longterm_scan_freshness.py")
spec=importlib.util.spec_from_file_location("fresh", P)
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
KST=ZoneInfo("Asia/Seoul")
NOW=dt.datetime(2026,9,28,8,10,tzinfo=KST)

base={
  "status":"PASS",
  "tradeDate":"20260923",
  "generatedAtKst":"2026-09-23T16:45:00+09:00",
  "methodologyVersion":"YBM_SWING_V2_2026-09-23"
}

x=m.validate(base,{"005930":"20260923","000660":"20260923","035420":"20260923"},NOW)
assert x["status"]=="PASS",x

stale=dict(base); stale["tradeDate"]="20260922"
x=m.validate(stale,{"005930":"20260923","000660":"20260923","035420":"20260923"},NOW)
assert x["status"]=="STALE",x
assert "SCAN_TRADE_DATE_STALE" in x["reasons"]

future=dict(base); future["tradeDate"]="20260928"
x=m.validate(future,{"005930":"20260923","000660":"20260923","035420":"20260923"},NOW)
assert x["status"]=="FAIL",x
assert "SCAN_TRADE_DATE_AHEAD_OF_COMPLETED_SESSION" in x["reasons"]

x=m.validate(base,{"005930":"20260923","000660":None,"035420":"20260922"},NOW)
assert x["status"]=="FAIL",x
assert "REFERENCE_SESSION_CONSENSUS_INSUFFICIENT" in x["reasons"]

bad=dict(base); bad["status"]="PARTIAL"
x=m.validate(bad,{"005930":"20260923","000660":"20260923","035420":"20260923"},NOW)
assert x["status"]=="FAIL",x
assert "SCAN_STATUS_NOT_PASS" in x["reasons"]

print("ALL_FRESHNESS_TESTS_PASS")
