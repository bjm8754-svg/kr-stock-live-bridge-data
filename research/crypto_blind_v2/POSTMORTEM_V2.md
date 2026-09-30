# Crypto Blind Walk-Forward V2 — Postmortem

## Integrity

- Initial capital: KRW 10,000,000.
- Continuous blind episode: 120 calendar days.
- Hidden episode commitment: `9ca8cf1291100b55d62e64a5640b67cd1602d88ef8cd151197c3bfa3fecbafe5`.
- Actual dates were hidden until all 24 decisions were committed.
- Revealed episode: 2019-07-02 through 2019-10-30.
- Decisions were made every 5 days using normalized BTC/ETH cards with no calendar date or future bars.
- Prior D00-D23 decisions remain immutable.
- Spot and generic daily-reset 2x exposure were both discretionary. There was no arbitrary 10%/20% user cap on 2x; the only ceiling was no vehicle above 2x and total cash allocation <=100%.

## Result

- Final capital: KRW 9,295,460.77.
- Total return: **-7.045%**.
- Max drawdown: **-10.303%**.
- 24 review intervals; 11 carried risk and 13 were fully cash.
- Positive active intervals: 4/11.
- Mean target capital utilization across all 24 review points: about 15.4%.

This remains an **absolute-return FAIL**. The objective is compounding capital, and 100% cash would have returned 0% over the same episode.

For context only, the hidden normalized series imply approximately:
- BTC buy-and-hold over the same episode: **-15.6%**.
- ETH buy-and-hold over the same episode: **-37.2%**.

Therefore V2 reduced bear-market damage relative to passive crypto exposure, but that is not the same as producing positive expected-value trading returns. Do not label the test a success because it lost less than the underlying.

## What improved versus the V1 process

### 1. The assistant actually managed positions

V2 allowed HOLD / ADD / REDUCE / EXIT / RE-ENTER / CASH rather than mechanically holding for 30 days.

Useful examples:
- D06 BTC probe: +2.667% portfolio interval.
- D07: risk was reduced after a sharp rise/rejection and the interval still finished +0.119%.
- D21: positions were exited because the confirmation thesis weakened before hard stops were reached.
- D22: a small BTC base probe was stopped rather than averaged down.
- D23: the assistant re-entered after a new high-participation spring/reclaim and recovered +1.912% in the final interval.

The process was more faithful to an actual discretionary trader than V1.

### 2. NO-CHASE / cash discipline worked

The strongest decision in V2 may have been not trading.

At D16 ETH had exploded vertically with RSI above 90 and heavy participation. The assistant stayed cash instead of chasing. Within the next five days both assets suffered a liquidation event; ETH fell from the mid-70s normalized area into the high-50s and BTC collapsed from the low-90s into the high-70s.

D17-D19 then remained cash through the immediate post-liquidation volatility rather than treating extreme RSI as a buy signal.

This validates the learned principle that strength/oversold conditions alone are not entries and that cash is an active position.

### 3. Stop-and-reenter behavior improved

D22 is a useful example. The BTC probe had a declared invalidation and was stopped when the base low failed. Two days later, a qualitatively different high-participation reclaim appeared. D23 treated that as a new setup and re-entered rather than refusing because of the prior stop. The final interval was positive.

That behavior is preferable to either averaging down or refusing to re-enter after being stopped.

## What still failed

### 1. ATTACK calibration remains the largest weakness

D08 was the only V2 decision that used 2x exposure:
- BTC spot 35% + generic BTC daily-reset 2x 15%.
- Both sleeves hit invalidation in the next interval.
- Portfolio interval return: **-3.657%**, the largest single interval loss in V2.

The 2x sleeve alone lost about KRW 166k, roughly 24% of the entire final KRW loss. The problem was not the existence of 2x; it was promoting a recent reclaim/pullback into ATTACK before the reclaimed structure had proved durable enough.

Do not respond by imposing an arbitrary 2x percentage cap. Improve the quality threshold for ATTACK and vehicle selection instead.

### 2. Reclaim signals below damaged higher-timeframe structure produced false starts

Several entries looked better than simple falling-knife buys but still failed:
- D02 BTC relative-strength add was stopped.
- D04 BTC re-entry probe was stopped.
- D13 BTC 'confirmed' reclaim was stopped.
- D20 BTC/ETH recovery probes lost -2.092% before the thesis was proactively abandoned.
- D22 BTC base probe was stopped before the later spring/reclaim.

The common issue is that a 20-day reclaim or a short base is not enough when the 50/100-day structure remains damaged or overhead supply is still dominant.

This is a review-layer lesson, not evidence that another rigid detector or score should automatically be added.

### 3. The process was too defensive to demonstrate positive alpha

The portfolio was fully cash in 13 of 24 review intervals and average target capital utilization was only ~15.4%. This helped limit drawdown, but it also means the test primarily demonstrated loss avoidance, not robust capital growth.

A good trader must do both:
- avoid bad markets,
- then deploy enough capital when asymmetry becomes genuinely favorable.

V2 did the first better than V1 but did not prove the second.

### 4. The first half still contained repeated premature bottom/reclaim attempts

Early in the episode the assistant repeatedly tried small re-entries before durable acceptance existed. Each loss was bounded, but the sequence accumulated frictional drawdown. Being small does not make a negative-expectancy entry good.

The colder rule is conceptual rather than numeric: after structural damage, require evidence that prior resistance has actually changed role and survived time/retest, not merely that price has bounced back above a short moving average.

## V1 vs V2

Do not compare the raw returns as if they were the same market sample.

- V1: sparse random entry/confidence stress test across 2020-2025; -13.04%, MDD -21.88%; position management largely absent.
- V2: one continuous hidden 120-day episode in 2019; -7.045%, MDD -10.303%; active 5-day management included.

V2 is structurally a much better test of the intended autonomous trader. Its lower drawdown is encouraging, but one bear-market episode is insufficient evidence of a durable edge.

## Learning update — do not overfit

Carry these lessons into future blind tests and live chart review:

1. Preserve NO-CHASE discipline. A vertical breakout can be strong and still be a bad current entry.
2. Treat RSI as context only. Extreme oversold did not justify catching the liquidation.
3. After major structural damage, short-term MA reclaim is insufficient by itself. Demand role change, time, and/or successful retest against higher-timeframe supply.
4. ATTACK needs substantially stronger durability/asymmetry than a normal PROBE. The failed D08 attack is the clearest warning.
5. Stops and re-entry are complementary. A stop does not invalidate a later, genuinely new setup.
6. Dynamic thesis decay matters: exit can occur before a hard stop when the expected confirmation fails.
7. Do not turn these observations into a large new scorecard or detector stack after one episode.

## Next validation

The next serious validation should use multiple additional unseen continuous episodes spanning different regimes (uptrend, downtrend, range, transition) under the same prospective walk-forward discipline. Do not tune the protocol to the revealed 2019 episode first. The goal is to determine whether the review process generalizes before using it to justify production trading decisions.
