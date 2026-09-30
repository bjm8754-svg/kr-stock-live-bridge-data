#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import re

DATE10_ANY = re.compile(r'(?<!\d)(20\d{2}-\d{2}-\d{2})(?!\d)')
DATE8_ANY = re.compile(r'(?<!\d)(20\d{6})(?!\d)')


def _parse_calendar_token(token: str):
    for fmt in ('%Y-%m-%d', '%Y%m%d'):
        try:
            return dt.datetime.strptime(token, fmt).date()
        except ValueError:
            pass
    return None


def _to_relative(token: str, cutoff: dt.date) -> str:
    d = _parse_calendar_token(token)
    if d is None:
        return token
    return f"T{(d-cutoff).days:+d}D"


def redact_calendar_dates(text: str, cutoff: dt.date) -> str:
    """Redact only valid calendar dates embedded in strings.

    Invalid 8-digit numbers such as 20230000 are preserved. Numeric JSON values are
    never inspected here, so prices/trading values cannot be mistaken for dates.
    """
    text = DATE10_ANY.sub(lambda m: _to_relative(m.group(1), cutoff), text)
    text = DATE8_ANY.sub(lambda m: _to_relative(m.group(1), cutoff), text)
    return text


def redact_embedded_dates(obj, cutoff: dt.date):
    if isinstance(obj, dict):
        return {k: redact_embedded_dates(v, cutoff) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact_embedded_dates(v, cutoff) for v in obj]
    if isinstance(obj, str):
        return redact_calendar_dates(obj, cutoff)
    return obj


def calendar_date_leak_paths(obj, path='$'):
    """Return JSON paths containing valid calendar dates in string values only."""
    leaks = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            leaks.extend(calendar_date_leak_paths(v, f'{path}.{k}'))
        return leaks
    if isinstance(obj, list):
        for i, v in enumerate(obj):
            leaks.extend(calendar_date_leak_paths(v, f'{path}[{i}]'))
        return leaks
    if isinstance(obj, str):
        for rx in (DATE10_ANY, DATE8_ANY):
            for m in rx.finditer(obj):
                if _parse_calendar_token(m.group(1)) is not None:
                    leaks.append({'path': path, 'token': m.group(1), 'value': obj[:240]})
    return leaks


def contains_calendar_date_string(obj) -> bool:
    return bool(calendar_date_leak_paths(obj))
