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
    # source-derived calibration case: long-history breakout-quality example
    {"code":"036540","name":"CASE_A","date":"2026-09-09","expectedTrack":"LONG_HISTORY"},
    # source-derived calibration case: long-MA recovery with strong money expansion
    {"code":"234690","name":"CASE_B","date":"2026-09-03","expectedTrack":"LONG_HISTORY"},
    # source-derived calibration case: new-listing mini-structure
    {"code":"064400","name":"CASE_C","date":"2026-05-12","expectedTrack":"NEW_LISTING"},
    # source-derived calibration case: reference candle -> controlled rest -> follow-through
    {"code":"012210","name":"CASE_D","date":"2026-09-10","expectedTrack":"LONG_HISTORY"},
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
    chart_grade = scan.compute_chart_grade(out, cfg)
    action_score = scan.compute_action_score(out, cfg)
    rows.append({
        "case": case["name"],
        "code": case["code"],
        "date": case["date"],
        "track": out["track"],
        "signal": out["signal"],
        "score": out["score"],
        "close": out["close"],
        "dayChangePct": out["dayChangePct"],
        "chartGrade": chart_grade,
        "qualified": scan.is_qualified_candidate(out, cfg),
        "actionScore": action_score,
        "entryPlan": out["entryPlan"],
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
