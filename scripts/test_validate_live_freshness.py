#!/usr/bin/env python3
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_live_freshness.py"
DATE = "20260923"


def stock(price, volume, value, status="OPEN", source_date="2026-09-23"):
    return {
        "currentPrice": price,
        "volume": volume,
        "tradingValue": value,
        "marketStatus": status,
        "nxtOverMarketPriceInfo": {
            "localTradedAt": f"{source_date}T09:00:00+09:00"
        },
    }


def build_case(codes, rows, watch_date=DATE, live_date=DATE):
    return {
        "live": {
            "tradeDate": live_date,
            "publishedAtKst": "2026-09-23 09:40:01.000 KST",
            "watchlist": codes,
            "history": {
                "count": len(rows),
                "from": rows[0]["atKst"] if rows else None,
                "to": rows[-1]["atKst"] if rows else None,
                "rows": rows,
            },
            "scan": {
                "status": "PASS",
                "turnoverTop": [{"code":"000001","tradingValue":1000}],
                "risingLiquid": [{"code":"000001","changePct":1.0}],
            },
            "scanDelta": {
                "comparedCount": 1,
                "turnoverAcceleration": [{"code":"000001","deltaTradingValue":100}],
            },
        },
        "watch": {"tradeDate": watch_date, "codes": codes},
    }


def run_validator(case):
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        live = td / "live.json"
        watch = td / "watchlist.json"
        out = td / "live-health.json"
        live.write_text(json.dumps(case["live"]), encoding="utf-8")
        watch.write_text(json.dumps(case["watch"]), encoding="utf-8")
        subprocess.run(
            [
                "python",
                str(VALIDATOR),
                "--live",
                str(live),
                "--watchlist",
                str(watch),
                "--output",
                str(out),
                "--asof-date",
                DATE,
            ],
            check=True,
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        return json.loads(out.read_text(encoding="utf-8"))


class LiveFreshnessTests(unittest.TestCase):
    def test_normal_open_dynamic_passes(self):
        codes = ["000001", "000002"]
        rows = []
        for minute in range(3):
            rows.append({
                "atKst": f"{DATE} 090{minute}",
                "stocks": {
                    "000001": stock(1000 + minute, 100 + minute, 1000 + minute),
                    "000002": stock(2000, 200 + minute, 2000 + minute),
                },
            })
        out = run_validator(build_case(codes, rows))
        self.assertEqual(out["status"], "PASS")
        self.assertEqual(out["reasons"], [])

    def test_minority_frozen_name_does_not_fail(self):
        codes = ["000001", "000002"]
        rows = []
        for minute in range(3):
            rows.append({
                "atKst": f"{DATE} 090{minute}",
                "stocks": {
                    "000001": stock(1000, 100 + minute, 1000 + minute),
                    "000002": stock(2000, 200, 2000),
                },
            })
        out = run_validator(build_case(codes, rows))
        self.assertEqual(out["status"], "PASS")

    def test_low_dynamic_open_market_is_warning_only(self):
        codes = ["000001", "000002", "000003"]
        rows = []
        for minute in range(3):
            rows.append({
                "atKst": f"{DATE} 090{minute}",
                "stocks": {
                    "000001": stock(1000, 100 + minute, 1000 + minute),
                    "000002": stock(2000, 200, 2000),
                    "000003": stock(3000, 300, 3000),
                },
            })
        out = run_validator(build_case(codes, rows))
        self.assertEqual(out["status"], "PASS")
        self.assertIn("LOW_INTRADAY_CHANGE", out["warnings"])

    def test_stale_aux_timestamp_is_warning_when_main_payload_live(self):
        codes = ["000001", "000002"]
        rows = []
        for minute in range(3):
            rows.append({
                "atKst": f"{DATE} 090{minute}",
                "stocks": {
                    "000001": stock(1000, 100 + minute, 1000 + minute, source_date="2026-09-22"),
                    "000002": stock(2000, 200 + minute, 2000 + minute, source_date="2026-09-22"),
                },
            })
        out = run_validator(build_case(codes, rows))
        self.assertEqual(out["status"], "PASS")
        self.assertIn("STALE_AUX_SOURCE_TIMESTAMP", out["warnings"])

    def test_closed_frozen_payload_fails_closed(self):
        codes = ["000001", "000002"]
        rows = []
        for minute in range(3):
            rows.append({
                "atKst": f"{DATE} 090{minute}",
                "stocks": {
                    "000001": stock(1000, 100, 1000, status="CLOSE", source_date="2026-09-22"),
                    "000002": stock(2000, 200, 2000, status="CLOSE", source_date="2026-09-22"),
                },
            })
        out = run_validator(build_case(codes, rows))
        self.assertEqual(out["status"], "FAIL")
        for reason in (
            "FROZEN_HISTORY",
            "MARKET_STATUS_CLOSED_OR_STALE",
            "INSUFFICIENT_INTRADAY_CHANGE",
            "STALE_SOURCE_TIMESTAMP",
        ):
            self.assertIn(reason, out["reasons"])

    def test_missing_scan_is_warning_only(self):
        codes = ["000001", "000002"]
        rows = []
        for minute in range(36):
            rows.append({
                "atKst": f"{DATE} 09{minute:02d}",
                "stocks": {
                    "000001": stock(1000 + minute, 100 + minute, 1000 + minute),
                    "000002": stock(2000 + minute, 200 + minute, 2000 + minute),
                },
            })
        case = build_case(codes, rows)
        case["live"].pop("scan", None)
        case["live"].pop("scanDelta", None)
        out = run_validator(case)
        self.assertEqual(out["status"], "PASS")
        self.assertIn("MARKET_SCAN_MISSING", out["warnings"])
        self.assertIn("SCAN_DELTA_MISSING", out["warnings"])

    def test_watchlist_date_mismatch_fails(self):
        codes = ["000001"]
        rows = [
            {"atKst": f"{DATE} 0900", "stocks": {"000001": stock(1000, 100, 1000)}},
            {"atKst": f"{DATE} 0901", "stocks": {"000001": stock(1001, 101, 1001)}},
        ]
        out = run_validator(build_case(codes, rows, watch_date="20260922"))
        self.assertEqual(out["status"], "FAIL")
        self.assertIn("WATCHLIST_TRADE_DATE_MISMATCH", out["reasons"])


if __name__ == "__main__":
    unittest.main()
