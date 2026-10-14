#!/usr/bin/env python3
"""Offline order semantics v2 tests. NOT a production or historical PnL test."""
import unittest
from order_semantics_v2 import plan_orders


def row(aid, action, pct):
    return {"assetId": aid, "action": action, "capitalPct": pct}


class OrderContractTests(unittest.TestCase):
    def test_hold_does_not_trim_winner_even_if_weight_has_risen(self):
        self.assertEqual(plan_orders({"A": 100}, {"A": 120}, [row("A", "HOLD", 20)], 50000), [])

    def test_hold_does_not_top_up_loser_even_if_weight_has_fallen(self):
        self.assertEqual(plan_orders({"A": 100}, {"A": 80}, [row("A", "HOLD", 30)], 50000), [])

    def test_enter_opens_new(self):
        x = plan_orders({}, {"A": 100}, [row("A", "ENTER", 20)], 100000)
        self.assertEqual((x[0]["side"], x[0]["shares"]), ("BUY", 200))

    def test_add_only_buys_explicit_increase(self):
        x = plan_orders({"A": 100}, {"A": 100}, [row("A", "ADD", 20)], 100000)
        self.assertEqual((x[0]["side"], x[0]["shares"]), ("BUY", 100))

    def test_reduce_only_sells_explicit_decrease(self):
        x = plan_orders({"A": 150}, {"A": 100}, [row("A", "REDUCE", 10)], 100000)
        self.assertEqual((x[0]["side"], x[0]["shares"]), ("SELL", 50))

    def test_absent_holding_exits(self):
        x = plan_orders({"A": 100}, {"A": 120}, [], 100000)
        self.assertEqual((x[0]["action"], x[0]["shares"]), ("EXIT", 100))

    def test_rejects_actions_with_wrong_position_state(self):
        with self.assertRaises(ValueError):
            plan_orders({}, {"A": 100}, [row("A", "HOLD", 20)], 100000)
        with self.assertRaises(ValueError):
            plan_orders({"A": 100}, {"A": 100}, [row("A", "ENTER", 20)], 100000)
        with self.assertRaises(ValueError):
            plan_orders({"A": 100}, {"A": 100}, [row("A", "ADD", 5)], 100000)
        with self.assertRaises(ValueError):
            plan_orders({"A": 100}, {"A": 100}, [row("A", "REDUCE", 20)], 100000)

    def test_invalid_weight_duplicate_and_missing_prices(self):
        for desired in [[row("A", "ENTER", 60), row("B", "ENTER", 60)], [row("A", "ENTER", 10), row("A", "ENTER", 20)]]:
            with self.assertRaises(ValueError):
                plan_orders({}, {"A": 100, "B": 100}, desired, 100000)
        with self.assertRaises(ValueError):
            plan_orders({}, {}, [row("A", "ENTER", 10)], 100000)


if __name__ == "__main__":
    unittest.main()
