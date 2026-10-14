# Experiments and non-regression scorecard

The research account has **no verified forecasting performance** as of revision 9. It has useful diagnostics; do not equate them with economic skill.

| ID | Cutoff / window | Method | Observed result | Validity | Next step |
| --- | --- | --- | --- | --- | --- |
| E-001 | 5 user-supplied expert plans, Sep–Oct 2026 | Known-price chart reverse engineering | Some apparent Fibonacci/structure matches; not independently derived | DIAGNOSTIC / outcome contamination | Re-run with hidden levels and unseen picks |
| E-002 | 2026-10-13 EOD V3 top 10 from 33 | Crash-regime machine-vs-human assessment | 0 approved trades; unrealistic invalidations found | DIAGNOSTIC, not stock-picking skill | Compare multiple regimes and valid stops |
| E-003 | 2026-09-18 cutoff, 2026-09-21–10-13 follow-up | Time-truncated data within future-selected 33 stocks | 6 screened; 3 proposed; 1 plan's targets touched after 1st buy, 2 unfilled; no cost-adjusted portfolio return | SELECTION-BIASED RETROSPECTIVE DIAGNOSTIC / NOT BLIND | Full KRX point-in-time lock and conservative execution |
| E-004 | historical stock_blind S01 (legacy execution) | Reconstructed full market; D00–D04 frozen decisions; D04 3-session interval return -0.325%, cumulative +0.268% after 15 sessions | **FUTURE-DATA CONTAMINATED:** D05 card includes one more day than D05 settled equity; plus legacy HOLD rebalancing. The original D00–D04 decisions may have been similarly exposed | INVALID FOR CLEAN BLIND EDGE / DIAGNOSTIC ONLY | Quarantine old episode, preserve all commits; do not continue as clean study |
| E-005 | S01 D04 decision locked at commit `a33da5e9...` | Held A91/A0E; 18 candidates reviewed; no new buys | Subsequent 3-session result -0.325%, no stop; **D04 analysis was made from a card produced by the same unfiltered source mechanism** and cannot establish forward-time predictive skill | CONTAMINATED PROCESS / RESEARCH CASE ONLY | Use S02 from clean time cutoff and preserve this adverse example |
| E-006 | S02 newly versioned 60-session blind | Separate strict-HOLD and timestamp-clipped V2 engine with explicit tests; 3-session checks, potentially multiweek holding | New study configured; no trading decision or outcome as of research revision 9 | NOT TESTED / WORKFLOW STATUS MUST BE VERIFIED | Generate initial masked card only after pure contract tests pass; lock all decisions before outcome |

## Swing horizon correction (L-010 / R-011)

The existing `research/stock_blind/ACTIVE_EPISODE.json` sets `stepSessions: 3` (a **decision review interval**) and `episodeSessions: 30` (experimental duration), **not a three-session holding cap**. The replay engine retains positions across interval boundaries unless acted on/stopped; stops check intervening session bars. A 30-session window is a limited **shorter-horizon diagnostic**, not proof of skill at several-week or multi-month swing holds. Episode completion reports portfolio mark-to-market, and open positions must be flagged as ongoing / censored for trade-outcome analysis. Compare longer independently locked episodes spanning multiple regime changes, with separate outcome windows for entry quality, thesis development and final realized disposition. Do not enforce 3/5/10/20 sessions as a universal exit clock.

## Minimum competence evaluation

All future experiments must be evaluated against [MINIMUM_COMPETENCE_BENCHMARK.md](MINIMUM_COMPETENCE_BENCHMARK.md) M-01 through M-07. This benchmark sets the five-plan expert as the **minimum qualitative standard**, while acknowledging that their actual track record is unknown. Do not present a diagnostic paper gain as minimum-level proficiency.

## Scorecard template for each future locked experiment

- Study ID / learning revision / GitHub source commit:
- Market regime, exchange universe size, delisting coverage, cutoff and point-in-time feeds:
- Candidate-selection policy frozen at:
- Recommendation decision commit hash and timestamp, cutoff, order semantics and position limits:
- Proposed candidates + rejected candidates + selection rationale:
- First buy, optional second buy, structural invalidation, first/final target, thesis-dependent holding horizon, planned reviews, expiry/cancel rules:
- Reproducible fill accounting (gaps, same-bar low/high ambiguity, fees, transaction tax where applicable):
- Entry coverage, non-fill rate, hit/stop/time-out rates, right-censored open positions versus realized trades, per-trade expectancy:
- Turnover, max drawdown, volatility, invested ratio, capital-weighted benchmark/alternative cash yield:
- Case-level postmortem including wrong stock selection and missed moves:
- Verdict: IMPROVED / REGRESSED / INCONCLUSIVE / NOT TESTED (never infer from a handful of winning charts):
- Linked lesson IDs, rule status changes, reproducible source files:

Do **not** mark any experiment PASS without the frozen pre-result decision artifact and market-appropriate execution and cost assumptions. Avoid selecting only famous future winners for validation.
