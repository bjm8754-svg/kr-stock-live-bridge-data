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

    def test_resting_order_requires_independent_current_chart(self):
        card = {"futureIncluded": False, "step": 1,
                "portfolioState": {"positions": [], "pendingOrders": [{"assetId": "A_PENDING"}]},
                "heldPositionAnalysis": [], "deepReviewCandidates": [],
                "pendingOrderAnalysis": []}
        with self.assertRaisesRegex(RuntimeError, "PIT_PENDING_ANALYSIS_MISSING"):
            mod.verify_pit_card(card, dt.date(2024, 5, 15))

    def test_resting_order_current_price_must_match_cutoff_trace(self):
        card = {"futureIncluded": False, "step": 1,
                "portfolioState": {"positions": [], "pendingOrders": [{"assetId": "A_PENDING"}]},
                "heldPositionAnalysis": [], "deepReviewCandidates": [],
                "pendingOrderAnalysis": [{"assetId": "A_PENDING",
                    "price": {"close": 105},
                    "priceAsOfOffsetCalendarDays": 0,
                    "chartTrace": {"daily": [[0, 100, 110, 90, 110, 1.0]]}}]}
        with self.assertRaisesRegex(RuntimeError, "PIT_PENDING_PRICE_MISMATCH"):
            mod.verify_pit_card(card, dt.date(2024, 5, 15))

    def test_resting_order_independent_chart_passes(self):
        card = {"futureIncluded": False, "step": 1,
                "portfolioState": {"positions": [], "pendingOrders": [{"assetId": "A_PENDING"}]},
                "heldPositionAnalysis": [], "deepReviewCandidates": [],
                "pendingOrderAnalysis": [{"assetId": "A_PENDING",
                    "price": {"close": 105},
                    "priceAsOfOffsetCalendarDays": 0,
                    "chartTrace": {"daily": [[0, 100, 110, 90, 105, 1.0]]}}]}
        self.assertTrue(mod.verify_pit_card(card, dt.date(2024, 5, 15)))

    def test_clean_card_held_and_candidate_pass(self):
        x = {"futureIncluded": False, "step": 5,
             "portfolioState": {"positions": [{"assetId": "A1", "currentPrice": 18810}]},
             "heldPositionAnalysis": [{"assetId": "A1", "price": {"close": 18810}}],
             "deepReviewCandidates": [{"assetId": "A2", "price": {"close": 110},
               "review": {"chartTrace": {"daily": [["T+0D", 100, 110, 90, 110]]}}}]}
        self.assertTrue(mod.verify_pit_card(x, dt.date(2024, 5, 15)))



if __name__ == "__main__":
    unittest.main()
