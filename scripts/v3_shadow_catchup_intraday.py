#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
YAHOO_SUFFIX = {
    "010950": ".KS",  # S-Oil
    "000250": ".KQ",  # Samchundang Pharm
    "039030": ".KQ",  # EO Technics
}
YAHOO_HOSTS = ("query1.finance.yahoo.com", "query2.finance.yahoo.com")


def get_json(url: str, attempts: int = 3):
    last_error = None
    for attempt in range(attempts):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "Accept": "application/json,text/plain,*/*",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/154 Safari/537.36",
                },
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            time.sleep(1.0 + attempt)
    raise RuntimeError(f"YAHOO_FETCH_FAILED:{type(last_error).__name__}:{last_error}")


def yahoo_ticker(code: str) -> str:
    suffix = YAHOO_SUFFIX.get(code)
    if not suffix:
        raise RuntimeError(f"UNMAPPED_KRX_CODE:{code}")
    return code + suffix


def recover(code: str, trade_date: str, end_hhmm: str = "0940"):
    target_date = dt.datetime.strptime(trade_date, "%Y%m%d").date()
    start = dt.datetime.combine(target_date, dt.time(8, 55), tzinfo=KST)
    end = dt.datetime.combine(target_date, dt.time(9, 46), tzinfo=KST)
    ticker = yahoo_ticker(code)
    params = urllib.parse.urlencode(
        {
            "period1": int(start.timestamp()),
            "period2": int(end.timestamp()),
            "interval": "1m",
            "includePrePost": "false",
            "events": "div,splits",
        }
    )

    payload = None
    used_host = None
    errors = []
    for host in YAHOO_HOSTS:
        url = f"https://{host}/v8/finance/chart/{ticker}?{params}"
        try:
            payload = get_json(url)
            used_host = host
            break
        except Exception as exc:
            errors.append(f"{host}:{exc}")
    if payload is None:
        return {
            "code": code,
            "ticker": ticker,
            "status": "FAIL",
            "source": "YAHOO_CHART_1M",
            "providerErrors": errors,
            "history": {"count": 0, "from": None, "to": None, "rows": []},
            "missingMinutes": [f"09:{m:02d}" for m in range(41)],
        }

    chart = payload.get("chart") or {}
    if chart.get("error"):
        return {
            "code": code,
            "ticker": ticker,
            "status": "FAIL",
            "source": "YAHOO_CHART_1M",
            "providerHost": used_host,
            "providerErrors": [f"CHART_ERROR:{chart.get('error')}"] + errors,
            "history": {"count": 0, "from": None, "to": None, "rows": []},
            "missingMinutes": [f"09:{m:02d}" for m in range(41)],
        }

    result = (chart.get("result") or [None])[0]
    if not result:
        return {
            "code": code,
            "ticker": ticker,
            "status": "FAIL",
            "source": "YAHOO_CHART_1M",
            "providerHost": used_host,
            "providerErrors": ["EMPTY_RESULT"] + errors,
            "history": {"count": 0, "from": None, "to": None, "rows": []},
            "missingMinutes": [f"09:{m:02d}" for m in range(41)],
        }

    timestamps = result.get("timestamp") or []
    quote = (((result.get("indicators") or {}).get("quote") or [{}])[0])
    opens = quote.get("open") or []
    highs = quote.get("high") or []
    lows = quote.get("low") or []
    closes = quote.get("close") or []
    volumes = quote.get("volume") or []

    by_time = {}
    for i, ts in enumerate(timestamps):
        when = dt.datetime.fromtimestamp(ts, tz=KST)
        if when.date() != target_date:
            continue
        hhmm = when.strftime("%H:%M")
        if not ("09:00" <= hhmm <= end_hhmm[:2] + ":" + end_hhmm[2:]):
            continue
        vals = {
            "open": opens[i] if i < len(opens) else None,
            "high": highs[i] if i < len(highs) else None,
            "low": lows[i] if i < len(lows) else None,
            "close": closes[i] if i < len(closes) else None,
            "volume": volumes[i] if i < len(volumes) else None,
        }
        if any(vals[k] is None for k in ("open", "high", "low", "close")):
            continue
        vals["time"] = hhmm
        vals["atKst"] = f"{trade_date} {when:%H%M}"
        vals["epoch"] = ts
        by_time[hhmm] = vals

    expected = [f"09:{m:02d}" for m in range(41)]
    rows = [by_time[t] for t in expected if t in by_time]
    missing = [t for t in expected if t not in by_time]
    return {
        "code": code,
        "ticker": ticker,
        "status": "PASS" if not missing else "FAIL",
        "source": "YAHOO_CHART_1M",
        "providerHost": used_host,
        "providerErrors": errors,
        "cutoffKst": f"{trade_date} {end_hhmm}",
        "history": {
            "count": len(rows),
            "from": rows[0]["atKst"] if rows else None,
            "to": rows[-1]["atKst"] if rows else None,
            "rows": rows,
        },
        "missingMinutes": missing,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trade-date", required=True)
    ap.add_argument("--codes", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    codes = []
    for raw in args.codes.split(","):
        code = raw.strip()
        if re.fullmatch(r"\d{6}", code) and code not in codes:
            codes.append(code)
    if not codes:
        raise SystemExit("NO_VALID_CODES")

    results = [recover(code, args.trade_date) for code in codes]
    out = {
        "schemaVersion": "V3_SHADOW_CATCHUP_INTRADAY_V1",
        "mode": "SHADOW_ONLY",
        "replayMode": "CATCHUP_REPLAY",
        "realTimeE2E": False,
        "productionWriteAllowed": False,
        "tradeDate": args.trade_date,
        "cutoffKst": f"{args.trade_date} 0940",
        "codes": codes,
        "source": "YAHOO_CHART_1M",
        "status": "PASS" if results and all(x["status"] == "PASS" for x in results) else "FAIL",
        "results": results,
    }
    Path(args.output).write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "results"}, ensure_ascii=False))
    for row in results:
        print(
            json.dumps(
                {
                    "code": row["code"],
                    "ticker": row.get("ticker"),
                    "status": row["status"],
                    "count": row["history"]["count"],
                    "missing": row["missingMinutes"],
                    "providerErrors": row.get("providerErrors"),
                },
                ensure_ascii=False,
            )
        )
    if out["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
