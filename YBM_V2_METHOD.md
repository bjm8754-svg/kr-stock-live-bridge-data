# YBM Swing V2 Methodology Specification

## Scope
This is a machine-readable interpretation of the source material supplied in the conversation. It is designed to replace manual HTS chart-sweep work, not to reproduce hidden intent. The scanner classifies observable price, volume, trading value, long moving averages, Ichimoku cloud, support/resistance, acceptance and follow-through.

## Source-derived concepts
- ABC: long decline (A) -> long base/congestion (B) -> long-MA recovery with an N-wave style advance (C).
- Long-term anchors: MA240 as an earlier recovery clue; MA480, MA600 (hot-pink), MA1000 (white-line) as long-term structure.
- Strong bullish reference candle ("더양봉"): large bullish candle with meaningful volume and trading value. Its open/close are primary support/resistance evidence.
- Secondary support/resistance: prior highs, candle-density/congestion, round figures, then moving averages.
- Neomoneomo: a supply/congestion zone between meaningful support/resistance levels, not a fixed N-day-high box.
- Jindol: meaningful resistance/supply breakout with both volume and trading value expansion.
- Gadol: price breakout without sufficient money/volume confirmation, or with materially weaker confirmation than the relevant prior reference move.
- KRW 100bn is the taught minimum trading-value reference; KRW 300bn is treated as very strong. These are references, not universal laws.
- Ichimoku cloud is overhead supply/resistance; clearing it strengthens the setup, while failure to clear it can mean more digestion is needed rather than automatic rejection.
- Yang-Eum-Yang: strong bullish reference candle -> controlled rest/negative candle -> renewed bullish move.
- New listings can be evaluated without MA600 using a strong reference candle, mini-base, supply zone and real/weak breakout logic.
- Gadol is not an automatic immediate sell signal; it is a deterioration/quality warning that changes follow-up and risk management.

## Implementation inferences (tunable, not source facts)
The source material does not specify exact machine thresholds for:
- ABC lookback windows, drawdown, base-range and MA-slope tolerances.
- Resistance clustering weights/tolerance.
- Relative-money threshold versus prior reference candle.
- Retest tolerance and reacceleration threshold.
- New-listing mini-ABC lookback/range.
- Structural scoring cutoffs.

These are explicitly kept in `longterm-scan-config.json` so they can be tuned after empirical validation.

## Core line construction
Core resistance is built only from data available before the current session to avoid look-ahead leakage. Candidate levels are:
1. historical strong-reference candle open/close/high,
2. local swing highs,
3. volume-weighted candle-density zones,
4. round figures,
5. Ichimoku cloud edge,
6. MA240/480/600/1000 when near the actionable price area.

Nearby levels are clustered. The strongest reachable cluster becomes `coreResistance`, with a zone rather than a single-pixel price.

## State machine
Primary states:
`ABC_CANDIDATE -> B_PLUS -> DEOYANGBONG_C_TRIGGER -> PRE_JINDOL -> JINDOL_CONFIRMED -> RETEST_OK -> REACCELERATION`

Weak/alternate branches:
`GADOL_RISK`, `NEW_LISTING_SETUP`, `MA600_BREAKOUT`, `NEAR_MA600`, `DATA_WARNING`.

These are structural states, not automatic buy/sell instructions.

## Data boundary
- Current KRX trading value uses exact KRX Amount when available.
- Historical trading value is estimated as typical price x volume.
- Foreign/institution flow is candidate-only supporting evidence.
- News/catalyst is intentionally excluded from this scanner.
- Corporate-action-like price jumps are flagged, not silently interpreted.


## Operational output layers
The scanner deliberately separates structural-state retention, first-stage qualification, fresh action-value ranking and user-facing disclosure.

- `allCandidates`: diagnostic union of non-NONE states.
- `qualifiedPool`: first-stage quality pool recalculated from current market state every run; not user-facing.
- `actionScore`: fresh session action-value score. It does not read prior selection/rejection/rank.
- `briefingCandidates`: user-facing positive shortlist that passes the current action-value threshold; there is no fixed-number cutoff.
- `riskWarnings`: weak-breakout / Gadol quality warnings, kept separate from positive discovery.
- `radarCandidates`: earlier or less-confirmed structures retained for observation without carry-over selection bonus.

A pullback/retest is accepted only when price holds the reference-candle area **and** intervening trading value/volume contract versus the reference candle. The exact contraction thresholds are implementation inferences and remain configurable.

Named historical securities are not part of production methodology, ranking, prompts, or special-case logic. Historical source examples are isolated as opaque QA fixtures only and confer no production priority.


## Fresh re-ranking and action-value shortlist
The first-stage quality set is now called `qualifiedPool`; it is not the user-facing briefing list.

Every session:
`full universe -> structural states -> qualifiedPool -> fresh actionScore -> briefingCandidates -> watchlist/attack selection`.

`actionScore` is recomputed from current observable state only:
- Structure 0–25
- Money quality 0–20
- Entry quality 0–25
- Structural R/R 0–15
- Acceptance/follow-through 0–10
- Risk penalty 0 to -20

Structural R/R uses detected support/resistance references only. It never manufactures a price by adding or subtracting an arbitrary percentage from the current price.

Critical anti-anchoring rule: past selection, rejection, rank, watchlist membership, briefing inclusion, or a prior Gadol warning are audit history only. They are never next-session score inputs. Objective time-series facts such as reference candles, support/resistance, MA/cloud position, money expansion and retest behavior remain available because they are market-state evidence, not selection memory.

A stock filtered out today can rank at the top tomorrow if fresh market data improves its action value. A stock ranked highly today receives no carry-over bonus tomorrow.


## Action-score calibration note
For pre-trigger structures, today's quiet turnover is not automatically negative if normal liquidity is sufficient; average liquidity and controlled quietness can support a WATCH_TRIGGER classification. Structural R/R ignores near-duplicate support references that are effectively at the current close by preferring the next meaningful detected structural support. These are implementation heuristics, not source-quoted thresholds.

The current user-facing threshold is config-driven (`briefingMinActionScore`) and does not impose a fixed number of stocks. `ACTION_NOW` and `WATCH_TRIGGER` are presentation tiers only and are freshly recomputed each run.
