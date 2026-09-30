# Crypto Blind Replay V1 — Postmortem

## Integrity

- Locked decision commit: `372ce63d32aaff5a9544c66b1e7fdd5766eeb69e`
- Future was not opened until all 20 cases were committed.
- Grading workflow run: `36657140890` — SUCCESS.
- Initial capital: KRW 10,000,000.
- Allowed exposure: BTC/ETH spot plus explicitly chosen capped generic daily-reset 2x sleeves; no margin borrowing or high leverage.

## V1 result

- Final capital: KRW 8,695,980.
- Total return: -13.04%.
- Max drawdown: -21.88%.
- Trade win rate: 25.81% (8/31 non-flat sleeves).
- Active-case win rate: 23.53% (4/17).
- Profit factor: 0.713.

This is a FAIL as a deployable trading process. Do not rationalize the negative result away.

## What failed

### 1. Confidence calibration

`ATTACK_CANDIDATE` was too permissive.

- 7 ATTACK cases.
- Only C14 finished positive.
- Arithmetic mean case return was about -2.87%.

`PROBE` sizing contained damage better.

- 10 PROBE cases.
- 3 finished positive.
- Arithmetic mean case return was about +0.92%, driven by a few large winners.

The central lesson is not to turn ATTACK into a score threshold. It is to demand better location/confirmation/asymmetry before allowing larger capital deployment.

### 2. Position management was missing from the replay

The V1 grader made one decision at cutoff and then mechanically held until a fixed stop, 30 calendar days, or the next case cutoff. That is not the intended autonomous-trader workflow.

Several losing sleeves first produced meaningful favorable excursion and then gave it back:

- C03 ETH: MFE +21.99%, final -3.86%.
- C16 BTC: MFE +23.57%, final -6.11%.
- C17 BTC spot: MFE +11.39%, final -2.28%.
- C17 BTC 2x: MFE +18.63%, final -6.18%.
- C17 ETH: MFE +10.66%, final -6.25%.

Across the table, 13 losing sleeves had MFE of at least +5% before finishing negative. This indicates that entry selection alone does not explain the result; dynamic management must be tested separately and prospectively.

### 3. Initial invalidation was often too expensive

Spot losses commonly reached roughly -8% to -15% before the fixed stop. With a 2x sleeve, C15 and C20 lost roughly -26% and -23% on that sleeve. The small capital allocation limited portfolio damage, but the structural invalidation/position-size relationship needs stricter asymmetry.

### 4. 2x exposure did not create an edge

The four 2x sleeves returned approximately:

- C14 BTC 2x: +43.18%.
- C15 BTC 2x: -26.09%.
- C17 BTC 2x: -6.18%.
- C20 ETH 2x: -22.88%.

Only 1/4 won. The average sleeve return was about -2.99%. Keep 2x exceptional; there is no evidence from V1 that leverage should be expanded.

## What V1 does and does not prove

V1 is a valid blind **entry/confidence stress test**. It is not a valid simulation of the full trader the user asked for, because the assistant was not allowed to re-read the chart and manage the live position after entry.

The reported BTC buy-and-hold return over the full 2020–2025 calendar span is not an apples-to-apples benchmark. V1 intentionally samples only 20 sparse decision windows and sits in forced cash between them. Do not use that benchmark to judge relative performance.

## Required V2 test

Do not change the V1 decisions after seeing outcomes. Preserve them as an immutable baseline.

V2 must be a prospective blind walk-forward:

1. Start with a new set of unseen historical episodes, not these 20 cutoffs.
2. Reveal only information available at each decision time.
3. Lock initial position, size, invalidation, no-chase rule and 2x decision.
4. Reveal the next increment only after that decision is committed.
5. At each review point allow HOLD / ADD / REDUCE / EXIT / RE-ENTER / CASH.
6. Portfolio capital must roll forward after every action.
7. Do not retrofit trailing rules from V1 outcomes into V1; any management rule must be declared before V2 starts.
8. Score final capital, MDD, profit factor, win rate, average win/loss, MFE capture ratio, loss-after-positive-MFE rate, and confidence calibration by ATTACK/PROBE.

The objective remains expected-value capital growth, not maximizing win rate or matching any named chart pattern.
