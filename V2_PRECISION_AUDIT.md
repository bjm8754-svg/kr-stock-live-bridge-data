# V2 Precision Audit

Evidence-only calibration record. Source labels are calibration controls, not ground truth: production logic is changed only when the mismatch exposes a defensible structural defect.

## Current calibration set

| Case | Source evidence | System result after current fix | Status |
| --- | --- | --- | --- |
| SFA Semiconductor 036540 / 2026-09-09 | source later states this was found as an A-grade example | chart B_PLUS; GADOL_RISK; timing RADAR | PARTIAL — discovery false-negative fixed; exact A mapping intentionally not forced |
| Fine M-Tec 441270 / 2026-09-03 | source calls it A-grade | chart B_PLUS; MA600_BREAKOUT; qualified, timing RADAR | PARTIAL — discoverable; exact A mapping intentionally not forced |
| Kumkang Steel 053260 / 2026-09-03 | source upgrades it to trading B+ after catalyst review | chart B_PLUS; timing RADAR/GADOL | PASS for structural discovery; catalyst-driven final trading rank is outside chart grade |
| Korea Kolmar 161890 / 2026-07-02 | source calls the setup A-grade and describes supply/prior-high breakout | chart B_PLUS; timing RADAR | PASS for discovery floor; exact A mapping not asserted |
| Samwha Capacitor 001820 / 2026-05-20 | source calls it A-grade | chart A; JINDOL_CONFIRMED; WATCH_TRIGGER | PASS |
| Vinatech 126340 / 2026-09-16 | source calls it B+ | chart B_PLUS; timing RADAR | PASS for chart-quality label; timing remains independently stricter |
| Sammi Metal 012210 / 2026-09-10 | source reviews deoyang/cloud breakout and Yang-Eum-Yang sequence | chart B_PLUS; RETEST_OK | PARTIAL — structure aligns, execution-line precision still under review |

Persisted replay evidence: `v2-replay-report.json`. Source labels are now treated only as a discovery floor, not an exact A/B+ reproduction target. Replay semantics commit `bf8ce822011b12dcef1353525af10e19d2a841b5`; run `35985452972` concluded success.

## False-negative correction already made

Old chart-grade logic could permanently reject a fresh, money-backed long-structure setup when an obsolete historical reference candle had failed. That contradicted fresh discovery: a past failed reference should not blacklist a new valid structure.

Fix:
- scanner commit `790b0f7c22749937115b427ff6179741867de5e1`
- regression-test commit `da0f7467fe692e46b1f798ed95c1570bee3732fc`
- replay run `35983214293` / success
- full-market run `35983214306` / success

The fallback is capped at B+. S/A still require a usable strong reference, preventing a single correction from inflating top grades.

## Execution-line evidence

Kumkang Steel source guidance on 2026-09-03 was that the 5,800–6,000 area should hold for the upside thesis. The replayed structural engine produced nearest support 5,759.58. That is 0.70% below the source range's lower edge. This is close structural agreement, but one example is insufficient for a general PASS.

The source hierarchy emphasizes strong-reference open/close first, then meaningful prior highs / congestion / round figures, then moving averages. `entryPlan` now preserves that hierarchy explicitly under `supportHierarchy` while leaving the existing nearest-support ranking logic unchanged. It separately exposes primary reference support, reference-low invalidation candidate, tactical/core support, and nearest long-MA support, so one tactical level no longer hides the thesis support.

## Remaining precision gates

- **Support hierarchy — PASS (implementation/contract):** scanner commit `fa542131f115c28e7b52e03871735183a36e445f`; regression-test commit `9af79231c5a036efaa7c2cc745a709b22081be87`; replay run `35984560851` concluded success. Levels remain observed structure only; no arbitrary percentage level is manufactured.
- Compare support / invalidation / next-resistance levels against additional source examples with explicit prices.
- Add explicit negative controls for non-ABC / weak-money setups where safely reproducible.
- Review false positives where chart grade is strong but liquidity, market cap, catalyst quality or current R/R make the trade unattractive; keep chart quality separate from timing/action quality.
- Expand replay beyond the current small calibration set before assigning any statistical precision rate.
