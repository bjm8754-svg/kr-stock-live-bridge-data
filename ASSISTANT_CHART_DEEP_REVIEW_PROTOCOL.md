# Assistant Chart Deep-Review Protocol

Status: CANONICAL REVIEW CONTRACT
Date: 2026-09-29

## Purpose

The scanner compresses the market and packages evidence. This protocol is the higher-order chart-reading layer. Its purpose is not to reproduce study terminology; it is to improve investment decision quality and expected value.

Machine setup names are hypotheses, never conclusions. Re-read the chart from the supplied trace and structural evidence before accepting any machine label.

## Review order

### 1. Reconstruct the chart before naming a pattern
- Read price path, range expansion/contraction, closes, volume/trading-value behavior and time spent at prices.
- Do not begin with `BOX`, `SPRING`, `BRIDGE`, `BASE_REVERSAL` or any other machine label.
- Ask first: where did meaningful trading occur, where did price fail to persist, and where did a new price area become accepted?

### 2. Build the important-price hierarchy
- Prefer prices supported by price + participation + time.
- Event closes, meaningful box boundaries/internal consensus, repeated role transitions and true trend-connection areas can be important.
- Simple swing highs/lows are supporting evidence unless the surrounding history makes them structurally dominant.
- Treat prices as zones with a reference price, not magical one-tick lines.

### 3. Determine current role from observable behavior
- A price below current price is not automatically support.
- A price above current price is not automatically resistance.
- Intraday penetration alone does not confirm transition.
- Close acceptance, subsequent holding/rejection and re-test behavior determine whether the role changed.
- Broken support can become resistance; broken resistance can become support only after observable acceptance.

### 4. Judge the structure in context
- Box: verify real time/transaction acceptance and repeated boundary behavior; do not accept a fixed-window box merely because the detector found one.
- Spring: require a genuine downside break attempt, failure to persist below the boundary and reclaim. Treat it as failed downside continuation, not guaranteed upside.
- Trend bridge: require impulse -> pause/organization -> same-direction resume. A small candle alone is not a bridge.
- High continuation: distinguish healthy compression/pressure from late extension and chase risk.
- Base reversal: distinguish genuine transition from a weak bounce inside a damaged long-term structure.
- If several machine labels describe the same underlying structure, collapse them into one interpretation.

### 5. Judge current location
- Good structure at a bad location can still be a bad trade.
- Compare current price with the nearest accepted support, meaningful internal reference, breakout boundary and next real supply/resistance.
- Prefer asymmetric setups where invalidation is structurally close and upside is not immediately capped.
- Explicitly flag chase risk when the thesis is valid but the price has already moved too far from the actionable reference.

### 6. Read participation with price
- Breakout participation expansion can strengthen evidence.
- Pullback contraction can support the interpretation that adjustment pressure is weakening.
- Re-expansion at support can strengthen the reaction.
- High volume/trading value without the expected price response is a warning, not bullish by itself.

### 7. RSI last
- RSI never creates the trade.
- Use direction and divergence only as confirmation/warning after price structure is understood.
- 70 is not an automatic sell; 30 is not an automatic buy.

### 8. Produce an investment-useful chart conclusion

Return one chart state:
- `ATTACK_CANDIDATE`: structure, location and invalidation are sufficiently clear for immediate integration with fundamentals/catalyst/live confirmation.
- `PROBE_CANDIDATE`: attractive asymmetry exists but one important confirmation is still missing.
- `WATCH`: structurally interesting, but current price/location or acceptance is not ready.
- `REJECT`: structure is damaged, ambiguous, too extended, poorly located or machine hypothesis is not convincing.

Every non-REJECT conclusion must include:
- dominant chart thesis in plain language,
- important price/zone that matters now,
- what observable event confirms the thesis,
- structural invalidation,
- next meaningful resistance/target area if visible,
- chase/no-chase judgement,
- one strongest counterargument.

## Boundaries

- Do not infer hidden operator intent as fact.
- Do not manufacture exact thresholds when the evidence is contextual.
- Do not reward a stock merely for matching more named patterns.
- Do not average contradictory structures into a score.
- Do not let RSI, one moving average or one event candle override the whole chart.
- Do not convert an attractive chart directly into a portfolio position without the broader investment layer (company quality, revisions, catalyst, industry/macro, US lead price discovery, event risk and position sizing).

## Sustainability rule

When new chart-study material is learned, first improve this review protocol. Add machine code only when the concept is objective enough to reduce review workload without destroying the contextual meaning.
