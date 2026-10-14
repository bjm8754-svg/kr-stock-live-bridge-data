#!/usr/bin/env python3
"""Pure, offline temporal and action gate tests. No external price/network access."""
import datetime as dt
import importlib.util
import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path("scripts")))
spec = importlib.util.spec_from_file_location("stock_blind_v2_test", "scripts/stock_blind_walkforward_v2.py")
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


class PointInTimeV2Tests(unittest.TestCase):
    def test_source_with_inclusive_extra_day_is_clipped(self):
        dates = pd.to_datetime(["2024-05-13", "2024-05-14", "2024-05-15", "2024-05-16"])
        df = pd.DataFrame({"Close": [100, 105, 110, 999]}, index=dates)
        out = mod.enforce_asof(df, dt.date(2024, 5, 15))
        self.assertEqual(len(out), 3)
        self.assertEqual(float(out.iloc[-1]["Close"]), 110)
        self.assertFalse(any(out.index.date > dt.date(2024, 5, 15)))

    def test_held_price_behind_fresh_card_rejects_future_leak(self):
        x = {"futureIncluded": False, "step": 5,
             "portfolioState": {"positions": [{"assetId": "A1", "currentPrice": 18810}]},
             "heldPositionAnalysis": [{"assetId": "A1", "price": {"close": 19000}}],
             "deepReviewCandidates": []}
        with self.assertRaisesRegex(RuntimeError, "PIT_HELD_PRICE_MISMATCH"):
            mod.verify_pit_card(x, dt.date(2024, 5, 15))

    def test_calendar_trace_label_t_plus_one_rejected(self):
        x = {"futureIncluded": False, "step": 5, "portfolioState": {"positions": []},
             "heldPositionAnalysis": [],
             "deepReviewCandidates": [{"assetId": "A2", "price": {"close": 110},
               "review": {"chartTrace": {"daily": [["T+1D", 100, 110, 90, 110]]}}}]}
        with self.assertRaisesRegex(RuntimeError, "PIT_FUTURE_TRACE_LABEL"):
            mod.verify_pit_card(x, dt.date(2024, 5, 15))

    def test_clean_card_held_and_candidate_pass(self):
        x = {"futureIncluded": False, "step": 5,
             "portfolioState": {"positions": [{"assetId": "A1", "currentPrice": 18810}]},
             "heldPositionAnalysis": [{"assetId": "A1", "price": {"close": 18810}}],
             "deepReviewCandidates": [{"assetId": "A2", "price": {"close": 110},
               "review": {"chartTrace": {"daily": [["T+0D", 100, 110, 90, 110]]}}}]}
        self.assertTrue(mod.verify_pit_card(x, dt.date(2024, 5, 15)))

    def test_no_same_close_fill_after_close_decision(self):
        """An ex-ante signal on close 100 can fill only at next-day open 120."""
        import pandas as pd
        dates = [dt.date(2024, 5, d) for d in (13, 14, 15, 16)]
        df = pd.DataFrame({
            "Open": [100, 120, 110, 111],
            "High": [102, 125, 115, 115],
            "Low": [99, 108, 106, 107],
            "Close": [100, 110, 111, 112],
            "Volume": [1000] * 4,
        }, index=pd.to_datetime(dates))
        orig = mod.fetch_price
        mod.fetch_price = lambda *args, **kwargs: df
        try:
            dec = {"step": 0, "portfolio": [{"assetId": "A", "action": "ENTER",
                   "capitalPct": 20.0, "stop": None, "target": None}]}
            rep = mod.replay([dec], dates, {"A": {"code": "123456", "source": "CURRENT"}})
            pos = rep["positions"][0]
            self.assertGreater(pos["avgEntry"], 120)
            self.assertLess(pos["avgEntry"], 121)
            self.assertEqual(round(rep["turnoverKrw"], 0), 1999920)
            self.assertGreater(rep["intervals"][0]["postTradeEquityKrw"], 0)
        finally:
            mod.fetch_price = orig

    def test_hold_does_not_rebalance_after_next_open(self):
        dates = [dt.date(2024, 5, d) for d in (13, 14, 15, 16, 17, 20, 21)]
        df = pd.DataFrame({
            "Open": [100, 120, 110, 111, 150, 151, 152],
            "High": [102, 125, 115, 115, 152, 154, 155],
            "Low": [99, 108, 106, 107, 145, 145, 149],
            "Close": [100, 110, 111, 112, 150, 152, 154],
            "Volume": [1000] * 7,
        }, index=pd.to_datetime(dates))
        orig = mod.fetch_price
        mod.fetch_price = lambda *args, **kwargs: df
        try:
            enter = {"step": 0, "portfolio": [{"assetId": "A", "action": "ENTER",
                     "capitalPct": 20.0, "stop": None, "target": None}]}
            hold = {"step": 1, "portfolio": [{"assetId": "A", "action": "HOLD",
                    "capitalPct": 20.0, "stop": None, "target": None}]}
            rep_first = mod.replay([enter], dates, {"A": {"code": "123456"}})
            rep_second = mod.replay([enter, hold], dates, {"A": {"code": "123456"}})
            self.assertAlmostEqual(rep_first["turnoverKrw"], rep_second["turnoverKrw"])
            self.assertEqual(rep_second["positions"][0]["lastAction"], "HOLD")
        finally:
            mod.fetch_price = orig


if __name__ == "__main__":
    unittest.main()
