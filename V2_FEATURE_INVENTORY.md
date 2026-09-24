# V2 Feature Inventory

Purpose: distinguish `implemented` from `precision-validated`. A field existing in JSON is not considered final trading-quality validation. This inventory is the evidence-only contract for the originally agreed V2 scope.

## After-close structural scanner contract

| Feature | Implementation evidence | Automated contract/test | Precision status |
| --- | --- | --- | --- |
| ABC long-decline/base/recovery | `abc_features`, `abc` output | output-contract test | NOT DONE |
| Strong reference candle / 더양봉 | `rolling_event_mask`, `deoyangbong`, active reference anchor | reference-candle grading tests | NOT DONE |
| Core resistance / supply zone / 네모네모 internal logic | `build_core_resistance`, clustered `coreResistance` | core clustering + pre-current construction | NOT DONE |
| Long MA structure | MA20/60/120/240/480/600/1000 | output-contract test | NOT DONE |
| Ichimoku cloud | `cloud` | output-contract test | NOT DONE |
| Money / turnover quality | absolute trading value, avg20 ratio, volume ratio, relative reference money, market-cap turnover | breakout/action tests | NOT DONE |
| Jindol / Gadol | `breakoutClass`, `classify_breakout` | JINDOL/GADOL tests | NOT DONE |
| Pre-Jindol | `preJindol` | output-contract test | NOT DONE |
| Acceptance / follow-through | Jindol close acceptance + `actionScore.components.acceptance` | action-score test path | NOT DONE |
| Retest + supply contraction | `retestOk`, `retestSupply` | output-contract test | NOT DONE |
| Reacceleration | `reacceleration` / Yang-Eum-Yang | output-contract test | NOT DONE |
| New-listing separate rail | `track=NEW_LISTING`, `newListingSetup` | synthetic new-listing test | NOT DONE |
| Structural entry / support / next resistance / R-R | `entryPlan` from detected structure only | no-arbitrary-price implementation + output contract | NOT DONE |
| Chart quality S/A/B+ independent of timing | `chartGrade`, `chartCandidates` | chart-grade independence/reference-integrity tests | NOT DONE |
| Fresh Action Score / anti-selection-memory | `actionScore` | selection-memory invariant test | NOT DONE |
| Compact canonical handoff | `YBM_BRIEF_V2` | compact-schema test | PARTIAL — current canonical scan is still the 2026-09-23 pre-chart-grade migration |

## Intraday operational contract

| Feature | Current evidence | Status |
| --- | --- | --- |
| 09:00~09:35/09:40 watched-symbol minute path | `live.json.history` + semantic freshness validator | IMPLEMENTED / REAL-SESSION REVALIDATION NOT DONE |
| Market Ignition | Canonical Master requires market/breadth/cluster ignition; `live.json` exposes indexes + scan | PARTIAL — no dedicated deterministic regression test for ignition classification |
| Turnover Ignition | Canonical Master requires absolute turnover, acceleration and same-time-relative expansion where available | PARTIAL — current live scan is not yet proven to provide full-market same-time turnover acceleration |
| NEW CHALLENGER outside morning watchlist | Canonical Master requires competition against the existing watchlist using live market scan evidence | PARTIAL — operational contract exists, but full-market discovery coverage and regression test are not yet proven |
| 08:15 plan vs actual follow-through | 09:35/09:40 Master contracts + minute path | IMPLEMENTED / REAL-SESSION REVALIDATION NOT DONE |
| Trigger / Retest / Reacceleration intraday confirmation | Master maps completed-daily setup to actual minute path | IMPLEMENTED / PRECISION NOT DONE |

## Current automated evidence

- Feature-contract/self-test change commit: `87b3e492974869c63c701223e951a399f8a1e937`.
- Historical replay check for that commit: `success` (`35977284215`).
- Full-market scan check from the same commit: `success` (`35977284250`). On the 2026-09-24 non-trading day, validation passed and the canonical commit step was correctly skipped rather than overwriting the prior trading-day canonical.
- Current `scripts/test_longterm_scan_v2.py` explicitly checks the agreed structural field contract, long-MA keys, Jindol/Gadol boundary, new-listing rail, selection-memory independence and chart-grade/reference integrity.

## Validation still required before final PASS

1. **Core-line / reference / entry precision review** across a broad real-chart sample.
2. **False Positive review**: identify structures promoted by the scanner that a disciplined chart review should reject, then tune only evidence-backed gates.
3. **False Negative review**: identify high-quality charts missed by the scanner and determine whether the miss is data, feature extraction, threshold or ranking.
4. **Historical Replay expansion**: current `replay_validate_v2.py` is a four-case calibration report, not a statistical precision test. Expand to positive and negative cases and record expected/actual state transitions.
5. **Intraday Market/Turnover Ignition + NEW CHALLENGER validation** on a real KRX session, including whether the live scan actually covers enough of the market to replace manual HTS monitoring.
6. **Real-session E2E** after Worker/security deployment: 08:15 -> secure watchlist sync -> 09:00~09:40 minute history -> live-health -> 09:35 -> 09:40 -> Evidence/NEXT_SESSION.

## What 'precision NOT DONE' means

The code path exists and automated invariants can pass, but we have not yet proven that detected core zones, reference candles, Jindol/Gadol, retests, entries/invalidation and next resistance match high-quality chart review across a sufficiently broad sample. Implementation PASS is not trading-quality PASS.

## Explicit non-goal

No user-facing rectangle/box drawing is required. Supply/box structure is an internal feature used to derive actionable prices.
