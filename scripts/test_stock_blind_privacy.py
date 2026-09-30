#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import importlib.util
from pathlib import Path

CORE = Path(__file__).with_name('stock_blind_walkforward.py')
spec = importlib.util.spec_from_file_location('stock_blind_core_privacy_test', CORE)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

cutoff = dt.date(2024, 5, 15)

sample = {
    'code': '005930',
    'name': 'SAMPLE',
    'tradeDate': '20240515',
    'generatedAtKst': '2024-05-15T18:00:00+09:00',
    'methodologyVersion': 'MARKET_STRUCTURE_V3_2026-09-29',
    'nested': [
        'event=20240510 confirmed',
        'plain 2024-05-12 text',
        'invalid-number-string=20230000',
        20260930,
        20230000.0,
    ],
}

out = mod.scrub(sample, cutoff, {'SAMPLE': 'A123456789'})

assert 'code' not in out
assert 'name' not in out
assert 'tradeDate' not in out
assert 'generatedAtKst' not in out
assert '2026-09-29' not in out['methodologyVersion']
assert '20240510' not in out['nested'][0]
assert '2024-05-12' not in out['nested'][1]
assert out['nested'][2] == 'invalid-number-string=20230000'
assert out['nested'][3] == 20260930
assert out['nested'][4] == 20230000.0
assert mod.contains_calendar_date_string(out) is False

leak = {'x': 'embedded date 2024-05-12'}
assert mod.contains_calendar_date_string(leak) is True
invalid = {'x': 'not a real date 20230000', 'price': 20260930}
assert mod.contains_calendar_date_string(invalid) is False

print('STOCK_BLIND_PRIVACY_UNIT: PASS')
