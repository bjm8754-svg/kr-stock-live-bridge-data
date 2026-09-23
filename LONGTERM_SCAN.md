# YBM Swing V2 Structural Scanner

## Purpose
This scanner replaces manual HTS condition-search/chart-sweep work. It is intentionally **price/volume/trading-value/structure first** and does not attempt to discover ordinary stock-specific news.

## V2 interpretation
The scanner no longer treats "MA600 cross" as the whole setup. The primary sequence is:

`long decline -> long base -> MA240/480/600/1000 recovery -> money-backed reference candle -> supply/resistance digestion -> real/weak breakout -> retest -> reacceleration`.

Key source terms are represented as observable states:

- **ABC**: long decline (A), long base/congestion (B), long-MA recovery / N-wave style advance (C).
- **더양봉 proxy**: strong bullish reference candle with meaningful volume and trading value.
- **네모네모**: supply/congestion zone built from meaningful support/resistance, not a fixed 120-day-high box.
- **진돌이**: meaningful resistance breakout with both volume and trading value confirmation.
- **가돌이**: breakout quality warning when confirmation is insufficient or materially weaker than the relevant prior reference move.
- **양음양 / reacceleration**: strong reference candle, controlled rest, renewed bullish move.

## Core resistance
`coreResistance` is built only from **pre-current** data. Candidate levels include:

1. historical strong-reference candle open/close/high,
2. swing highs,
3. candle-density/volume-profile proxy zones,
4. round figures,
5. Ichimoku cloud edge,
6. MA240/480/600/1000 when near price.

Nearby candidates are clustered into a zone and scored by source overlap and repeated touches.

## Money logic
The scanner combines:

- absolute trading value,
- current vs estimated 20-session trading value,
- volume expansion,
- close location,
- current money vs the prior strong reference candle,
- market-cap-normalized turnover when available.

KRW 100bn is the taught minimum reference for a "real" money-backed breakout; KRW 300bn is treated as very strong. These are references, not universal laws.

Current KRX `Amount` is exact when available. Historical trading value is estimated as typical price × volume and is explicitly labeled estimated.

## Long-history and new-listing tracks
- **LONG_HISTORY**: uses MA600/MA1000 and ABC logic when enough history exists.
- **NEW_LISTING**: does not require MA600; it looks for a strong reference candle, mini-base, supply zone and subsequent breakout quality.

## Output states
Primary scanner states:

- `REACCELERATION`
- `JINDOL_CONFIRMED`
- `RETEST_OK`
- `DEOYANGBONG_C_TRIGGER`
- `PRE_JINDOL`
- `B_PLUS`
- `ABC_CANDIDATE`
- `GADOL_RISK`
- `NEW_LISTING_SETUP`
- `MA600_BREAKOUT`
- `NEAR_MA600`
- `DATA_WARNING`

These are **structural states, not automatic buy/sell instructions**.

## Grade boundary
`structuralGrade` is this system's own `STRONG / GOOD / WATCH / EARLY` grade. It deliberately does **not** claim to reproduce the source teacher's S/A/B grade because the supplied source material does not define that grading formula completely.

## Source vs inference
See `YBM_V2_METHOD.md`. Source-derived concepts and implementation inferences are separated explicitly. Numeric ABC windows, clustering weights, tolerances, relative-money cutoffs and score bands remain tunable until empirical validation is completed.

## Schedule
GitHub Actions runs weekdays at **16:30 KST**. Holiday/stale data is detected and canonical output is not committed.

## Validation
Every workflow run now performs local V2 self-tests before the full-market scan. Coverage and methodology-version gates must also pass before a canonical result can be committed.

## Downstream
Intended pipeline:

`after-close full-market V2 scan -> next 08:15 candidate compression -> watchlist -> Cloudflare/live bridge -> 09:35/09:40 intraday follow-through validation`.

Master/08:15/09:35/09:40 prompts should be updated only after the V2 scanner itself is validated.
