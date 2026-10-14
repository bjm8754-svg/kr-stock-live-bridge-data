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

## Evidence provenance

- Existing EOD scanner artifacts: `market-structure-v3-review-index.json`, `market-structure-v3-review-shard-01.json` … `-33.json`, `v3-eod-deep-review.json`.
- Pre-existing assistant protocol: `ASSISTANT_CHART_DEEP_REVIEW_PROTOCOL.md`.
- Portfolio blind infrastructure: `research/stock_blind/PROTOCOL.md` and active episode; **different window**, cannot be represented as a 2026-09 verified blind result.

Preserve all adverse and non-fill examples on later revisions; correct with an appended erratum, never silently erase an embarrassment.
