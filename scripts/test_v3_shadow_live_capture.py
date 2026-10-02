#!/usr/bin/env python3
import json
import tempfile
from pathlib import Path

from v3_shadow_live_capture import (
    MODE,
    SCHEMA,
    load_resume,
    parse_scan_minutes,
    validate_live_payload,
)

codes = ["011200", "005930"]

valid = {
    "stocks": {
        "011200": {"currentPrice": 21000, "marketStatus": "OPEN"},
        "005930": {"currentPrice": 280000, "marketStatus": "OPEN"},
    }
}
stocks = validate_live_payload(valid, codes)
assert set(stocks) == set(codes)

missing = {
    "stocks": {
        "011200": {"currentPrice": 21000, "marketStatus": "OPEN"},
    }
}
try:
    validate_live_payload(missing, codes)
    raise AssertionError("missing code must fail")
except RuntimeError as e:
    assert "MISSING_STOCKS" in str(e)

closed = {
    "stocks": {
        "011200": {"currentPrice": 21000, "marketStatus": "CLOSE"},
        "005930": {"currentPrice": 280000, "marketStatus": "CLOSE"},
    }
}
try:
    validate_live_payload(closed, codes)
    raise AssertionError("closed market must fail")
except RuntimeError as e:
    assert "MARKET_NOT_OPEN" in str(e)

invalid = {
    "stocks": {
        "011200": {"currentPrice": None, "marketStatus": "OPEN"},
        "005930": {"currentPrice": 280000, "marketStatus": "OPEN"},
    }
}
try:
    validate_live_payload(invalid, codes)
    raise AssertionError("invalid stock payload must fail")
except RuntimeError as e:
    assert "INVALID_STOCK_PAYLOAD" in str(e)

assert parse_scan_minutes("35") == {35}
assert parse_scan_minutes("") == set()
assert parse_scan_minutes("30,35") == {30, 35}

trade_date = "20261002"
rows = [
    {
        "atKst": f"{trade_date} 09{m:02d}",
        "capturedAtKst": "2026-10-02T09:00:00+09:00",
        "stocks": valid["stocks"],
        "indexes": {},
    }
    for m in range(36)
]
resume = {
    "status": "PARTIAL",
    "schemaVersion": SCHEMA,
    "mode": MODE,
    "productionWriteAllowed": False,
    "tradeDate": trade_date,
    "codes": codes,
    "history": {"count": 36, "from": rows[0]["atKst"], "to": rows[-1]["atKst"], "rows": rows},
    "marketScans": {},
    "scanDiagnostics": {
        "0935": {"status": "FAIL", "attempts": 2, "error": "HTTPError:503"}
    },
}
with tempfile.TemporaryDirectory() as td:
    path = Path(td) / "resume.json"
    path.write_text(json.dumps(resume), encoding="utf-8")
    got_rows, got_scans, got_diag = load_resume(str(path), trade_date, codes, 36)
    assert len(got_rows) == 36
    assert got_scans == {}
    assert got_diag["0935"]["status"] == "FAIL"

print("V3 shadow live capture tests: PASS")
