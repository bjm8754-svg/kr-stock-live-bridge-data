#!/usr/bin/env python3
"""Capture 09:00~09:40 KST minute evidence for V3 shadow candidates.

This script is intentionally production-isolated:
- reads only the public Worker /live and /scan endpoints,
- never writes Worker KV, production watchlist.json, live.json, or Library production files,
- fails closed if it cannot capture a complete 41-minute sequence.

For a strict real-session validation the process must already be running before 09:00 KST.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
DEFAULT_BASE = "https://kr-stock-live-bridge.bjm8754.workers.dev"
SCAN_MINUTES = {30, 35, 40}


def get_json(url: str, timeout: int = 20):
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json,text/plain,*/*",
            "User-Agent": "v3-shadow-live-capture/1.0",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def minute_key(now: dt.datetime) -> str:
    return now.strftime("%Y%m%d %H%M")


def sleep_until(target: dt.datetime):
    while True:
        now = dt.datetime.now(KST)
        remaining = (target - now).total_seconds()
        if remaining <= 0:
            return
        time.sleep(min(remaining, 5.0))


def validate_live_payload(payload, codes):
    stocks = payload.get("stocks") or {}
    missing = [c for c in codes if c not in stocks]
    if missing:
        raise RuntimeError(f"MISSING_STOCKS:{','.join(missing)}")

    open_count = 0
    valid_count = 0
    for c in codes:
        row = stocks.get(c) or {}
        if row.get("currentPrice") is not None:
            valid_count += 1
        if row.get("marketStatus") == "OPEN":
            open_count += 1
    if valid_count != len(codes):
        raise RuntimeError(f"INVALID_STOCK_PAYLOAD:{valid_count}_OF_{len(codes)}")
    if open_count < max(1, (len(codes) + 1) // 2):
        raise RuntimeError(f"MARKET_NOT_OPEN:{open_count}_OF_{len(codes)}")
    return stocks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trade-date", required=True, help="YYYYMMDD target KRX session")
    ap.add_argument("--codes", required=True, help="comma-separated six-digit codes")
    ap.add_argument("--base", default=DEFAULT_BASE)
    ap.add_argument("--output", default="/tmp/v3-shadow-live.json")
    ap.add_argument("--allow-late-start", action="store_true",
                    help="diagnostic only; strict E2E should not use this")
    args = ap.parse_args()

    codes = []
    for raw in args.codes.split(","):
        c = raw.strip()
        if len(c) == 6 and c.isdigit() and c not in codes:
            codes.append(c)
    if not codes:
        raise SystemExit("NO_VALID_CODES")
    if len(args.trade_date) != 8 or not args.trade_date.isdigit():
        raise SystemExit("INVALID_TRADE_DATE")

    now = dt.datetime.now(KST)
    if now.strftime("%Y%m%d") != args.trade_date:
        raise SystemExit(f"TRADE_DATE_MISMATCH:{now:%Y%m%d}!={args.trade_date}")

    start = now.replace(hour=9, minute=0, second=2, microsecond=0)
    end = now.replace(hour=9, minute=40, second=2, microsecond=0)
    if now > start + dt.timedelta(seconds=20) and not args.allow_late_start:
        raise SystemExit(f"LATE_START:{now.isoformat()}")
    if now > end:
        raise SystemExit(f"AFTER_CAPTURE_WINDOW:{now.isoformat()}")

    if now < start:
        sleep_until(start)

    rows = []
    scans = {}
    first_minute = max(0, int((dt.datetime.now(KST) - start).total_seconds() // 60))
    if first_minute > 0 and not args.allow_late_start:
        raise SystemExit(f"MISSED_OPEN_MINUTES:{first_minute}")

    for m in range(first_minute, 41):
        target = start + dt.timedelta(minutes=m)
        sleep_until(target)
        actual = dt.datetime.now(KST)
        expected_at = f"{args.trade_date} 09{m:02d}"
        if actual > target + dt.timedelta(seconds=35):
            raise SystemExit(f"CAPTURE_TOO_LATE:{expected_at}:{actual.isoformat()}")

        q = urllib.parse.urlencode({"codes": ",".join(codes)})
        live = get_json(f"{args.base.rstrip('/')}/live?{q}")
        stocks = validate_live_payload(live, codes)
        rows.append({
            "atKst": expected_at,
            "capturedAtKst": dt.datetime.now(KST).isoformat(),
            "stocks": stocks,
            "indexes": live.get("indexes") or {},
        })

        if m in SCAN_MINUTES:
            scan = get_json(f"{args.base.rstrip('/')}/scan")
            scans[f"09{m:02d}"] = scan

    expected = [f"{args.trade_date} 09{m:02d}" for m in range(41)]
    actual_keys = [r.get("atKst") for r in rows]
    status = "PASS" if actual_keys == expected else "FAIL"
    out = {
        "status": status,
        "schemaVersion": "V3_SHADOW_LIVE_CAPTURE_V1",
        "mode": "SHADOW_ONLY",
        "productionWriteAllowed": False,
        "tradeDate": args.trade_date,
        "codes": codes,
        "source": "PUBLIC_WORKER_READ_ONLY",
        "capturedAtKst": dt.datetime.now(KST).isoformat(),
        "history": {
            "count": len(rows),
            "from": rows[0]["atKst"] if rows else None,
            "to": rows[-1]["atKst"] if rows else None,
            "rows": rows,
        },
        "marketScans": scans,
    }
    Path(args.output).write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": status,
        "tradeDate": args.trade_date,
        "codes": codes,
        "historyCount": len(rows),
        "from": out["history"]["from"],
        "to": out["history"]["to"],
        "scanKeys": sorted(scans),
    }, ensure_ascii=False))
    if status != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
