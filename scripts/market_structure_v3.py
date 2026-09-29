#!/usr/bin/env python3
"""Market Structure V3 full-market scanner.

The machine layer is a universe compressor and evidence packager:
price/volume/time -> important levels -> role states -> setup hypotheses ->
mechanical plan -> assistant deep review.

It intentionally does not claim to automate every chart-context judgement. YBM is
not the governing architecture, and existing market-data infrastructure remains
reusable.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime as dt
import json
from pathlib import Path

import FinanceDataReader as fdr
import pandas as pd

from msv3.engine import analyze_frame, build_output

KST = dt.timezone(dt.timedelta(hours=9))


def current_listing():
    try:
        from FinanceDataReader.krx.listing import KrxMarcapListing
        df = KrxMarcapListing("KRX").read().copy()
    except Exception:
        df = fdr.StockListing("KRX").copy()

    code_col = "Code" if "Code" in df.columns else "Symbol"
    df[code_col] = df[code_col].astype(str).str.zfill(6)
    df = df[df[code_col].str.fullmatch(r"\d{6}")].copy()
    if "Market" in df.columns:
        df = df[df["Market"].isin(["KOSPI", "KOSDAQ"])]
    if "Name" in df.columns:
        df = df[~df["Name"].astype(str).str.contains(r"스팩|SPAC", case=False, regex=True, na=False)]

    out = []
    for _, x in df.iterrows():
        out.append({
            "code": x[code_col],
            "name": str(x.get("Name", x[code_col])),
            "market": str(x.get("Market", "")),
            "amount": float(x["Amount"]) if "Amount" in df.columns and pd.notna(x.get("Amount")) else None,
            "marcap": float(x["Marcap"]) if "Marcap" in df.columns and pd.notna(x.get("Marcap")) else None,
        })
    return out


def analyze(meta, cfg):
    start = (dt.date.today() - dt.timedelta(days=int(cfg["historyCalendarDays"]))).isoformat()
    raw = fdr.DataReader(meta["code"], start)
    return analyze_frame(meta, raw, cfg)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="market-structure-v3-config.json")
    p.add_argument("--output", default="market-structure-v3.json")
    p.add_argument("--full-output", default="/tmp/market-structure-v3-full.json")
    args = p.parse_args()

    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    universe = current_listing()
    if len(universe) < int(cfg.get("minUniverseCount", 2200)):
        raise SystemExit(f"universe too small: {len(universe)}")

    rows, errors = [], []
    with cf.ThreadPoolExecutor(max_workers=int(cfg.get("maxWorkers", 8))) as ex:
        fm = {ex.submit(analyze, meta, cfg): meta for meta in universe}
        for fut in cf.as_completed(fm):
            meta = fm[fut]
            try:
                rows.append(fut.result())
            except Exception as e:
                errors.append({
                    "code": meta["code"],
                    "name": meta["name"],
                    "error": f"{type(e).__name__}: {e}",
                })

    now = dt.datetime.now(KST).isoformat()
    compact = build_output(rows, errors, cfg, now)

    # Keep the diagnostic artifact compact. Recent chart traces are already preserved
    # for the bounded assistant deep-review queue in the compact output; storing them
    # for the entire market would add weight without improving auditability.
    full_rows = []
    for row in rows:
        x = dict(row)
        if isinstance(x.get("review"), dict):
            review = dict(x["review"])
            review.pop("chartTrace", None)
            review.pop("traceSchema", None)
            x["review"] = review
        full_rows.append(x)

    full = {
        "status": compact["status"],
        "schemaVersion": compact["schemaVersion"],
        "methodologyVersion": compact["methodologyVersion"],
        "generatedAtKst": now,
        "tradeDate": compact["tradeDate"],
        "coverage": compact["coverage"],
        "counts": compact["counts"],
        "rows": full_rows,
        "errors": errors,
    }

    Path(args.output).write_text(json.dumps(compact, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(args.full_output).write_text(json.dumps(full, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({
        "status": compact["status"],
        "tradeDate": compact["tradeDate"],
        "coverage": compact["coverage"],
        "counts": compact["counts"],
        "output": args.output,
        "fullOutput": args.full_output,
    }, ensure_ascii=False))

    if compact["status"] not in ("PASS", "PARTIAL"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
