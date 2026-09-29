# YBM Method Audit

Status: CANONICAL METHOD TRACE
Updated: 2026-09-29
Purpose: keep the original YBM-based discovery logic distinguishable from later system enhancements.

## 1. Source-first principles

The scanner originated as an automation of the chart-selection workflow taught in the user's YBM source material. Later modules such as macro, revisions, catalysts, US lead price discovery, R/R and hard filters are overlays. They must not silently replace the source chart-selection logic.

Core source concepts reviewed:
- stock selection comes before entry timing;
- ABC = long decline -> long sideways/base -> C-stage recovery led by a strong MA600 breakout/N-wave;
- the source explicitly calls MA600 the hot-pink/pink line;
- MA1000 is another major long-term line; the text available to this audit does not explicitly equate the nickname "white line" to MA1000, so that nickname must not be hard-coded without stronger evidence;
- a strong reference candle normally needs both volume and trading value, with KRW 100bn taught as a minimum money reference and 10% accepted / 15% preferred for a strong bullish close;
- primary support/resistance comes from the strong reference candle's open/close, then previous highs/candle-density/round figures, then moving averages;
- "Neomoneomo" is a supply/support-resistance zone, not merely a fixed N-day high;
- Jindol is a money/volume-confirmed breakout; weak-money breakout is treated as Gadol risk;
- stronger source setups combine ABC, long-MA recovery, Ichimoku/cloud context, supply-zone digestion and Jindol rather than relying on one signal;
- chart alone is insufficient: company quality, material/catalyst, industry cycle and market context are additional puzzle pieces.

## 2. Implementation mapping

| Source concept | Current implementation | Audit status |
|---|---|---|
| A long decline | abc.aDeclinePct / abcMinDeclinePct | MATCH, threshold is implementation inference |
| B long base | abc.bRangePct + flat MA600 slope | MATCH, window/range thresholds are inference |
| C / hot-pink recovery | close above MA600 + C start detection | MATCH |
| Hot-pink | MA600 | EXACT SOURCE MAPPING |
| MA1000 long anchor | MA1000 fields / core resistance / entry support | MATCH |
| White-line nickname | not explicitly mapped | KEEP UNRESOLVED; do not invent |
| Strong reference candle | Deoyangbong proxy: return + trading value + volume + close location | MATCH / observable proxy |
| 10% possible, 15% preferred | deoyangbongMinReturnPct=10, preferred=15 | MATCH |
| KRW 100bn taught minimum | deoyangbong/jindol 100bn threshold | MATCH |
| Volume + trading value both matter | VOL_RATIO20 + tradingValue / ratio | MATCH |
| Reference-candle S/R priority | entry/support and core inputs | MATCH |
| Previous high / density / round figure | core resistance sources | MATCH |
| Neomoneomo | clustered supply/resistance zone | MATCH as proxy |
| Ichimoku context | cloud ABOVE/INSIDE/BELOW | MATCH |
| Jindol / Gadol | breakoutClass with money, volume, close acceptance, relative money | PARTIAL: raw breakout can qualify without full ABC/MA600/cloud confluence |
| Retest / supply drying | retestSupply + retestOk | MATCH as observable proxy |
| Reacceleration | retest + new high + money + close acceptance | MATCH as proxy |
| Yang-Eum-Yang | 3-candle observable rule | MATCH as proxy |
| Source S/A/B final quality | current chartGrade S/A/B_PLUS | NOT SAME THING: system chart-only structural grade |
| Company/material/cycle | downstream Company Quality, Revision, Catalyst, Macro modules | MATCH at system level, intentionally outside EOD chart scanner |
| First-wave / early-stage preference | ABC/C-stage + extension penalties | PARTIAL proxy; no subjective Elliott wave count is asserted |

## 3. Non-negotiable interpretation rules

1. Never call a stock "YBM A-grade" from chartGrade alone.
2. Display chartGrade as SYSTEM STRUCTURAL GRADE.
3. Every ATTACK/Radar candidate must expose observable evidence before interpretation.
4. Hot-pink may be named directly as MA600 because the source explicitly defines it.
5. "White line" remains UNRESOLVED_FROM_TEXT until an explicit source mapping is available; MA1000 may be shown by its actual name.
6. Jindol is a breakout-quality label. A separate YBM confluence state must show whether ABC/MA600/cloud/core-supply context also agrees.
7. Missing evidence remains UNKNOWN. Do not backfill narrative.
8. Hidden operator intent ("accumulation", "energy gathering", etc.) is not asserted as fact; use observable price/volume language.
9. Downstream Hard Filter/R/R may reject a good YBM structure, but must not rewrite the structural interpretation itself.
10. Preserve distinct source setup families instead of forcing every pattern into one score:
   - ABC_SWING_*: long-horizon/worker-friendly ABC and MA600 recovery track.
   - JINDOL_TACTICAL: money-confirmed breakout trading track even when full ABC confluence is absent.
   - ABC_JINDOL_CONFLUENCE: ABC + MA600 + cloud/supply context + Jindol overlap.
   A tactical Jindol must not be mislabeled as full ABC confluence, and a valid tactical Jindol must not be deleted merely because it is not full ABC.
11. SYSTEM STRUCTURAL GRADE is chart-only. Source-style final quality requires the downstream company/material/industry-cycle context; never present system S/A/B_PLUS as the teacher's final S/A/B grade.

## 4. Required trace chain

For every exposed scanner-derived candidate:

OBSERVED EVIDENCE
-> YBM SOURCE ALIGNMENT
-> SYSTEM STRUCTURAL GRADE
-> COMPANY QUALITY / CATALYST / REVISION
-> ENTRY READINESS / HARD FILTER
-> ACTION

This ordering is the audit contract. Later modules are overlays, not replacements for the original source method.


## 5. Market-structure study overlay

The 2026-09-29 chart-study canonical adds a separate observable market-structure layer. It is an overlay on the YBM discovery engine, not a replacement for it.

Implemented Phase 1 rules:
- keep **price level discovery** separate from **current role state**;
- a detected resistance zone remains `RESISTANCE` / `DECISION_ZONE` until close behavior changes its role;
- the first close above resistance is `BREAKOUT_PENDING`; repeated closes above it may become `ACCEPTED_SUPPORT`;
- unresolved resistance must not be reused as support/invalidation merely because its lower edge is below current price;
- intraday penetration followed by a close back below the zone is exposed as `UPPER_REJECTION` / `FAILED_BREAKOUT` without depending on the sign of the daily return;
- `HIGH_TREND_PRESSURE` is a parallel continuation **discovery/radar** track for established trends near highs with compression, rising lows and repeated upper tests;
- the continuation track is deliberately **not** an action-score bonus or automatic briefing trigger;
- high-distance measurements are supporting evidence only; a simple "within X% of a high" rule is forbidden.

Still restricted / not promoted to execution:
- box compression, spring/reclaim and box-breakout retest are implemented only as observable context; they do not create entries, action-score bonuses or briefing promotion;
- exact box window/width and box-close selection remain implementation proxies rather than source-mandated constants;
- trend-bridge close/wick levels are not yet automated;
- RSI divergence/strength is implemented only as price-first confirmation/warning context.

Any future promotion from observation to execution requires a generic, non-overfit regression contract first.

### RSI implementation guardrails
- RSI uses Wilder-style period 14 by default as an implementation parameter, not a source-mandated constant.
- RSI direction/slope and price-vs-RSI divergence are exposed as context only.
- RSI 70/30 never creates automatic buy/sell signals.
- RSI does not promote candidates, change actionScore, or override price structure.
- Divergence lookback, swing window and tolerances are implementation inference and must stay auditable in config.

### Box/spring implementation guardrails
- Box detection requires relative range compression versus a prior window plus repeated reactions near both boundaries.
- The detected box is an algorithmic proxy, not a claim that the source supplied a universal box length/width.
- Box high / low / final close are exposed as evidence; no automatic buy is created from box lower-bound contact.
- Spring is exposed only as an observed lower-bound breach and reclaim (`SPRING_RECLAIM_TODAY` / `SPRING_NEXT_BAR_RECLAIM`).
- Box/spring context does not change discovery, actionScore, or briefing eligibility.
- Post-breakout box-top / box-close retest states are now observed (`TOP_RETEST_HELD`, `DEEP_RETEST_CORE_HELD`, `BOX_CORE_FAILURE`), but they remain non-action context until separately validated for execution.
