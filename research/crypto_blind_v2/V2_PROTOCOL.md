# Crypto Blind Walk-Forward V2 Protocol

## Objective
Run one continuous KRW 10,000,000 BTC/ETH portfolio as if the assistant were the trader. The objective is expected-value capital growth with drawdown control, not pattern recognition or win-rate maximization.

## Integrity
- V1 remains immutable and is not rewritten.
- V2 uses a new deterministic hidden historical episode that does not overlap the V1 scored windows.
- Calendar dates and absolute prices are hidden from the assistant; price series are normalized to reduce historical-regime recognition.
- At each review only information available through that review point is exposed.
- A decision is committed before the next 5 calendar days are revealed.
- No result-driven edits to an already committed decision.

## Capital and allowed vehicles
- Initial capital: KRW 10,000,000.
- BTC and ETH only.
- Spot is the default vehicle, but vehicle choice is part of the assistant's decision.
- A generic daily-reset 2x sleeve is allowed as a proxy for BITU/ETHU-type exposure.
- No margin borrowing, futures, options, or products above 2x.
- Total cash actually allocated to positions may not exceed 100% of portfolio capital.
- There is NO arbitrary cap on the fraction placed in 2x sleeves. The assistant decides spot/2x/cash allocation from the chart, asymmetry, invalidation distance, volatility and portfolio context at each review.

## Walk-forward cycle
- One continuous hidden episode: 120 calendar days.
- Review cadence: every 5 calendar days plus the final review.
- At each review the assistant may HOLD, ADD, REDUCE, EXIT, RE-ENTER, rotate BTC/ETH, change spot/2x mix, or stay fully in cash.
- Every decision must state target capital allocation and structural invalidation for each active sleeve.
- Rebalancing occurs at the observed review close represented by the current normalized card.
- Between reviews, declared structural stops remain live. If a stop is hit, that sleeve exits to cash and stays cash until the next review.
- The assistant is free to protect profits or reduce risk at review points; there is no forced 30-day hold.

## Decision principles
- Read price + participation + time first.
- Build important-price hierarchy and role state before naming a setup.
- Judge acceptance/rejection, current location, asymmetry and chase risk.
- RSI is secondary confirmation/warning only.
- Do not buy merely because price is low or RSI is oversold.
- Do not attack merely because trend is strong.
- ATTACK requires materially better asymmetry and confirmation than PROBE; no numeric score threshold is imposed.
- Position size, stop distance and vehicle choice are a single capital-allocation decision.

## Scoring
Track continuously:
- final capital and total return,
- max drawdown,
- realized and mark-to-market P/L,
- profit factor,
- trade and review-point win rates where meaningful,
- average win/loss,
- MFE capture ratio,
- loss-after-positive-MFE rate,
- ATTACK vs PROBE confidence calibration,
- 2x contribution to return and drawdown,
- time in cash and capital utilization.

V2 is a trading-process test. A negative result is preserved as a failure; it is not re-labeled or rerun with retrofitted rules.