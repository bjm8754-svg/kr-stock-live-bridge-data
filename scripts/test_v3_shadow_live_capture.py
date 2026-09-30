#!/usr/bin/env python3
from v3_shadow_live_capture import validate_live_payload

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

print("V3 shadow live capture tests: PASS")
