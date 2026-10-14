"""Research-only pure order-intent planner. NOT connected to S01 or Production."""
from __future__ import annotations
from typing import Any

ENTER = {"ENTER", "ROTATE_IN"}
EXISTING = {"HOLD", "ADD", "REDUCE"}
VALID = ENTER | EXISTING


def plan_orders(
    positions: dict[str, float],
    prices: dict[str, float],
    desired: list[dict[str, Any]],
    equity: float,
) -> list[dict[str, float | str]]:
    """Return proposed *discretionary* review-close orders (no fills or costs).

    `positions` maps ID to shares. HOLD leaves the number of shares unchanged.
    Existing positions omitted from `desired` are complete exits.
    This pure prototype does not make stops, trades, or portfolio changes.
    """
    if equity <= 0:
        raise ValueError("equity must be positive")
    if any(shares < 0 for shares in positions.values()):
        raise ValueError("negative shares")
    targets: dict[str, dict[str, Any]] = {}
    allocation = 0.0
    for row in desired:
        aid = str(row["assetId"])
        if aid in targets:
            raise ValueError("duplicate assetId")
        action = str(row["action"])
        pct = float(row["capitalPct"])
        if action not in VALID or not 0 <= pct <= 100:
            raise ValueError("invalid action or capital percent")
        targets[aid] = row
        allocation += pct
    if allocation > 100 + 1e-9:
        raise ValueError("target weights sum to more than 100%")

    orders: list[dict[str, float | str]] = []

    def amount(aid: str, action: str, direction: str, shares: float) -> None:
        if shares > 1e-12:
            orders.append({"assetId": aid, "action": action, "side": direction,
                           "shares": shares, "notional": shares * float(prices[aid])})

    for aid, old_shares in positions.items():
        if old_shares > 0 and aid not in targets:
            if aid not in prices or prices[aid] <= 0:
                raise ValueError("price missing for exit")
            amount(aid, "EXIT", "SELL", old_shares)

    for aid, row in targets.items():
        if aid not in prices or float(prices[aid]) <= 0:
            raise ValueError("price missing")
        price = float(prices[aid])
        current_shares = float(positions.get(aid, 0))
        current_value = current_shares * price
        target_value = equity * float(row["capitalPct"]) / 100.0
        action = row["action"]
        if action in ENTER:
            if current_shares > 0:
                raise ValueError("ENTER/ROTATE_IN requires a new position")
            amount(aid, action, "BUY", target_value / price)
        elif action == "HOLD":
            if current_shares <= 0:
                raise ValueError("HOLD requires existing position")
            # No trade. Share count must remain unchanged despite weight drift.
        elif action == "ADD":
            if current_shares <= 0 or target_value <= current_value + 1e-8:
                raise ValueError("ADD requires increasing an existing position")
            amount(aid, action, "BUY", (target_value - current_value) / price)
        elif action == "REDUCE":
            if current_shares <= 0 or target_value >= current_value - 1e-8:
                raise ValueError("REDUCE requires decreasing an existing position")
            amount(aid, action, "SELL", min(current_shares, (current_value - target_value) / price))
    return orders
