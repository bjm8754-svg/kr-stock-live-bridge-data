#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import re
from pathlib import Path

CORE = Path(__file__).with_name('stock_blind_walkforward.py')
spec = importlib.util.spec_from_file_location('stock_blind_core', CORE)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

_original_scrub = mod.scrub
_date10 = re.compile(r'20\d{2}-\d{2}-\d{2}')
_date8 = re.compile(r'20\d{6}')


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


mod.scrub = hardened_scrub
mod.main()
