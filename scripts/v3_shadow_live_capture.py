#!/usr/bin/env python3
"""Capture KST minute evidence for V3 shadow candidates.

V3.1 design:
- production read-only: only public Worker /live and /scan are read.
- one session can be checkpointed at 09:35 and resumed to 09:40.
- /scan is opt-in by minute; production schedule uses only 09:35 to avoid duplicate full-market scans.
- transient /live failures are retried within a bounded per-minute window.
- failure diagnostics are written to the output before exiting non-zero.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
DEFAULT_BASE = "https://kr-stock-live-bridge.bjm8754.workers.dev"
SCHEMA = "V3_SHADOW_LIVE_CAPTURE_V1"
MODE = "SHADOW_ONLY"
START_SECOND = 5
LIVE_DEADLINE_SECOND = 48
RETRY_SLEEP_SECONDS = 4.0
SCAN_RETRIES = 2
SCAN_RETRY_SLEEP_SECONDS = 4.0


def get_json(url: str, timeout: int = 20):
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json,text/plain,*/*",
            "User-Agent": "v3-shadow-live-capture/1.2",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


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


def parse_scan_minutes(raw: str) -> set[int]:
    raw = (raw or "").strip()
    if not raw:
        return set()
    out = set()
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        minute = int(item)
        if not 0 <= minute <= 40:
            raise ValueError(f"INVALID_SCAN_MINUTE:{minute}")
        out.add(minute)
    return out


def build_output(args, codes, rows, scans, scan_diagnostics, attempts, errors, status, fail_reason):
    return {
        "status": status,
        "schemaVersion": SCHEMA,
        "mode": MODE,
        "productionWriteAllowed": False,
        "tradeDate": args.trade_date,
        "codes": codes,
        "source": "PUBLIC_WORKER_READ_ONLY",
        "capturedAtKst": dt.datetime.now(KST).isoformat(),
        "endMinute": args.end_minute,
        "history": {
            "count": len(rows),
            "from": rows[0]["atKst"] if rows else None,
            "to": rows[-1]["atKst"] if rows else None,
            "rows": rows,
        },
        "marketScans": scans,
        "scanDiagnostics": scan_diagnostics,
        "diagnostics": {
            "startMinute": args.start_minute,
            "requestedEndMinute": args.end_minute,
            "resumeFrom": args.resume_from,
            "attemptsByMinute": attempts,
            "recentErrors": errors[-20:],
            "failReason": fail_reason,
        },
    }


def write_output(path: str, obj):
    Path(path).write_text(
        json.dumps(obj, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def load_resume(path: str, trade_date: str, codes, start_minute: int):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schemaVersion") != SCHEMA:
        raise RuntimeError("RESUME_SCHEMA_MISMATCH")
    if data.get("mode") != MODE or data.get("productionWriteAllowed") is not False:
        raise RuntimeError("RESUME_MODE_MISMATCH")
    if data.get("tradeDate") != trade_date:
        raise RuntimeError("RESUME_TRADE_DATE_MISMATCH")
    if data.get("codes") != codes:
        raise RuntimeError("RESUME_CODES_MISMATCH")
    if data.get("status") not in {"PASS", "PARTIAL"}:
        raise RuntimeError(f"RESUME_STATUS_INVALID:{data.get('status')}")

    rows = ((data.get("history") or {}).get("rows") or [])
    expected = [f"{trade_date} 09{m:02d}" for m in range(start_minute)]
    actual = [r.get("atKst") for r in rows]
    if actual != expected:
        raise RuntimeError(
            f"RESUME_HISTORY_MISMATCH:{len(actual)}_ROWS_EXPECTED_{len(expected)}"
        )
    scans = data.get("marketScans") or {}
    scan_diagnostics = data.get("scanDiagnostics") or {}
    return rows, scans, scan_diagnostics


def capture_live_minute(base: str, codes, target: dt.datetime):
    query = urllib.parse.urlencode({"codes": ",".join(codes)})
    url = f"{base.rstrip('/')}/live?{query}"
    deadline = target.replace(second=LIVE_DEADLINE_SECOND, microsecond=0)
    attempt = 0
    last_error = None

    while True:
        now = dt.datetime.now(KST)
        remaining = (deadline - now).total_seconds()
        if remaining <= 0:
            return None, None, attempt, last_error or "LIVE_DEADLINE_EXCEEDED"

        attempt += 1
        try:
            timeout = max(2, min(8, int(remaining)))
            payload = get_json(url, timeout=timeout)
            finished = dt.datetime.now(KST)
            if finished > deadline:
                last_error = f"LIVE_RESPONSE_TOO_LATE:{finished.isoformat()}"
            else:
                stocks = validate_live_payload(payload, codes)
                return payload, stocks, attempt, None
        except Exception as exc:
            last_error = f"{type(exc).__name__}:{exc}"

        now = dt.datetime.now(KST)
        if now >= deadline:
            return None, None, attempt, last_error
        time.sleep(min(RETRY_SLEEP_SECONDS, max(0.0, (deadline - now).total_seconds())))


def capture_scan(base: str):
    last_error = None
    for attempt in range(1, SCAN_RETRIES + 1):
        try:
            return get_json(f"{base.rstrip('/')}/scan", timeout=20), attempt, None
        except Exception as exc:
            last_error = f"{type(exc).__name__}:{exc}"
            if attempt < SCAN_RETRIES:
                time.sleep(SCAN_RETRY_SLEEP_SECONDS)
    return None, SCAN_RETRIES, last_error


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trade-date", required=True, help="YYYYMMDD target KRX session")
    ap.add_argument("--codes", required=True, help="comma-separated six-digit codes")
    ap.add_argument("--base", default=DEFAULT_BASE)
    ap.add_argument("--output", default="/tmp/v3-shadow-live.json")
    ap.add_argument("--start-minute", type=int, default=0)
    ap.add_argument("--end-minute", type=int, default=40)
    ap.add_argument(
        "--scan-minutes",
        default="35",
        help="comma-separated minutes after 09:00 that call full-market /scan; empty disables",
    )
    ap.add_argument(
        "--resume-from",
        default=None,
        help="previous V3 shadow capture JSON; required when start-minute > 0",
    )
    ap.add_argument(
        "--allow-late-start",
        action="store_true",
        help="diagnostic only; strict E2E should not use this",
    )
    args = ap.parse_args()

    codes = []
    rows = []
    scans = {}
    scan_diagnostics = {}
    attempts = {}
    errors = []
    fail_reason = None
    status = "FAIL"

    try:
        if not 0 <= args.start_minute <= args.end_minute <= 40:
            raise RuntimeError(
                f"INVALID_MINUTE_RANGE:{args.start_minute}-{args.end_minute}"
            )

        for raw in args.codes.split(","):
            c = raw.strip()
            if len(c) == 6 and c.isdigit() and c not in codes:
                codes.append(c)
        if not codes:
            raise RuntimeError("NO_VALID_CODES")
        if len(args.trade_date) != 8 or not args.trade_date.isdigit():
            raise RuntimeError("INVALID_TRADE_DATE")

        scan_minutes = parse_scan_minutes(args.scan_minutes)
        now = dt.datetime.now(KST)
        if now.strftime("%Y%m%d") != args.trade_date:
            raise RuntimeError(
                f"TRADE_DATE_MISMATCH:{now:%Y%m%d}!={args.trade_date}"
            )

        session_start = now.replace(
            hour=9, minute=0, second=START_SECOND, microsecond=0
        )

        if args.start_minute > 0:
            if not args.resume_from:
                raise RuntimeError("RESUME_REQUIRED_FOR_NONZERO_START")
            rows, scans, scan_diagnostics = load_resume(
                args.resume_from, args.trade_date, codes, args.start_minute
            )
        elif args.resume_from:
            raise RuntimeError("RESUME_NOT_ALLOWED_FOR_ZERO_START")

        first_target = session_start + dt.timedelta(minutes=args.start_minute)
        if (
            args.start_minute == 0
            and now > first_target + dt.timedelta(seconds=20)
            and not args.allow_late_start
        ):
            raise RuntimeError(f"LATE_START:{now.isoformat()}")
        if now > session_start + dt.timedelta(minutes=args.end_minute, seconds=LIVE_DEADLINE_SECOND):
            raise RuntimeError(f"AFTER_CAPTURE_WINDOW:{now.isoformat()}")

        if now < first_target:
            sleep_until(first_target)

        for m in range(args.start_minute, args.end_minute + 1):
            target = session_start + dt.timedelta(minutes=m)
            sleep_until(target)
            expected_at = f"{args.trade_date} 09{m:02d}"

            actual = dt.datetime.now(KST)
            if actual > target.replace(second=LIVE_DEADLINE_SECOND, microsecond=0):
                raise RuntimeError(
                    f"CAPTURE_TOO_LATE:{expected_at}:{actual.isoformat()}"
                )

            live, stocks, n_attempts, error = capture_live_minute(
                args.base, codes, target
            )
            attempts[f"09{m:02d}"] = n_attempts

            if error:
                errors.append(
                    {
                        "minute": f"09{m:02d}",
                        "kind": "LIVE",
                        "attempts": n_attempts,
                        "error": error,
                    }
                )
                raise RuntimeError(f"LIVE_CAPTURE_FAILED:{expected_at}:{error}")

            rows.append(
                {
                    "atKst": expected_at,
                    "capturedAtKst": dt.datetime.now(KST).isoformat(),
                    "stocks": stocks,
                    "indexes": live.get("indexes") or {},
                }
            )

            if m in scan_minutes:
                scan, scan_attempts, scan_error = capture_scan(args.base)
                if scan_error:
                    scan_diagnostics[f"09{m:02d}"] = {
                        "status": "FAIL",
                        "attempts": scan_attempts,
                        "error": scan_error,
                    }
                    errors.append(
                        {
                            "minute": f"09{m:02d}",
                            "kind": "SCAN",
                            "attempts": scan_attempts,
                            "error": scan_error,
                        }
                    )
                else:
                    scans[f"09{m:02d}"] = scan
                    scan_diagnostics[f"09{m:02d}"] = {
                        "status": "PASS",
                        "attempts": scan_attempts,
                        "error": None,
                    }

        expected = [
            f"{args.trade_date} 09{m:02d}" for m in range(args.end_minute + 1)
        ]
        actual_keys = [r.get("atKst") for r in rows]
        if actual_keys != expected:
            raise RuntimeError(
                f"HISTORY_SEQUENCE_MISMATCH:{len(actual_keys)}_OF_{len(expected)}"
            )

        required_scan_failures = [
            key
            for key, diag in scan_diagnostics.items()
            if diag.get("status") != "PASS"
        ]
        status = "PARTIAL" if required_scan_failures else "PASS"

    except Exception as exc:
        fail_reason = f"{type(exc).__name__}:{exc}"
        errors.append({"kind": "FATAL", "error": fail_reason})
        status = "FAIL"

    out = build_output(
        args,
        codes,
        rows,
        scans,
        scan_diagnostics,
        attempts,
        errors,
        status,
        fail_reason,
    )
    write_output(args.output, out)

    print(
        json.dumps(
            {
                "status": status,
                "tradeDate": args.trade_date,
                "codes": codes,
                "startMinute": args.start_minute,
                "endMinute": args.end_minute,
                "historyCount": len(rows),
                "from": out["history"]["from"],
                "to": out["history"]["to"],
                "scanKeys": sorted(scans),
                "scanDiagnostics": scan_diagnostics,
                "failReason": fail_reason,
            },
            ensure_ascii=False,
        )
    )
    if status == "FAIL":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
