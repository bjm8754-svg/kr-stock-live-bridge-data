#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt

from stock_blind_privacy import (
    calendar_date_leak_paths,
    contains_calendar_date_string,
    redact_embedded_dates,
)

cutoff = dt.date(2024, 5, 15)

sample = {
    'methodologyVersion': 'MARKET_STRUCTURE_V3_2026-09-29',
    'nested': [
        'event=20240510 confirmed',
        'plain 2024-05-12 text',
        'invalid-number-string=20230000',
        20260930,
        20230000.0,
    ],
}

out = redact_embedded_dates(sample, cutoff)
assert out['methodologyVersion'] == 'MARKET_STRUCTURE_V3_T+867D'
assert out['nested'][0] == 'event=T-5D confirmed'
assert out['nested'][1] == 'plain T-3D text'
assert out['nested'][2] == 'invalid-number-string=20230000'
assert out['nested'][3] == 20260930
assert out['nested'][4] == 20230000.0
assert contains_calendar_date_string(out) is False
assert calendar_date_leak_paths(out) == []

leak = {
    'a': 'embedded date 2024-05-12',
    'b': ['MARKET_STRUCTURE_V3_2026-09-29'],
}
paths = calendar_date_leak_paths(leak)
assert len(paths) == 2
assert contains_calendar_date_string(leak) is True

invalid = {
    'x': 'not a real date 20230000',
    'price': 20260930,
    'tradingValue': 20240515.0,
}
assert contains_calendar_date_string(invalid) is False

print('STOCK_BLIND_PRIVACY_UNIT: PASS')
