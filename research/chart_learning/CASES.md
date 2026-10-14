# Chart study cases — evidence and mistakes

These are **research** observations and deliberately not instructions to buy. Exact observations must be checked against source data before trade execution.

## C-001 — Expert five-plan benchmark (DIAGNOSTIC, known levels)

Five *recommended*, not actually-filled, first/add/stop/target price plans were supplied as examples of quality:
- 에이피알 (278470), 2026-09-11: 352,000 / 301,000 / 289,000 / 426,600 / final 500,000.
- 삼화콘덴서 (001820), 2026-09-20: 139,000 / 118,300 / 98,900 / 172,500.
- 레메디 (387690), 2026-09-29: 22,300 / 18,750 / 17,760 / 34,650.
- 주성엔지니어링 (036930), 2026-10-06: 254,000 / 223,500 / 215,000 / 300,000.
- 인제니아테라퓨틱스 (950260), 2026-10-06: 23,000 / 20,050 / 18,650 / 35,000.

Positions in each row: first buy / second buy / stop / first target [/ final target]. 1:2 **money** sizing was a tentative user recollection, **not confirmed actual execution**. Reverse-engineered Fibonacci/exact matches were exposed to original prices and must NOT be called clean blind proof. The economic challenge is independently selecting stocks and coherent conditional pricing. See L-001, L-004.

## C-002 — V3 mechanical candidate stop mismatch (VERIFIED DIAGNOSTIC)

Source: repository 2026-10-13 `market-structure-v3-review-shard-*.json`.
- 비나텍: machine 75,303 reference, 74,923.5 invalidation, ~0.50% stop distance vs ~8.26% ATR. Also invalid KRX execution tick units.
- 에이치브이엠: 58,300 / 57,100, ~2.06% stop distance vs ~9.00% ATR.
- 루닛: 10,046.67 / 9,860, ~1.86% distance vs ~8.91% ATR and sub-tick raw reference.
- 뉴파워프라즈마: 13,280 / 8,450, ~36.37% distance vs ~7.38% ATR.

The conclusion is not that all tight stops are bad: **these machine-derived stops were not demonstrated to coincide with meaningful structural invalidation**, yet yield extraordinary numerical RR. A full swing/structure review is mandatory. See L-002, L-003.

## C-003 — Sep-18 retrospectively restricted cohort (DIAGNOSTIC; NOT BLIND)

Cutoff: 2026-09-18 after close. Available 2026-10-13-selected 33-stock review set was truncated to Sep-18. Screen required MA20>MA60, close>MA20, 20d momentum between +5% and +45%, price within 10% of 20d high, 5d momentum >= -5%, 5d relative volume >=0.6 and close-location >=0.35. **This filtering formula was decided during the analysis**, not validated independently.

Six passed: 에이치브이엠, LS에코에너지, 산일전기, KBI메탈, 비츠로테크, 메리츠금융지주. Three provisional plans:

| Name | First buy | Second buy | Stop | Target 1 | Final target |
| --- | ---: | ---: | ---: | ---: | ---: |
| 에이치브이엠 | 54,400 | 49,500 | 47,000 | 65,800 | 72,600 |
| LS에코에너지 | 53,400 | 49,000 | 46,600 | 64,800 | 74,000 |
| 산일전기 | 195,500 | 188,800 | 181,000 | 215,000 | 230,000 |

Outcome using 2026-09-21 through 2026-10-13 repository OHLCV (13 sampled sessions):
- 에이치브이엠 first buy touched on 9/29 (low 53,300); first target reached by 10/2 (high 70,200); final target crossed on 10/6 gap (open 77,800). Second buy never touched. Previously quoted simulated +27.21% assumes **one buy, half exiting at each target, ideal prices and excludes costs**. No real trading evidence; gap execution assumptions matter.
- LS에코에너지 first buy 53,400 not touched; later lowest 58,200; **no fill**.
- 산일전기 first buy 195,500 not touched; later lowest 199,600; **no fill**.

**DO NOT claim 1/3 win rate or proven positive edge**: selected-from-future cohort, no realistic intrabar execution audit, no independent full-market screen, no fee/cash drag, no genuine benchmark adjustment. See L-005, L-006.

## C-004 — Crash-session rejection is not a discovery benchmark

2026-10-13 10-stock review, zero approved buys in index stress. The result is valid as no-trade caution only. Test bullish/normal regimes separately and measure both false entries and missing strong winners. See L-008.

## C-005 — Three-session review cadence is NOT a three-session swing holding limit (CONFIG VERIFIED)

Source: `research/stock_blind/ACTIVE_EPISODE.json` and `scripts/stock_blind_walkforward.py` at 2026-10-14.
- Existing S01: `stepSessions: 3`; `episodeSessions: 30`.
- At every review, the assistant specifies portfolio actions (HOLD, ADD, REDUCE, EXIT/ROTATE); positions **persist across reviews** if retained. Stop logic runs across the intervening daily bars, including gap-below-stop handling.
- The episode produces a final **mark-to-market portfolio snapshot** after 30 sessions; it does not establish disposition of every open swing thesis and must not be called proof of multi-month skill.
- Assistant previously described each 3-session follow-up as if it were the swing result horizon. User corrected that swings can span weeks. **Never repeat this conflation**.
- Next controlled tests should include longer, independent evaluation episodes; record review cadence, thesis horizon and final status separately. Do not rewrite the existing S01 locked decisions to retroactively extend a winning holding period. See L-010, R-011.

## C-006 — Legacy S01 HOLD label silently rebalances portfolio weights (CODE VERIFIED / UNFIXED)

**Source:** `scripts/stock_blind_walkforward.py`, `replay()`, around lines 251–332 at git commit `a33da5e9e0e14f1c08627d18929a2ed4824d8053`.
- Each review builds a `target` keyed by `assetId`. For every existing asset, it computes `tgt_val = equity0 * capitalPct / 100` and sells `cur_val - tgt_val` when positive. For each desired target, it buys `tgt_val - cur_val` when positive.
- The quoted `action` is **only written as `lastAction`** and is not used to decide whether the buy/sell should occur. Hence even `action: HOLD` implicitly sells a winner after weight drift or adds to a loser until the target weight is restored.
- This can generate costs/turnover and adulterate the study's intended assessment of keeping strong multiweek swings. **Do not call it risk-adjusted HOLD skill evidence.** Conversely, S01's `capitalPct` *has* historically meant target weight; never silently reinterpret locked decisions or claim historical counterfactual equivalence.
- D04 review was locked at commit `a33da5e9...` while run `38508572523` was still in progress at this issue's discovery. Results after the commit were not inspected for this case.
- **Remedy:** document baseline simulator as LEGACY_REBALANCE; use `research/stock_blind/ORDER_SEMANTICS_V2.md` and its standalone `order_semantics_v2.py` prototype for a newly versioned experiment. Freeze new action semantics and test before opening future prices. Stop protection and gap logic remain separate concerns; prototype does not replace a full backtester. See L-011 / R-012.

## C-007 — S01 look-ahead from end-date-inclusive price source (CODE + CARD VERIFIED)

Source code: `scripts/stock_blind_walkforward.py`: `fetch_price` and `index_frame` send `end + 1 calendar day` to FDR and return the resulting frame **without filtering to end**. `scan_market(cutoff)` and `market_context(cutoff)` therefore may expose next-session bars; `CARD.futureIncluded=False` is a hard-coded assertion without evidence.

Reproducible actual S01 D05 mismatch, source `research/stock_blind/episodes/S01/state.json` vs freshly generated `current_card.json` after commit `8dfed3b3509ae16ad29566b503f706a71289e6df`:
- Locked state: A91ECD3412 currentPrice **18,810**; card held analysis price.close **19,000**.
- Locked state: A0E433D981 currentPrice **86,100**; card held analysis price.close **86,800**.
- Market context includes additional KOSPI close **2,470.41** after the legitimate relativeSession=15 close **2,447.43**; candidate daily traces show future-relative labels `T+1D`.
- State return +0.268% after D04 -0.325% and no stops; **these are *legacy* diagnostic replay figures, not valid clean blind evidence**. D04 was chosen before this discrepancy was discovered, but its own source card may likewise have included future prices.

Consequence: previous purported full-market blind S01 tests **cannot be declared blind**, even if decision commits were frozen, because their information set was potentially contaminated. The original dataset/results are preserved exactly as evidence, not silently repaired.

Remedy: fork separate S02, filter both stock and index frames to cutoff before analysis, add explicit held portfolio price parity and future candidate trace label checks. Test fake +1D leakage and intentionally failing held mismatch. Do not assert these fixes prove price-data vendor correctness or clean fundamentals; independent evaluation still required. See L-012 / R-013 / PROTOCOL_V2.md.

## Evidence provenance

- Existing EOD scanner artifacts: `market-structure-v3-review-index.json`, `market-structure-v3-review-shard-01.json` … `-33.json`, `v3-eod-deep-review.json`.
- Pre-existing assistant protocol: `ASSISTANT_CHART_DEEP_REVIEW_PROTOCOL.md`.
- Portfolio blind infrastructure: `research/stock_blind/PROTOCOL.md` and active episode; **different window**, cannot be represented as a 2026-09 verified blind result.

Preserve all adverse and non-fill examples on later revisions; correct with an appended erratum, never silently erase an embarrassment.
