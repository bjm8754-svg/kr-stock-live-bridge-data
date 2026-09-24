#!/usr/bin/env python3
import argparse
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")


def parse_args():
    p = argparse.ArgumentParser(description="Validate live.json semantic freshness.")
    p.add_argument("--live", default="live.json")
    p.add_argument("--watchlist", default="watchlist.json")
    p.add_argument("--output", default="live-health.json")
    p.add_argument("--asof-date", default=None, help="YYYYMMDD override for replay/tests")
    return p.parse_args()


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def minute_key(value):
    return datetime.strptime(value, "%Y%m%d %H%M")


def main():
    a = parse_args()
    now = datetime.now(KST)
    expected_date = a.asof_date or now.strftime("%Y%m%d")
    live = load_json(a.live)
    watch = load_json(a.watchlist)

    reasons = []
    rows = (live.get("history") or {}).get("rows") or []
    history = live.get("history") or {}
    live_codes = live.get("watchlist") or []
    watch_codes = watch.get("codes") or []

    if live.get("tradeDate") != expected_date:
        reasons.append("LIVE_TRADE_DATE_MISMATCH")
    if watch.get("tradeDate") != expected_date:
        reasons.append("WATCHLIST_TRADE_DATE_MISMATCH")
    if live_codes != watch_codes:
        reasons.append("WATCHLIST_CODES_MISMATCH")

    if history.get("count") != len(rows):
        reasons.append("HISTORY_COUNT_MISMATCH")

    if not rows:
        reasons.append("HISTORY_EMPTY")
    else:
        row_times = [r.get("atKst") for r in rows]
        try:
            parsed = [minute_key(x) for x in row_times]
            if len(set(row_times)) != len(row_times):
                reasons.append("DUPLICATE_HISTORY_TIMESTAMPS")
            for prev, cur in zip(parsed, parsed[1:]):
                if int((cur - prev).total_seconds()) != 60:
                    reasons.append("NONCONTIGUOUS_HISTORY")
                    break
            if history.get("from") != row_times[0] or history.get("to") != row_times[-1]:
                reasons.append("HISTORY_RANGE_MISMATCH")
            if any(x[:8] != live.get("tradeDate") for x in row_times if isinstance(x, str) and len(x) >= 8):
                reasons.append("ROW_TRADE_DATE_MISMATCH")
        except Exception:
            reasons.append("INVALID_HISTORY_TIMESTAMP")

    valid_codes = []
    dynamic_codes = []
    open_codes = []
    frozen_codes = []
    source_dates = []

    if rows:
        for code in live_codes:
            vals = [r.get("stocks", {}).get(code) for r in rows]
            vals = [v for v in vals if isinstance(v, dict)]
            if not vals:
                continue
            valid_codes.append(code)
            first, last = vals[0], vals[-1]
            if (
                first.get("volume") != last.get("volume")
                or first.get("tradingValue") != last.get("tradingValue")
            ):
                dynamic_codes.append(code)
            if last.get("marketStatus") == "OPEN":
                open_codes.append(code)
            tuples = {
                (
                    v.get("currentPrice"),
                    v.get("volume"),
                    v.get("tradingValue"),
                )
                for v in vals
            }
            if len(tuples) == 1:
                frozen_codes.append(code)

            for v in vals:
                nxt = v.get("nxtOverMarketPriceInfo")
                if isinstance(nxt, dict):
                    ts = nxt.get("localTradedAt")
                    if isinstance(ts, str) and len(ts) >= 10:
                        source_dates.append(ts[:10].replace("-", ""))

    n = len(valid_codes)
    dynamic_ratio = (len(dynamic_codes) / n) if n else 0.0
    open_ratio = (len(open_codes) / n) if n else 0.0
    frozen_ratio = (len(frozen_codes) / n) if n else 1.0

    if n == 0:
        reasons.append("NO_VALID_STOCK_PAYLOAD")
    else:
        if dynamic_ratio < 0.50:
            reasons.append("INSUFFICIENT_INTRADAY_CHANGE")
        if frozen_ratio == 1.0:
            reasons.append("FROZEN_HISTORY")
        if open_ratio < 0.50 and dynamic_ratio < 0.50:
            reasons.append("MARKET_STATUS_CLOSED_OR_STALE")

    if source_dates and all(d < expected_date for d in source_dates):
        reasons.append("STALE_SOURCE_TIMESTAMP")

    published = live.get("publishedAtKst")
    if not isinstance(published, str) or expected_date not in published.replace("-", ""):
        reasons.append("PUBLISHED_AT_DATE_MISMATCH")

    status = "PASS" if not reasons else "FAIL"
    out = {
        "status": status,
        "checkedAtKst": now.strftime("%Y-%m-%d %H:%M:%S KST"),
        "expectedTradeDate": expected_date,
        "liveTradeDate": live.get("tradeDate"),
        "watchlistTradeDate": watch.get("tradeDate"),
        "livePublishedAtKst": published,
        "history": {
            "count": history.get("count"),
            "from": history.get("from"),
            "to": history.get("to"),
            "rows": len(rows),
        },
        "watchlistCount": len(live_codes),
        "validStockCount": n,
        "dynamicStockCount": len(dynamic_codes),
        "dynamicStockRatio": round(dynamic_ratio, 4),
        "openStockCount": len(open_codes),
        "openStockRatio": round(open_ratio, 4),
        "frozenStockCount": len(frozen_codes),
        "frozenStockRatio": round(frozen_ratio, 4),
        "sourceTimestampCount": len(source_dates),
        "reasons": reasons,
    }
    Path(a.output).write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
