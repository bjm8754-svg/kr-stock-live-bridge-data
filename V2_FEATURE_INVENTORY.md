# V2 Feature Inventory

Purpose: distinguish `implemented` from `precision-validated`. A field existing in JSON is not considered final trading-quality validation. The agreed V2 implementation/output contract is now PASS; empirical chart/timing precision remains NOT DONE.

## Agreed feature contract

| Feature | Implementation evidence | Automated contract/test | Precision status |
| --- | --- | --- | --- |
| ABC long-decline/base/recovery | `abc` output + V2 methodology | output-contract test | NOT DONE |
| Strong reference candle / 더양봉 | `deoyangbong`, active reference anchor | reference-candle grading tests | NOT DONE |
| Core resistance / supply zone / 네모네모 internal logic | `build_core_resistance`, `coreResistance`, clustered sources | core clustering test | NOT DONE |
| Long MA structure | MA20/60/120/240/480/600/1000 | output-contract test | NOT DONE |
| Ichimoku cloud | `cloud` | output-contract test | NOT DONE |
| Money / turnover quality | `money` | breakout/action tests | NOT DONE |
| Jindol / Gadol | `breakoutClass`, `classify_breakout` | JINDOL/GADOL tests | NOT DONE |
| Pre-Jindol | `preJindol` | output-contract test | NOT DONE |
| Retest + supply contraction | `retestOk`, `retestSupply` | output-contract test | NOT DONE |
| Reacceleration | `reacceleration` | output-contract test | NOT DONE |
| Yang-Eum-Yang | `yangEumYang` | output-contract test | NOT DONE |
| New-listing track | `newListingSetup`, NEW_LISTING track | synthetic new-listing test | NOT DONE |
| Structural entry / support / next resistance / R-R | `entryPlan` | no-arbitrary-price implementation + output-contract test | NOT DONE |
| Chart quality S/A/B+ independent of timing | `chartGrade`, `chartCandidates` | chart-grade independence/reference tests | NOT DONE |
| Fresh Action Score / anti-selection-memory | `actionScore` | selection-memory invariant test | NOT DONE |
| Compact canonical handoff | `YBM_BRIEF_V2` | compact-schema test | PARTIAL — current 2026-09-23 migration predates chart-grade layer |

## Current automated evidence

- Feature-contract/self-test change commit: `87b3e492974869c63c701223e951a399f8a1e937`.
- Historical replay check for that commit: `success` (`35977284215`).
- Full-market scan check from the same commit: `success` (`35977284250`). On the 2026-09-24 non-trading day, validation passed and the canonical commit step was correctly skipped rather than overwriting the previous trading-day canonical.

## What 'precision NOT DONE' means

The code path exists and automated invariants can pass, but we have not yet proven that the detected core zone, reference candle, Jindol/Gadol, retest, entry/invalidation and next resistance match high-quality human chart review across a sufficiently broad sample. That is the next precision phase after sustainability blockers are resolved.

## Explicit non-goal

No user-facing rectangle/box drawing is required. Supply/box structure is an internal feature used to derive actionable prices.
