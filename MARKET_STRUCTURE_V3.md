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
7. **A small candle alone is not a trend-bridge level.** It must sit inside impulse -> pause -> same-direction resume.
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
- ATR
- RSI context

This layer does not decide whether a chart is good.

### 2. Level discovery

Independent evidence generators:
- `EVENT_CLOSE` / `EVENT_BODY`
- `BOX_UPPER` / `BOX_CLOSE` / `BOX_LOWER`
- `TREND_BRIDGE`
- `SWING_HIGH` / `SWING_LOW`

Nearby evidence is merged into a zone while preserving its provenance.

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

These families are peers. No family owns the engine.

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

No aggregate score is used.

Execution references must be observed structure:
- setup trigger level
- accepted structural support
- setup-specific invalidation
- next structural resistance
- structural R/R when both legs are real

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

A future feature belongs in V3 only if it can answer all four:

1. What observable market behavior does it represent?
2. Which layer owns it?
3. Can it be tested with a generic synthetic fixture?
4. Can it be added without creating a second hidden scoring system?

If not, it stays outside the production decision engine.
