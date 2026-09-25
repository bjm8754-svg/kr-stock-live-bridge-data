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


## Additional FP/FN evidence

- **Low-money negative control — PASS:** Hanseong Clean Tech 066980 / 2026-05-20 was source-labeled as pattern-compatible but not A-grade because volume/money were insufficient. Replay case CASE_J produced `BELOW_B_PLUS`, `qualified=false`, Action Score 18.8 / RADAR. Replay commit `7b62676c385262a5d7e9d01ce3ce3ead492d26f5`; run `35985982065` concluded success.
- **Source-level calibration — PASS for two explicit examples:** replay commit `ccbb4b4db718c5e9d1e589d4ecf078f3d03cf9b6`; run `35986185265` concluded success. Sammi Metal's source 10,000 reference was matched by structural reference-low 10,040 (0.4% gap). Kumkang Steel's source support 5,800~6,000 was matched by core support 5,759.58 (0.685% below the range). These are calibration matches, not a statistical precision claim.
- **Positive discovery controls:** six source-labeled A/B+ examples currently all meet at least the B+ discovery floor in replay. This supports FN control but is still too small to claim a population precision/recall rate.


## Structural R/R invalidation separation

The prior ranking R/R used the nearest structural support as the risk denominator. That was too optimistic when the actual thesis invalidation sat deeper than the nearest tactical support.

- scanner commit `834f13b92cbe0b5eb64dfe03d40ff281faded45e`
- regression-test commit `38c033e1dfcb5287ca4b53f004772ecfc2abb937`
- replay run `35987234904` concluded success

Current rule:
1. nearest support remains the extension/ranking reference;
2. invalidation prefers the active strong-reference low;
3. if no valid reference exists, core-zone low can serve as structural invalidation;
4. a long MA by itself is context, not a hard invalidation;
5. structural R/R is calculated from current evaluation reference to the explicit invalidation and next resistance; if either is absent, R/R is null.

This change intentionally lowers some historical R/R values rather than manufacturing a tighter stop to make the trade look better.


## Cross-sectional invariant sweep

A full-market structural-level validator is now part of the scanner workflow. It checks that structural R/R is traceable to observed invalidation/target levels, forbids long-MA-only hard invalidation, validates R/R arithmetic, and verifies reference/core invalidation provenance.

- validator commit: `58a5ddb2dd53f99afcc6a07d0490b21816627737`
- corrected invariant commit: `cdb4e911612d152f1144bb92cc10ea038e9202f6`
- full-market run: `36122568757`
- conclusion: `success`

The first validator run deliberately failed because it assumed invalidation must always sit below the selected ranking support. Artifact inspection showed that assumption was wrong: ranking support intentionally ignores levels that are too close to current price, while a valid reference-low invalidation can sit above the deeper ranking support. The validator was corrected to test traceability instead of enforcing the false ordering. This was a validator defect, not hidden by loosening the scanner.


## ABC / new-listing separation

Replay commit `06609a39733001b5efe0af610845c73d10d46be4`; run `36126782084` concluded success; persisted report SHA `f22e2ed84d463f969215abf44095725f975805e9`.

- **CASE_C / 064400 / 2026-05-12:** source-labeled real new-listing small-ABC example. System returned `track=NEW_LISTING`, `signal=NEW_LISTING_SETUP`, chart grade `B_PLUS`, qualified=true. Both source discovery floor and new-listing setup alignment are `MATCH`.
- **CASE_K / 255440 / 2026-08-18:** source-labeled ABC candidate that was separately deprioritized in the source context. System returned `signal=ABC_CANDIDATE` and ABC alignment `MATCH`, but chart grade `BELOW_B_PLUS`, qualified=false, Action Score RADAR because strong-reference/money quality was insufficient.

This is desirable separation: recognizing an ABC-shaped structure does not automatically promote it to a tradable A/B+ candidate. Structural recognition and execution quality remain separate layers. These two cases improve calibration coverage but do not justify a population precision/recall claim.
