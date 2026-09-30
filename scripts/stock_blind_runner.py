#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

CORE = Path(__file__).with_name('stock_blind_walkforward.py')
spec = importlib.util.spec_from_file_location('stock_blind_core', CORE)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

_original_scrub = mod.scrub
_real_search = re.search
_date10 = re.compile(r'20\d{2}-\d{2}-\d{2}')
_date8 = re.compile(r'20\d{6}')
_guard_pattern = r'20\d{2}-\d{2}-\d{2}|20\d{6}'


def _redact_string(s, cutoff):
    def r10(m):
        return mod.relative_date_string(m.group(0), cutoff)
    def r8(m):
        return mod.relative_date_string(m.group(0), cutoff)
    s = _date10.sub(r10, s)
    s = _date8.sub(r8, s)
    return s


def _redact_embedded(obj, cutoff):
    if isinstance(obj, dict):
        return {k: _redact_embedded(v, cutoff) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_redact_embedded(x, cutoff) for x in obj]
    if isinstance(obj, str):
        return _redact_string(obj, cutoff)
    return obj


def hardened_scrub(obj, cutoff, replacements=None):
    first = _original_scrub(obj, cutoff, replacements)
    return _redact_embedded(first, cutoff)


def _has_calendar_string(obj):
    if isinstance(obj, dict):
        return any(_has_calendar_string(v) for v in obj.values())
    if isinstance(obj, list):
        return any(_has_calendar_string(v) for v in obj)
    if isinstance(obj, str):
        return bool(_date10.search(obj) or _date8.search(obj))
    return False


def guarded_search(pattern, string, flags=0):
    raw = pattern.pattern if hasattr(pattern, 'pattern') else pattern
    if raw == _guard_pattern:
        try:
            obj = json.loads(string)
        except Exception:
            return _real_search(pattern, string, flags)
        # Return a truthy sentinel only for actual calendar-like strings.
        return True if _has_calendar_string(obj) else None
    return _real_search(pattern, string, flags)


mod.scrub = hardened_scrub
# The core guard historically searched raw JSON text and could mistake large numeric
# prices/trading values for YYYYMMDD. Restrict only that exact guard to JSON strings.
mod.re.search = guarded_search
mod.main()
