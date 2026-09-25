# V2 Feature Inventory

Purpose: distinguish `implemented` from `precision-validated`. A field existing in JSON is not considered final trading-quality validation. This inventory is the evidence-only contract for the originally agreed V2 scope.

## After-close structural scanner contract

| Feature | Implementation evidence | Automated contract/test | Precision status |
| --- | --- | --- | --- |
| ABC long-decline/base/recovery | `abc_features`, `abc` output | output-contract/self-test | IMPLEMENTED / PRECISION NOT DONE |
| Strong reference candle / 더양봉 | `rolling_event_mask`, `deoyangbong`, active reference anchor | reference-candle grading/self-tests | IMPLEMENTED / PRECISION PARTIAL |
| Core resistance / supply zone / 네모네모 internal logic | `build_core_resistance`, clustered `coreResistance` | pre-current construction + replay calibration | IMPLEMENTED / PRECISION PARTIAL |
| Long MA structure | MA20/60/120/240/480/600/1000 | output-contract/self-test | IMPLEMENTED / CONTRACT PASS |
| Ichimoku cloud | `cloud` | output-contract/self-test | IMPLEMENTED / CONTRACT PASS |
| Money / turnover quality | absolute trading value, avg20 ratio, volume ratio, relative reference money, market-cap turnover | breakout/action/self-tests | IMPLEMENTED / PRECISION PARTIAL |
| Jindol / Gadol | `breakoutClass`, `classify_breakout` | JINDOL/GADOL regression tests | IMPLEMENTED / PRECISION PARTIAL |
| Pre-Jindol | `preJindol` | output-contract/self-test | IMPLEMENTED / PRECISION NOT DONE |
| Acceptance / follow-through | Jindol close acceptance + `actionScore.components.acceptance` | action-score regression path | IMPLEMENTED / PRECISION NOT DONE |
| Retest + supply contraction | `retestOk`, `retestSupply` | output-contract/replay path | IMPLEMENTED / PRECISION PARTIAL |
| Reacceleration | `reacceleration` / Yang-Eum-Yang | output-contract/replay path | IMPLEMENTED / PRECISION PARTIAL |
| New-listing separate rail | `track=NEW_LISTING`, `newListingSetup` | synthetic new-listing regression test | IMPLEMENTED / SYNTHETIC PASS; REAL SAMPLE NOT DONE |
| Structural entry / support / next resistance / R-R | `entryPlan` from detected structure only | support hierarchy + invalidation/R-R regression + source-level replay | IMPLEMENTED / PRECISION PARTIAL |
| Chart quality S/A/B+ independent of timing | `chartGrade`, `chartCandidates` | independence/reference-integrity tests | IMPLEMENTED / CALIBRATION PARTIAL |
| Fresh Action Score / anti-selection-memory | `actionScore` | selection-memory invariant regression | IMPLEMENTED / INVARIANT PASS |
| Compact canonical handoff | `YBM_BRIEF_V2` | compact-schema test | PARTIAL — current canonical scan is still the 2026-09-23 pre-chart-grade migration |

## Intraday operational contract

| Feature | Current evidence | Status |
| --- | --- | --- |
| 09:00~09:35/09:40 watched-symbol minute path | `live.json.history` + semantic freshness validator | IMPLEMENTED / REAL-SESSION REVALIDATION NOT DONE |
| Market Ignition | Canonical Master requires market/breadth/cluster ignition; hardened Worker exposes indexes + money-aware ranked scan | IMPLEMENTED / REAL-SESSION CLASSIFICATION REVALIDATION NOT DONE |
| Turnover Ignition | Hardened Worker stores 09:30/09:35/09:40 money-aware ranked scans and publishes `scan.turnoverTop` plus `scanDelta.turnoverAcceleration` | IMPLEMENTED FOR RANKED-SCAN DELTA / REAL-SESSION REVALIDATION NOT DONE; not claimed as full-market same-time average |
| NEW CHALLENGER outside morning watchlist | Canonical Master uses `scan.turnoverTop`, `scan.volumeTop`, `scan.risingLiquid`, `scanDelta.newEntries` and explicitly forbids claiming full-market completeness beyond coverage | IMPLEMENTED FOR RANKED-SCAN DISCOVERY / REAL-SESSION REVALIDATION NOT DONE |
| 08:15 plan vs actual follow-through | 09:35/09:40 Master contracts + minute path | IMPLEMENTED / REAL-SESSION REVALIDATION NOT DONE |
| Trigger / Retest / Reacceleration intraday confirmation | Master maps completed-daily setup to actual minute path | IMPLEMENTED / PRECISION NOT DONE |

## Current automated evidence

- Feature-contract/self-test change commit: `87b3e492974869c63c701223e951a399f8a1e937`.
- Historical replay baseline: `success` (`35977284215`).
- Feature-contract full-market baseline: `success` (`35977284250`). On the 2026-09-24 non-trading day, validation passed and the canonical commit step was correctly skipped rather than overwriting the prior trading-day canonical.
- Source-labeled replay report is now persisted as `v2-replay-report.json`; replay workflow persistence commit `e8db6671decbbb0b0a3955ab033b206c4f88dcac`.
- Replay observability expansion commit `f9957546b2f3909a5e1da110cf2de9e557a02086`; source-labeled control expansion commit `69b0d442225d769042c7edc6c750d14bc7e2ca4a`; latest replay run `35983362185` concluded `success`.
- False-negative discovery fix: `790b0f7c22749937115b427ff6179741867de5e1` plus regression test `da0f7467fe692e46b1f798ed95c1570bee3732fc`. It permits a fresh money-backed long-structure/core/cloud setup to enter B+ even when an obsolete historical reference has failed, while S/A still require a usable strong reference.
- Full-market regression after that fix: run `35983214306` concluded `success`; self-test, full scan and validation all passed, and the non-trading-day canonical commit was correctly skipped.
- Current `scripts/test_longterm_scan_v2.py` explicitly checks the agreed structural field contract, long-MA keys, Jindol/Gadol boundary, new-listing rail, selection-memory independence, chart-grade/reference integrity and the fresh-discovery B+ fallback.
- Money-aware market-scan commit `b933e27a701aaee99a645d562df3878dbd37d8fe`; regression-test commit `54d7c2adfb27caf0d25e2736d4b68ea6e283178f`; CI run `35986527136` concluded `success`.
- Live-health noncritical scan-warning commits `3b3c12baf1568803222f66e76ab1f717eb774ad4`, `7815e3f354f8d85af6a66f3fb4d66237cd755afd`; CI run `35986620061` concluded `success`.

## Validation still required before final PASS

1. **Core-line / reference / entry precision review** across a broad real-chart sample.
2. **False Positive review**: identify structures promoted by the scanner that a disciplined chart review should reject, then tune only evidence-backed gates.
3. **False Negative review**: identify high-quality charts missed by the scanner and determine whether the miss is data, feature extraction, threshold or ranking.
4. **Historical Replay expansion**: the persisted report now contains nine calibration controls, including source-labeled positive/B+ cases, but it is still too small to be a statistical precision test. Add negative controls and more entry/resistance examples before calling precision PASS.
5. **Intraday Market/Turnover Ignition + NEW CHALLENGER validation** on a real KRX session, including whether the live scan actually covers enough of the market to replace manual HTS monitoring.
6. **Real-session E2E** after Worker/security deployment: 08:15 -> secure watchlist sync -> 09:00~09:40 minute history -> live-health -> 09:35 -> 09:40 -> Evidence/NEXT_SESSION.

## What 'precision NOT DONE' means

The code path exists and automated invariants can pass, but we have not yet proven that detected core zones, reference candles, Jindol/Gadol, retests, entries/invalidation and next resistance match high-quality chart review across a sufficiently broad sample. Implementation PASS is not trading-quality PASS.

## Explicit non-goal

No user-facing rectangle/box drawing is required. Supply/box structure is an internal feature used to derive actionable prices.
