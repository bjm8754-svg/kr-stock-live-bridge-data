#!/usr/bin/env python3
"""Historical source-example replay for YBM V2 calibration.

This is a calibration report, not a hard pass/fail test. Exact historical KRX Amount
is unavailable in the long-history source, so historical trading value is estimated.
"""

import importlib.util
import json
from pathlib import Path

import FinanceDataReader as fdr

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("scan", ROOT / "scripts" / "longterm_scan.py")
scan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scan)
cfg = json.loads((ROOT / "longterm-scan-config.json").read_text(encoding="utf-8"))

CASES = [
    # source material: found as A-grade on 2026-09-09; used for repeated Jindol/Gadol examples
    {"code":"036540","name":"SFA반도체","date":"2026-09-09","expectedTrack":"LONG_HISTORY"},
    # source material: 2026-09-03, +16.47%, meaningful ~KRW100bn money, ABC/B-grade discussion
    {"code":"234690","name":"녹십자웰빙","date":"2026-09-03","expectedTrack":"LONG_HISTORY"},
    # source material: new listing, 2026-05-12 small ABC + Neomoneomo + small Jindol example
    {"code":"064400","name":"LG씨엔에스","date":"2026-05-12","expectedTrack":"NEW_LISTING"},
    # source material: KRW10,000 round figure + strong-candle/cloud breakout + rest/reacceleration example
    {"code":"012210","name":"삼미금속","date":"2026-09-10","expectedTrack":"LONG_HISTORY"},
]

rows = []
for case in CASES:
    start = "2022-01-01"
    end = case["date"]
    df = fdr.DataReader(case["code"], start, end)
    # FDR end can be exclusive in some readers; retry one calendar day later if needed.
    if df is None or len(df) == 0 or df.index[-1].strftime("%Y-%m-%d") < case["date"]:
        import datetime as dt
        d = dt.datetime.strptime(case["date"], "%Y-%m-%d").date() + dt.timedelta(days=1)
        df = fdr.DataReader(case["code"], start, d.isoformat())
    out = scan.analyze_frame(
        {"code":case["code"],"name":case["name"],"market":"","amount":None,"marcap":None},
        df,
        cfg,
    )
    assert out["status"] == "OK", (case, out)
    assert out["track"] == case["expectedTrack"], (case, out["track"])
    rows.append({
        "case": case["name"],
        "date": case["date"],
        "track": out["track"],
        "signal": out["signal"],
        "score": out["score"],
        "dayChangePct": out["dayChangePct"],
        "abc": out["abc"],
        "deoyangbong": out["deoyangbong"],
        "coreResistance": out["coreResistance"],
        "breakoutClass": out["breakoutClass"],
        "preJindol": out["preJindol"],
        "retestOk": out["retestOk"],
        "reacceleration": out["reacceleration"],
        "yangEumYang": out["yangEumYang"],
        "money": out["money"],
        "cloud": out["cloud"],
    })

print(json.dumps(rows, ensure_ascii=False, indent=2, default=scan.json_default))
