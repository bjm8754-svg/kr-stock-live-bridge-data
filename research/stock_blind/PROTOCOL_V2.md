# S02 — strict-HOLD, point-in-time blind swing research

Status: ISOLATED NEW EXPERIMENT / NO PRODUCTION, NO REAL ORDERS
Engine source: `scripts/stock_blind_walkforward_v2.py` + `scripts/stock_blind_runner_v2.py`
Active configuration: `research/stock_blind/ACTIVE_EPISODE_V2.json`
Episode: `S02`, 60 trading sessions, 3-session *review cadence* (NOT forced holding period).
Decision input: `research/stock_blind/episodes/S02/decisions/Dxx.json` — append only, locked before next card.
Action semantics: `research/stock_blind/ORDER_SEMANTICS_V2.md`; a genuine HOLD has zero discretionary order quantity.
Security master: still reconstructed from current + historically delisted KRX (not exchange-certified point-in-time feed).
Required verified data guard:
1. Every raw stock/index frame clipped to index calendar date <= hidden cutoff BEFORE scanning, indicators, chart traces, sentiment or decision exposure. Inclusive provider end-date bugs must not leak tomorrow's bars.
2. After building the card, **cross-check exact held-position closing prices** against end-of-interval portfolio state; if mismatched, fail closed.
3. Inspect candidate daily relative-date labels and reject `T+1D` etc. The monthly/weekly bars may legitimately use future *period-end labels* for partial in-progress buckets, but can only contain underlying clipped daily observations.
4. Run offline synthetics testing a +1d bar leak and held-price mismatch, plus strict-HOLD order-intent unit tests before costly market scan.
5. Never equate `futureIncluded:false` alone with verified point-in-time correctness.

Legacy S01 remains untouched and flagged **CONTAMINATED / LEGACY_REBALANCE** due to future-priced D05 raw analysis card and forced weight rebalancing; no S01 edge demonstrated. Do not treat current_cards derived from stale S01 `current_card_decision_table.json` or `current_details` as current; the authoritative card is `current_card.json` with matching `step` and price-state alignment.

S02 will still lack fully point-in-time news, institutional sentiment, analyst revisions, broker live fills and exchange-certified listing history. The new tests establish crucial invariants, **not proven investment skill or complete temporal validity of all external data**. The first run should generate masked S02 D00 card from the full historical universe; decisions and outcomes remain locked in order. This protocol is a new versioned research study, not a rewrite of S01.

## Swing entry model — precommitted LIMIT reservations (binding before S02 D00)

**The assistant's job is to determine the price worth paying, not to buy tomorrow's opening price.** After a cutoff-close analysis, independently precommit first-buy price, optional second-buy price, structural stop, suitable target or trend exit premise, sizing, and per-order cancellation/expiry. The system places a **simulation-only reservation**, never a real brokerage order.

Use `portfolio[].action = "ENTER"` or `"ROTATE_IN"` with an explicit `buyOrders` list; each item has unique `orderId`, `kind: "FIRST"` or `"ADD"`, `limitPrice`, `capitalPct` and optional explicit `expireAtSession`. `stop` is mandatory, and must be structurally below the reserved buy limit. Omit ADD entirely unless a separately defensible price exists. `capitalPct` inside each tranche is a cash budget **frozen at the decision**, not a rebalanced portfolio target. A prospective ADD waits until FIRST is actually filled. Unfilled FIRST/ADD orders are shown in `state.pendingOrders` and `current_card.portfolioState.pendingOrders` and do not count as invested or profitable.

**Order lifespan is independent of review cadence.** Orders stay pending across every 3-session review unless filled, explicitly canceled with `action:"CANCEL"`, invalidated by a gap below stop, or expire at an explicit `expireAtSession`. A `KEEP_PENDING` action can reaffirm an unfilled order. An omitted pending order continues to wait (it is not a market purchase or automatic cancellation); an omitted *held* position still implies an EXIT per v2 complete-portfolio convention. Explicit sell/REDUCE choices are settled at next session open; that does not authorize market-buying.

**Conservative OHLC execution:** A limit buy is eligible only on a *later* session where open <= limit (fill at open if above stop) or where the daily low **penetrates below** the limit (fill at limit; exact touch without penetration is treated as queue-uncertain nonfill). Opening below stop cancels the reservation; if a new fill and its structural stop trade on the same daily bar, count the stopped-out loss, not the winner. Existing held stops are honored before new adds when intrabar chronology is unknown. Simulation uses whole shares and buy/sell cost assumptions. Resting orders' combined budget plus fees cannot exceed free cash. This still assumes complete fills once price passes limit; **true order-book depth, queues, liquidity limits, halts, slippage, splits and adjusted data remain unverified**.

The initial historical 60-session S02 card was created before any D00 decision. Prior GitHub code briefly introduced a next-session-open **buy** approximation; it has been discarded **before any S02 trade decision was locked**. S01 remains quarantined. All subsequent S02 trades must use only these reserved buy conditions.

### Example schema (not a live signal)

```json
{"step":0,"portfolio":[{"assetId":"A_EXAMPLE","action":"ENTER","stop":9000,"target":null,"buyOrders":[{"orderId":"S02-EX-1","kind":"FIRST","limitPrice":10000,"capitalPct":12,"expireAtSession":15},{"orderId":"S02-EX-2","kind":"ADD","limitPrice":9500,"capitalPct":6,"expireAtSession":15}]}],"cashPct":100}
```
