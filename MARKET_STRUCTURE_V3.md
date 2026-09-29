# Market Structure V3

Status: SHADOW / NOT PRODUCTION CUTOVER  
Architecture date: 2026-09-29

## Goal

Replace the old YBM-governed decision architecture with a sustainable chart engine whose governing model is:

**price + volume + time -> important price zones -> role state -> close acceptance/rejection -> setup family -> confirmation -> execution**

YBM is no longer a required top-level framework. Any useful YBM idea may survive only when it can be expressed as generic observable market structure.

The existing data collection, KRX universe handling, daily-bar freshness gates, GitHub automation and diagnostic infrastructure are retained because they are generic infrastructure rather than YBM logic.

## Non-negotiable design rules

1. **No stock-specific rules.** Regression fixtures are synthetic.
2. **No hidden operator intent.** Do not infer accumulation, manipulation, or "energy" as facts.
3. **No aggregate action score.** Candidate state must remain explainable from categorical structure and evidence.
4. **A price level and its role are different objects.**
5. **Intraday penetration is not equal to a confirmed breakout.** Close acceptance matters.
6. **RSI is confirmation/warning only.** RSI 70/30 never creates automatic buy/sell signals.
7. **A small candle alone is not a trend-bridge level.** It must sit inside impulse -> pause -> same-direction resume. Rising bridges are potential support evidence; falling bridges are potential resistance evidence.
8. **A spring is a failed support-break attempt plus reclaim, not an automatic rally prediction.**
9. **A box is an area with upper / compressed close / lower kept separately.**
10. **Implementation thresholds are configuration, not doctrine.**
11. **V2 remains a frozen comparison baseline until V3 passes shadow validation and explicit cutover.**

## Layering

### 1. Data / features

Reusable infrastructure:
- KOSPI/KOSDAQ universe
- OHLCV history
- current trading value when available
- estimated historical trading value
- MA20/60/120/240/480/600/1000
- shorter-history listings are allowed into the common engine once enough bars exist for the setup being tested; there is no separate legacy "new listing doctrine"
- ATR
- RSI context

This layer does not decide whether a chart is good.

### 2. Level discovery

Independent evidence generators:
- `EVENT_CLOSE` / `EVENT_BODY`
- `BOX_UPPER` / `BOX_CLOSE` / `BOX_LOWER`
- `TREND_BRIDGE`
- `TRADE_DENSITY` (price-volume-time concentration)
- `SWING_HIGH` / `SWING_LOW`

Nearby evidence is merged into a zone while preserving its provenance. Merged zones are classified as `CORE` or `SUPPORTING`; only `CORE` zones can drive hard failure warnings or execution support.

### 3. Role state

Each merged level receives a current role from observable price behavior:
- `DECISION_ZONE`
- `BREAKOUT_PENDING`
- `ACCEPTED_SUPPORT`
- `SUPPORT_CANDIDATE`
- `FAILED_BREAKOUT`
- `BREAKDOWN_PENDING`
- `ACCEPTED_RESISTANCE`
- `RESISTANCE_CANDIDATE`
- `SPRING_RECLAIM`

A level cannot be used as execution support merely because it lies below current price.

### 4. Setup families

V3 currently recognizes:
- `BASE_REVERSAL`
- `HIGH_TREND_CONTINUATION`
- `BOX_BREAKOUT`
- `SPRING`
- `TREND_BRIDGE`
- `ROLE_REVERSAL`
- `BOX` building state

These families are peers. No family owns the engine. Setup precedence is categorical and internal; V3 does not emit a numeric setup score/maturity score.

### 5. Confirmation

Supporting evidence:
- current/normal trading-value state
- current/normal volume state
- recent pullback-money contraction
- RSI direction
- RSI bullish/bearish divergence

Confirmation cannot manufacture a setup that price structure does not contain.

### 6. Execution

Outputs are categorical:
- `EXECUTABLE`
- `WATCH_TRIGGER`
- `RADAR`
- `REJECT`

`BOX_BREAKOUT_ACCEPTED` and `SPRING_CONFIRMED` are still information/confirmation states; they do not become `EXECUTABLE` merely because price moved away from the level. V3 prefers an observable retest/role confirmation instead of chasing.

No aggregate score is used.

Execution references must be observed CORE structure. Supporting swing levels may add evidence but cannot independently become execution support.

Execution references must be observed structure:
- setup trigger level
- accepted structural support
- setup-specific invalidation
- next structural resistance
- structural R/R when both legs are real

## Assistant deep-review layer

V3 is deliberately hybrid.

The scanner's job is **not** to encode every visual/context judgement from the chart-study material. Its machine scope is limited to:

- compress the full market into a bounded candidate set,
- surface observable price/volume/time evidence,
- propose structural hypotheses,
- calculate mechanically traceable reference levels and invalidation candidates,
- attach bounded **daily + weekly + monthly** price/participation traces for deeper review.

Every surfaced candidate carries `assistantReviewRequired=true`. A bounded `deepReviewQueue` is selected with family diversity so one easily-detected pattern cannot dominate the review set.

The later assistant review layer receives multiple timeframes so it does not overfit to a short crop. It owns the higher-order judgements that are fragile when hard-coded:

- whether the detected box/bridge is genuinely meaningful in full context,
- whether the important price is actually the dominant market reference,
- whether current location is attractive or already chased,
- whether higher-timeframe context changes the interpretation,
- whether several weak machine hypotheses are merely different names for the same structure.

This separation is intentional: future chart-study improvements should usually improve the assistant review rubric first, not automatically create another detector or numeric threshold.

The machine plan is therefore a **proposal**, not the final investment decision.

## Storage / artifact boundary

Multi-timeframe chart traces are **ephemeral review evidence**, not canonical Git history.

- `market-structure-v3.json`: lightweight canonical state/evidence summary; no heavy chart traces.
- `/tmp/market-structure-v3-review.json`: bounded assistant-review packet with daily/weekly/monthly traces.
- `/tmp/market-structure-v3-full.json`: diagnostic market output without review traces.
- The workflow uploads review/full diagnostics with short retention and commits only the lightweight canonical file.

This prevents daily Git history from growing by several megabytes while preserving the evidence needed for deep chart review.

## Why V2 is not deleted immediately

This is not because YBM must be preserved. V2 is retained temporarily as a **baseline control** so V3 can be judged against a known working scanner without contaminating V3 with V2 decisions.

Cutover sequence:

1. V3 synthetic regressions pass.
2. V3 full-market shadow scan passes coverage/selectivity invariants.
3. Inspect several sessions for:
   - candidate explosion
   - obvious structure omissions
   - invalid support/resistance role assignments
   - false breakout handling
   - setup duplication
   - execution R/R integrity
4. Compare V3 vs V2 only as an audit; V2 does not vote on V3 candidates.
5. Explicitly cut production output to V3.
6. Archive or delete YBM-specific decision code after rollback window.

## What is intentionally not hard-coded yet

The study material does not justify pretending there is one universal numeric answer for:
- ideal box duration
- exact box-close algorithm beyond compressed-candle semantics
- spring maximum undershoot
- spring maximum reclaim delay
- trend-bridge pause duration
- multi-timeframe level priority
- RSI divergence thresholds

V3 exposes every such threshold in config and keeps it regression-testable.

## Sustainability contract

A future **machine-coded** feature belongs in V3 only if it can answer all five:

1. What observable market behavior does it represent?
2. Which layer owns it?
3. Can it be tested with a generic synthetic fixture?
4. Can it be added without creating a second hidden scoring system?
5. Is hard-coding it actually better than leaving it to assistant deep review?

If the fifth answer is no, preserve the evidence needed for review instead of adding another detector. If the first four answers fail, it stays outside the production decision engine.
