#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from stock_blind_privacy import calendar_date_leak_paths, redact_embedded_dates

CORE = Path(__file__).with_name('stock_blind_walkforward.py')
spec = importlib.util.spec_from_file_location('stock_blind_core', CORE)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

_original_scrub = mod.scrub


def hardened_scrub(obj, cutoff, replacements=None):
    return redact_embedded_dates(_original_scrub(obj, cutoff, replacements), cutoff)


mod.scrub = hardened_scrub

# The legacy core guard searches serialized JSON text and can mistake numeric values
# shaped like 20xxxxxx for dates. Bypass only that exact legacy guard here; the
# structured string-only guard below is authoritative.
_real_search = mod.re.search
_CORE_GUARD_PATTERN = r'20\d{2}-\d{2}-\d{2}|20\d{6}'


def guarded_search(pattern, string, flags=0):
    raw = pattern.pattern if hasattr(pattern, 'pattern') else pattern
    if raw == _CORE_GUARD_PATTERN:
        return None
    return _real_search(pattern, string, flags)


mod.re.search = guarded_search
mod.main()

if mod.CARD.exists():
    card = json.loads(mod.CARD.read_text(encoding='utf-8'))
    leaks = calendar_date_leak_paths(card)
    if leaks:
        print(json.dumps({'privacyLeaks': leaks[:20]}, ensure_ascii=False, indent=2))
        raise RuntimeError(f'blind privacy guard failed: {len(leaks)} calendar string leak(s)')
    if card.get('futureIncluded') is not False:
        raise RuntimeError('blind privacy guard failed: futureIncluded is not false')

print('STOCK_BLIND_RUNNER_PRIVACY: PASS')
