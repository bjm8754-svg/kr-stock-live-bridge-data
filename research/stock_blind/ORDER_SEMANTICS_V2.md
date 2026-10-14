# S02+ research-only order semantics prototype (NOT LIVE)

**Scope:** isolated order-intent planning and offline unit tests. Do not wire into running S01, pre-existing locked decisions, scanning pipelines or Production. No historical or live data downloaded by these tests.

## Why

Legacy `scripts/stock_blind_walkforward.py` always rebalances to `capitalPct`, even for an action labelled HOLD. This produces buys/sells without discretionary ADD/REDUCE instructions, potentially inflating turnover and distorting evaluation of multi-week swing judgement. Preserve S01 as legacy baseline.

## Future versioned semantics (proposal, independently tested for order intent only)

1. `HOLD` on an **existing** position: 0 discretionary shares bought and 0 sold, irrespective of natural market-value-weight drift. Structural stop updates are independent and continue daily.
2. `ENTER` on a **new** position: create a **BUY_LIMIT reservation** at the assistant's precommitted first-buy price (not a market buy or filled review close). The former pure `order_semantics_v2.py` planner only tests intention direction and is **not used by the new S02 replay**. See `reservation_engine.py` and `test_reservation_engine.py` for fill and persistence semantics.
3. `ADD` on existing position: schedule an **explicit BUY_LIMIT** at the new independently justified price, or place a conditional second reservation along with FIRST. It does not execute until its limit is tradable and the first position exists.
4. `REDUCE` on existing position: sell only a positive delta to the explicitly reduced target percent. Never use `REDUCE` to buy.
5. Existing position absent from target list: explicit full EXIT / ROTATE_OUT, retaining exit audit reason.
6. `ROTATE_IN`: open a newly selected position like ENTER.
7. Invalid actions, duplicate IDs, negative sizes, overallocated targets, missing prices or action-position mismatches cause hard errors; no silent fallback.
8. `capitalPct` on HOLD remains **informational / risk upper bound if separately specified**; it does not override immutable shares. Report current drifting weight separately.
9. The isolated v2 full simulator now checks whole-share reservation fills, stop and gap logic, basic transaction costs and cash exposure. True order-book depth, participation limits, slippage, actual corporate actions and historical adjusted-tick validity remain unknown. The old order-intent prototype does NOT claim to implement realistic fill mechanics.

## Stage-gate

The prototype below is NOT a working correction of the legacy replay engine. Full validation requires a fresh versioned episode: frozen data/universe, chronology and decisions, cost-adjusted portfolio simulator, risk-check guards, no lookahead, explicit executed versus missed trades, and several-week/multi-month outcomes. S01 30-session results must continue to be called **LEGACY_REBALANCE_METHODOLOGY**.
