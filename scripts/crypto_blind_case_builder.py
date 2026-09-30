#!/usr/bin/env python3
"""Build deterministic BTC/ETH blind replay cases from Binance public market data.

The generated case files contain ONLY information available through the cutoff
candle. No future bars or outcomes are written. Cases are stratified through
time with a fixed seed to avoid cherry-picking.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import random
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = "https://data-api.binance.vision/api/v3/klines"
SYMBOLS = ("BTCUSDT", "ETHUSDT")
START = dt.date(2019, 1, 1)
END = dt.date(2025, 12, 31)
CASE_COUNT = 20
SEED = 8754
LOOKBACK_DAYS = 365
MIN_EDGE_DAYS = 45
OUTDIR = Path("research/crypto_blind/cases")


def ms(d: dt.date) -> int:
    return int(dt.datetime(d.year, d.month, d.day, tzinfo=dt.timezone.utc).timestamp() * 1000)


def fetch_all(symbol: str, start: dt.date, end: dt.date):
    rows = []
    cursor = ms(start)
    end_ms = ms(end + dt.timedelta(days=1)) - 1
    while cursor <= end_ms:
        q = urlencode({"symbol": symbol, "interval": "1d", "startTime": cursor, "endTime": end_ms, "limit": 1000})
        req = Request(f"{BASE}?{q}", headers={"User-Agent": "crypto-blind-replay/1.0"})
        with urlopen(req, timeout=30) as r:
            batch = json.loads(r.read().decode("utf-8"))
        if not batch:
            break
        for x in batch:
            d = dt.datetime.fromtimestamp(x[0] / 1000, tz=dt.timezone.utc).date()
            rows.append({
                "date": d.isoformat(),
                "open": float(x[1]),
                "high": float(x[2]),
                "low": float(x[3]),
                "close": float(x[4]),
                "volume": float(x[5]),
                "quoteVolume": float(x[7]),
            })
        nxt = int(batch[-1][0]) + 86400000
        if nxt <= cursor:
            break
        cursor = nxt
        time.sleep(0.05)
    return rows


def rsi14(closes):
    if len(closes) < 15:
        return None
    gains = []
    losses = []
    for a, b in zip(closes[-15:-1], closes[-14:]):
        d = b - a
        gains.append(max(d, 0.0))
        losses.append(max(-d, 0.0))
    ag = sum(gains) / 14
    al = sum(losses) / 14
    if al == 0:
        return 100.0
    rs = ag / al
    return round(100 - 100 / (1 + rs), 2)


def resample(rows, mode):
    buckets = {}
    for r in rows:
        d = dt.date.fromisoformat(r["date"])
        if mode == "week":
            iso = d.isocalendar()
            key = f"{iso.year}-W{iso.week:02d}"
        elif mode == "month":
            key = f"{d.year}-{d.month:02d}"
        else:
            raise ValueError(mode)
        b = buckets.setdefault(key, {"date": r["date"], "open": r["open"], "high": r["high"], "low": r["low"], "close": r["close"], "volume": 0.0, "quoteVolume": 0.0})
        b["date"] = r["date"]
        b["high"] = max(b["high"], r["high"])
        b["low"] = min(b["low"], r["low"])
        b["close"] = r["close"]
        b["volume"] += r["volume"]
        b["quoteVolume"] += r["quoteVolume"]
    return list(buckets.values())


def pct(a, b):
    return None if not b else round((a / b - 1) * 100, 2)


def enrich(rows):
    closes = [r["close"] for r in rows]
    last = rows[-1]
    out = {
        "cutoff": last["date"],
        "lastClose": last["close"],
        "rsi14": rsi14(closes),
        "change7dPct": pct(last["close"], closes[-8]) if len(closes) >= 8 else None,
        "change30dPct": pct(last["close"], closes[-31]) if len(closes) >= 31 else None,
        "change90dPct": pct(last["close"], closes[-91]) if len(closes) >= 91 else None,
        "range30": {"high": max(r["high"] for r in rows[-30:]), "low": min(r["low"] for r in rows[-30:])},
        "range90": {"high": max(r["high"] for r in rows[-90:]), "low": min(r["low"] for r in rows[-90:])},
        "daily": rows[-180:],
        "weekly": resample(rows[-365:], "week")[-60:],
        "monthly": resample(rows, "month")[-36:],
    }
    return out


def choose_cutoffs(valid_dates):
    lo = START + dt.timedelta(days=LOOKBACK_DAYS)
    hi = END - dt.timedelta(days=30)
    eligible = [d for d in valid_dates if lo <= d <= hi]
    span = (hi - lo).days + 1
    rng = random.Random(SEED)
    picks = []
    for i in range(CASE_COUNT):
        s = lo + dt.timedelta(days=math.floor(span * i / CASE_COUNT))
        e = lo + dt.timedelta(days=math.floor(span * (i + 1) / CASE_COUNT) - 1)
        pool = [d for d in eligible if s <= d <= e]
        if not pool:
            continue
        picks.append(rng.choice(pool))
    return sorted(picks)


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    fetch_start = START - dt.timedelta(days=LOOKBACK_DAYS + 10)
    fetch_end = END
    data = {s: fetch_all(s, fetch_start, fetch_end) for s in SYMBOLS}
    maps = {s: {dt.date.fromisoformat(r["date"]): r for r in rows} for s, rows in data.items()}
    common = sorted(set(maps[SYMBOLS[0]]) & set(maps[SYMBOLS[1]]))
    cutoffs = choose_cutoffs(common)
    manifest = {
        "schema": "CRYPTO_BLIND_REPLAY_V1",
        "seed": SEED,
        "caseCount": len(cutoffs),
        "symbols": list(SYMBOLS),
        "initialCapitalKrw": 10000000,
        "futureIncluded": False,
        "executionNote": "Decision is made after cutoff daily close; any immediate market entry is scored from next UTC daily open. Future is revealed only after decision is locked.",
        "cases": [],
    }
    for idx, cutoff in enumerate(cutoffs, 1):
        payload = {
            "schema": "CRYPTO_BLIND_CASE_V1",
            "caseId": f"C{idx:02d}",
            "cutoff": cutoff.isoformat(),
            "futureIncluded": False,
            "assets": {},
        }
        for s in SYMBOLS:
            hist = [r for r in data[s] if dt.date.fromisoformat(r["date"]) <= cutoff]
            payload["assets"][s] = enrich(hist)
        fn = f"C{idx:02d}.json"
        (OUTDIR / fn).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        manifest["cases"].append({"caseId": payload["caseId"], "cutoff": payload["cutoff"], "file": fn})
    (OUTDIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "caseCount": len(cutoffs), "first": cutoffs[0].isoformat(), "last": cutoffs[-1].isoformat()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
