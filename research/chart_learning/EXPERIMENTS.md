# Experiments and non-regression scorecard

The research account has **no verified forecasting performance** as of revision 6. It has useful diagnostics; do not equate them with economic skill.

| ID | Cutoff / window | Method | Observed result | Validity | Next step |
| --- | --- | --- | --- | --- | --- |
| E-001 | 5 user-supplied expert plans, Sep–Oct 2026 | Known-price chart reverse engineering | Some apparent Fibonacci/structure matches; not independently derived | DIAGNOSTIC / outcome contamination | Re-run with hidden levels and unseen picks |
| E-002 | 2026-10-13 EOD V3 top 10 from 33 | Crash-regime machine-vs-human assessment | 0 approved trades; unrealistic invalidations found | DIAGNOSTIC, not stock-picking skill | Compare multiple regimes and valid stops |
| E-003 | 2026-09-18 cutoff, 2026-09-21–10-13 follow-up | Time-truncated data within future-selected 33 stocks | 6 screened; 3 proposed; 1 plan's targets touched after 1st buy, 2 unfilled; no cost-adjusted portfolio return | SELECTION-BIASED RETROSPECTIVE DIAGNOSTIC / NOT BLIND | Full KRX point-in-time lock and conservative execution |
| E-004 | pre-existing historical stock_blind S01 | Repo has independent universe reconstruction and locked decisions for a different hidden period | Existing state shows 4 locked steps, not a concluded proof of 2026 September selection | SEPARATE ONGOING RESEARCH | Use existing protocols without claiming it was this study |

## Minimum competence evaluation

All future experiments must be evaluated against [MINIMUM_COMPETENCE_BENCHMARK.md](MINIMUM_COMPETENCE_BENCHMARK.md) M-01 through M-07. This benchmark sets the five-plan expert as the **minimum qualitative standard**, while acknowledging that their actual track record is unknown. Do not present a diagnostic paper gain as minimum-level proficiency.

## Scorecard template for each future locked experiment

- Study ID / learning revision / GitHub source commit:
- Market regime, exchange universe size, delisting coverage, cutoff and point-in-time feeds:
- Candidate-selection policy frozen at:
- Recommendation decision commit hash and timestamp, cutoff, order semantics and position limits:
- Proposed candidates + rejected candidates + selection rationale:
- First buy, optional second buy, structural invalidation, first/final target, expiry/cancel rules:
- Reproducible fill accounting (gaps, same-bar low/high ambiguity, fees, transaction tax where applicable):
- Entry coverage, non-fill rate, hit/stop/time-out rates, per-trade expectancy:
- Turnover, max drawdown, volatility, invested ratio, capital-weighted benchmark/alternative cash yield:
- Case-level postmortem including wrong stock selection and missed moves:
- Verdict: IMPROVED / REGRESSED / INCONCLUSIVE / NOT TESTED (never infer from a handful of winning charts):
- Linked lesson IDs, rule status changes, reproducible source files:

Do **not** mark any experiment PASS without the frozen pre-result decision artifact and market-appropriate execution and cost assumptions. Avoid selecting only famous future winners for validation.
