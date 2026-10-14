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
