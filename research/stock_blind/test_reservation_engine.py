#!/usr/bin/env python3
"""Offline executable contract tests for swing limit reservations (no market access)."""
import datetime as dt
import sys
import unittest
import pandas as pd

sys.path.insert(0, "research/stock_blind")
from reservation_engine import simulate

CFG = {"initialCapitalKrw": 100000, "buyCostBps": 5, "sellCostBps": 20, "stepSessions": 3}
DAYS = list(pd.date_range("2024-05-13", periods=7, freq="B").date)
CATALOG = {"A": {"code": "000001"}, "B": {"code": "000002"}}


def frame(opens, lows, highs=None, closes=None):
    if highs is None:
        highs = [max(a, b) + 3 for a, b in zip(opens, lows)]
    if closes is None:
        closes = [(o + l) / 2 for o, l in zip(opens, lows)]
    return pd.DataFrame({"Open": opens, "High": highs, "Low": lows,
                         "Close": closes, "Volume": [1000] * len(opens)},
                        index=pd.to_datetime(DAYS[:len(opens)]))


def entry(limit=100, stop=90, pct=30, order="O1", expiry=None, add=None):
    slices = [{"orderId": order, "kind": "FIRST", "limitPrice": limit,
               "capitalPct": pct}]
    if expiry is not None:
        slices[0]["expireAtSession"] = expiry
    if add:
        slices.append({"orderId": "O2", "kind": "ADD", "limitPrice": add, "capitalPct": 10})
    return {"assetId": "A", "action": "ENTER", "capitalPct": pct + (10 if add else 0),
            "stop": stop, "target": None, "buyOrders": slices}


def run(decisions, df, count=None):
    dates = DAYS[:count or (len(decisions) * 3 + 1)]
    return simulate(decisions, dates, CATALOG,
                    lambda meta, start, end: df, CFG)


class SwingReservationTests(unittest.TestCase):
    def test_reservation_no_fill_if_price_never_reaches_buy_price(self):
        df = frame([110, 113, 114, 115], [105, 105, 103, 102])
        r = run([{"step": 0, "portfolio": [entry()]}], df)
        self.assertEqual(r["positions"], [])
        self.assertEqual(r["turnoverKrw"], 0)
        self.assertEqual(len(r["pendingOrders"]), 1)
        self.assertAlmostEqual(r["equity"], 100000)

    def test_touch_only_without_penetration_is_not_assumed_filled(self):
        df = frame([110, 110, 110, 110], [105, 100, 100, 100])
        r = run([{"step": 0, "portfolio": [entry()]}], df)
        self.assertEqual(r["positions"], [])
        self.assertEqual(len(r["pendingOrders"]), 1)

    def test_trade_through_limit_fills_at_precommitted_price(self):
        df = frame([110, 108, 111, 112], [105, 99, 101, 102])
        r = run([{"step": 0, "portfolio": [entry()]}], df)
        x = r["positions"][0]
        self.assertGreater(x["avgEntry"], 100)
        self.assertLess(x["avgEntry"], 101)
        self.assertEqual(x["shares"], 299)
        self.assertEqual(r["pendingOrders"], [])
        self.assertEqual([e["event"] for e in r["orderEvents"] if "FILLED" in e["event"]], ["BUY_LIMIT_FILLED"])

    def test_gap_down_below_limit_above_stop_gets_price_improvement(self):
        df = frame([110, 97, 103, 108], [105, 96, 101, 103])
        r = run([{"step": 0, "portfolio": [entry()]}], df)
        e = next(e for e in r["orderEvents"] if e["event"] == "BUY_LIMIT_FILLED")
        self.assertEqual(e["fillPrice"], 97)

    def test_gap_below_invalidation_cancels_instead_of_buying(self):
        df = frame([110, 88, 95, 105], [105, 84, 91, 104])
        r = run([{"step": 0, "portfolio": [entry()]}], df)
        self.assertEqual(r["positions"], [])
        self.assertEqual(r["pendingOrders"], [])
        self.assertIn("CANCEL_GAP_BELOW_STOP", [e["event"] for e in r["orderEvents"]])

    def test_same_bar_entry_and_stop_counts_loss_not_fake_profit(self):
        df = frame([110, 110, 112, 112], [105, 88, 111, 111])
        r = run([{"step": 0, "portfolio": [entry()]}], df)
        events = [e["event"] for e in r["orderEvents"]]
        self.assertIn("BUY_LIMIT_FILLED", events)
        self.assertIn("STOP_SAME_DAY", events)
        self.assertLess(r["equity"], 100000)
        self.assertEqual(r["positions"], [])

    def test_pending_reservation_survives_three_session_review(self):
        df = frame([110, 110, 110, 110, 107, 108, 110],
                   [108, 105, 104, 103, 98, 102, 106])
        d = [{"step": 0, "portfolio": [entry()]}, {"step": 1, "portfolio": []}]
        r = run(d, df)
        ev = [x for x in r["orderEvents"] if x["event"] == "BUY_LIMIT_FILLED"]
        self.assertEqual(len(ev), 1)
        self.assertEqual(ev[0]["session"], 4)
        self.assertEqual(r["positions"][0]["lastAction"], "ENTER")

    def test_optional_second_buy_waits_for_first_and_needs_its_own_limit(self):
        df = frame([115, 112, 111, 111], [110, 98, 99, 105])
        d = [{"step": 0, "portfolio": [entry(limit=105, stop=90, pct=20, add=101)]}]
        r = run(d, df)
        orders = [e for e in r["orderEvents"] if e["event"] == "BUY_LIMIT_FILLED"]
        self.assertEqual([x["kind"] for x in orders], ["FIRST", "ADD"])
        self.assertEqual([x["fillPrice"] for x in orders], [105, 101])

    def test_add_not_filled_before_first(self):
        df = frame([115, 112, 111, 111], [110, 106, 108, 107])
        r = run([{"step": 0, "portfolio": [entry(limit=105, add=101)]}], df)
        self.assertEqual(r["positions"], [])
        self.assertEqual(len(r["pendingOrders"]), 2)

    def test_expiry_is_explicit_not_automatically_three_sessions(self):
        df = frame([110, 110, 110, 110], [105, 105, 104, 103])
        r = run([{"step": 0, "portfolio": [entry(expiry=2)]}], df)
        self.assertEqual(len(r["pendingOrders"]), 0)
        self.assertIn("CANCEL_EXPIRED", [e["event"] for e in r["orderEvents"]])

    def test_user_cancel_pending_order(self):
        df = frame([110, 110, 110, 110, 100, 99, 98],
                   [105, 105, 104, 103, 98, 97, 96])
        d = [{"step": 0, "portfolio": [entry()]},
             {"step": 1, "portfolio": [{"assetId": "A", "action": "CANCEL"}]}]
        r = run(d, df)
        self.assertFalse(r["pendingOrders"])
        self.assertFalse(r["positions"])
        self.assertIn("CANCEL_USER", [e["event"] for e in r["orderEvents"]])

    def test_hold_does_not_buy_or_trim_after_fill(self):
        df = frame([110, 108, 116, 116, 135, 137, 140],
                   [105, 99, 112, 112, 130, 133, 135])
        first = {"step": 0, "portfolio": [entry()]}
        hold = {"step": 1, "portfolio": [{"assetId": "A", "action": "HOLD",
                                             "capitalPct": 30, "stop": 90}]}
        r0 = run([first], df)
        r1 = run([first, hold], df)
        self.assertAlmostEqual(r0["turnoverKrw"], r1["turnoverKrw"])
        self.assertEqual(r0["positions"][0]["shares"], r1["positions"][0]["shares"])

    def test_rejects_missing_limit_or_invalid_stop(self):
        df = frame([110, 105, 102, 101], [105, 100, 100, 99])
        invalid = {"assetId": "A", "action": "ENTER", "capitalPct": 30, "stop": 90,
                   "entryReference": 100}
        with self.assertRaisesRegex(ValueError, "explicit buyOrders"):
            run([{"step": 0, "portfolio": [invalid]}], df)
        with self.assertRaisesRegex(ValueError, "invalid structural limit"):
            run([{"step": 0, "portfolio": [entry(limit=100, stop=105)]}], df)


if __name__ == "__main__":
    unittest.main()
