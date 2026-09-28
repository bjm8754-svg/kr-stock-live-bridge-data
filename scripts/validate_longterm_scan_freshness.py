#!/usr/bin/env python3
"""Validate that longterm-scan.json represents the latest completed KRX session.

Lightweight pre-open guard. It does not rescan the market.
Reference session date is derived from a consensus of liquid KRX stocks
using Naver's public daily-candle endpoint.
"""
import argparse
import collections
import datetime as dt
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
DEFAULT_CODES = ("005930", "000660", "035420")
BUILD_PREFIX = "YBM_SWING_V2_"


def _walk_dates(obj):
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in {"localDate", "bizDate", "tradeDate", "date"}:
                s = re.sub(r"[^0-9]", "", str(v))
                if re.fullmatch(r"20\d{6}", s):
                    out.append(s)
            out.extend(_walk_dates(v))
    elif isinstance(obj, list):
        for x in obj:
            out.extend(_walk_dates(x))
    return out


def fetch_latest_completed_date(code, asof):
    start = (asof.date() - dt.timedelta(days=25)).strftime("%Y%m%d")
    end = asof.strftime("%Y%m%d")
    qs = urllib.parse.urlencode({
        "periodType": "dayCandle",
        "startDateTime": start,
        "endDateTime": end,
    })
    url = f"https://api.stock.naver.com/chart/domestic/item/{code}?{qs}"
    req = urllib.request.Request(url, headers={
        "Accept": "application/json,text/plain,*/*",
        "User-Agent": "Mozilla/5.0 longterm-scan-freshness/1.0",
        "Referer": f"https://m.stock.naver.com/domestic/stock/{code}/total",
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    dates = sorted(set(_walk_dates(payload)))
    if not dates:
        raise RuntimeError("NO_DAILY_DATES")

    today = asof.strftime("%Y%m%d")
    # Before the completed-daily cutoff, today's candle is unfinished even if
    # an upstream API exposes a partial daily row.
    if asof.hour < 15 or (asof.hour == 15 and asof.minute < 40):
        dates = [x for x in dates if x < today]
    else:
        dates = [x for x in dates if x <= today]

    if not dates:
        raise RuntimeError("NO_COMPLETED_DAILY_DATE")
    return dates[-1]


def validate(scan, source_dates, checked_at):
    reasons = []
    usable = {k: v for k, v in source_dates.items() if re.fullmatch(r"20\d{6}", str(v or ""))}
    counts = collections.Counter(usable.values())
    expected = counts.most_common(1)[0][0] if counts else None
    consensus = counts.get(expected, 0) if expected else 0

    if consensus < 2:
        reasons.append("REFERENCE_SESSION_CONSENSUS_INSUFFICIENT")

    scan_date = str(scan.get("tradeDate") or "")
    scan_status = scan.get("status")
    method = str(scan.get("methodologyVersion") or "")
    if scan_status != "PASS":
        reasons.append("SCAN_STATUS_NOT_PASS")
    if not method.startswith(BUILD_PREFIX):
        reasons.append("SCAN_METHODOLOGY_UNEXPECTED")
    if not scan.get("generatedAtKst"):
        reasons.append("SCAN_GENERATED_AT_MISSING")

    if expected:
        if scan_date < expected:
            reasons.append("SCAN_TRADE_DATE_STALE")
        elif scan_date > expected:
            reasons.append("SCAN_TRADE_DATE_AHEAD_OF_COMPLETED_SESSION")
    else:
        reasons.append("EXPECTED_COMPLETED_SESSION_UNKNOWN")

    status = "PASS" if not reasons else (
        "STALE" if "SCAN_TRADE_DATE_STALE" in reasons and len(reasons) == 1 else "FAIL"
    )
    return {
        "status": status,
        "checkedAtKst": checked_at.strftime("%Y-%m-%d %H:%M:%S KST"),
        "expectedCompletedTradeDate": expected,
        "scanTradeDate": scan_date or None,
        "scanStatus": scan_status,
        "scanGeneratedAtKst": scan.get("generatedAtKst"),
        "methodologyVersion": scan.get("methodologyVersion"),
        "referenceConsensusCount": consensus,
        "referenceDates": source_dates,
        "reasons": reasons,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan", default="longterm-scan.json")
    ap.add_argument("--output", default="longterm-scan-health.json")
    ap.add_argument("--codes", default=",".join(DEFAULT_CODES))
    ap.add_argument("--asof-kst", default=None,
                    help="ISO timestamp for deterministic replay, e.g. 2026-09-28T08:10:00+09:00")
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()

    now = dt.datetime.fromisoformat(a.asof_kst).astimezone(KST) if a.asof_kst else dt.datetime.now(KST)
    scan = json.loads(Path(a.scan).read_text(encoding="utf-8"))

    source_dates = {}
    source_errors = {}
    for code in [x.strip() for x in a.codes.split(",") if x.strip()]:
        try:
            source_dates[code] = fetch_latest_completed_date(code, now)
        except Exception as e:
            source_dates[code] = None
            source_errors[code] = str(e)

    out = validate(scan, source_dates, now)
    if source_errors:
        out["sourceErrors"] = source_errors
    Path(a.output).write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False))
    if a.strict and out["status"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
