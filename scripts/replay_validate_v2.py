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
    {"code":"036540","name":"CASE_A","date":"2026-09-09","expectedTrack":"LONG_HISTORY","sourceLabel":"A_GRADE","sourceDiscoveryFloor":"B_PLUS"},
    # source-derived calibration case: long-MA recovery with strong money expansion
    {"code":"234690","name":"CASE_B","date":"2026-09-03","expectedTrack":"LONG_HISTORY","sourceLabel":"B_GRADE"},
    # source-derived calibration case: new-listing mini-structure
    {"code":"064400","name":"CASE_C","date":"2026-05-12","expectedTrack":"NEW_LISTING"},
    # source-derived calibration case: reference candle -> controlled rest -> follow-through
    {"code":"012210","name":"CASE_D","date":"2026-09-10","expectedTrack":"LONG_HISTORY","sourceLabel":"YANG_EUM_YANG_REVIEW"},
    # source-labeled A-grade example from the 2026-09-03 review
    {"code":"441270","name":"CASE_E","date":"2026-09-03","sourceLabel":"A_GRADE","sourceDiscoveryFloor":"B_PLUS"},
    # source-labeled B+ trading example from the same review
    {"code":"053260","name":"CASE_F","date":"2026-09-03","sourceLabel":"B_PLUS_TRADING","sourceDiscoveryFloor":"B_PLUS"},
    # historical source labels used only as calibration controls, never as ranking memory
    {"code":"161890","name":"CASE_G","date":"2026-07-02","sourceLabel":"A_GRADE","sourceDiscoveryFloor":"B_PLUS"},
    {"code":"001820","name":"CASE_H","date":"2026-05-20","sourceLabel":"A_GRADE","sourceDiscoveryFloor":"B_PLUS"},
    {"code":"126340","name":"CASE_I","date":"2026-09-16","sourceLabel":"B_PLUS","sourceDiscoveryFloor":"B_PLUS"},
    # explicit negative calibration: source says pattern fit but volume/money were insufficient, so not A-grade
    {"code":"066980","name":"CASE_J","date":"2026-05-20","sourceLabel":"NOT_A_LOW_MONEY","sourceMaxChartGrade":"B_PLUS"},
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
    if case.get("expectedTrack"):
        assert out["track"] == case["expectedTrack"], (case, out["track"])
    chart_grade = scan.compute_chart_grade(out, cfg)
    action_score = scan.compute_action_score(out, cfg)
    grade_rank = {"BELOW_B_PLUS": 0, "B_PLUS": 1, "A": 2, "S": 3}
    expected_grade = case.get("sourceDiscoveryFloor")
    max_grade = case.get("sourceMaxChartGrade")
    if expected_grade:
        source_alignment = (
            "MATCH"
            if grade_rank.get(chart_grade.get("grade"), -1) >= grade_rank[expected_grade]
            else "MISMATCH"
        )
    else:
        source_alignment = "NOT_ASSERTED"

    if max_grade:
        source_max_alignment = (
            "MATCH"
            if grade_rank.get(chart_grade.get("grade"), -1) <= grade_rank[max_grade]
            else "MISMATCH"
        )
    else:
        source_max_alignment = "NOT_ASSERTED"

    rows.append({
        "case": case["name"],
        "code": case["code"],
        "sourceLabel": case.get("sourceLabel"),
        "sourceDiscoveryFloor": expected_grade,
        "sourceDiscoveryAlignment": source_alignment,
        "sourceMaxChartGrade": max_grade,
        "sourceMaxAlignment": source_max_alignment,
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
