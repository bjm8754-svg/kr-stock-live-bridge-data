# V3 Chart Research MASTER

Version: **v1 / 2026-10-14 KST**. Source of truth for chart judgement continuity. **Not a trading signal.**

## End objective

Build a system that independently **discovers appropriate stocks**, understands market regime and chart context, designs an evidence-backed entry (and optional second buy), structural invalidation and resistance-derived targets, and generates real **risk-adjusted tradable results**. The expert's five recommended plans benchmark competence; they are **not** numerical recipes or demonstrated fills. Accurate-looking levels alone do not demonstrate edge.

Keep the V3 scanner / deep-review / evidence integration / live confirmation architecture. **PRODUCTION remains unchanged until independent validation and explicit user instruction.**

## CANONICAL — must be applied in all future analysis

### R-001 — Point-in-time integrity
Do not inspect future prices, later-selected names or historical outcome when constructing a purported blind recommendation. When using a future-selected universe, label the exercise **selection-biased diagnostic**, not blind. Precommit prices and conditions **before** subsequent outcome evaluation. See L-001, L-006.

### R-002 — Independent reasoning precedes numerical matching
The problem is original judgement, **not** matching an expert's known exact numbers or a scanner's setup label. Reconstruct multiple timeframes, price/volume/time and supply/demand acceptance first; only then write prices. Mark exact-price coincidences as potentially cherry-picked, not proof. See L-001.

### R-003 — Structural invalidation must survive realistic volatility
A price below entry is not automatically a valid stop. Evaluate actual broken structure, normal daily true range/ATR, gaps and feasible R/R **at first entry and after any add**. Reject unrealistic stops or untradeable tick fractions, even if the computed R/R is extraordinary. See L-002, L-003.

### R-004 — A suggested buy is not an executed fill
First-buy, optional second-buy, stop and targets are **conditional orders/plans**. Buy recommendations are not evidence trades occurred. Backtests must model order mechanics, gap-through, same-candle sequencing ambiguity, non-fills, fees and slippage. A buy level above the market requires an explicit breakout/stop-trigger design, not a naive buy limit. See L-004, L-006.

### R-005 — Entry strategy depends on pattern and opportunity cost
Assess pullback entry, breakout acceptance/retest and strong-trend continuation **as distinct alternatives**. Avoid a forced add-buy, forced 1:2 allocation, forced stop percentage, or universal Fibonacci formula. Record missed winners due to orders never touched. See L-005.

### R-006 — Price progress versus participation
High aggressive-buy delta/CVD without upward price progress at resistance may indicate sell-side absorption, not straightforward strength. Confirm whether price makes new highs and holds them. **Never compare absolute CVD levels with different reset/anchor periods**; ordinary time-based volume does not prove a volume void (use a true volume profile when needed). See L-007.

### R-007 — Market regime, source freshness and data validity first
Assess regime/sector pressure before promoting a plan. If the market is in a hard breakdown, a no-trade decision is **risk management, not proof of entry selection skill**. Reconcile OHLCV vendors, corporate actions, session definitions and KRX tick sizes before executable output. See L-003, L-008.

### R-008 — Measure economic performance, not good-looking prose
Track executed trades **and non-fills**, signal timing, maximum adverse excursion, realized cost-adjusted return, maximum drawdown, benchmark regime, turnover, cash drag and false negatives. Require an out-of-sample comparison before declaring improvement. See L-006, L-008.

### R-009 — Visible uncertainty; no fake PASS
Label findings as VERIFIED / DIAGNOSTIC / HYPOTHESIS / NOT_TESTED; distinguish simulated outcomes from actual live performance. Never claim GitHub commits, scheduled jobs, downstream health, current market quotes, or repeatability without successful checks. See L-006, L-008.

## HYPOTHESES — research only, not hard-coded into V3

### H-001 — Expert sample may use comparable average-basis risk
On an **unconfirmed** assumption of equal-money 1:2 allocation (first buy one monetary unit, second buy two units), four out of five expert examples showed simulated post-add stop exposure near 8–11%; one exceeded 20%. Tiny sample and possible retrospective selection invalidate adopting a universal 10% rule. The expert's actual capital plan is **not verified**. See L-004.

### H-002 — Three entry modes could reduce missed moves
The restricted Sep-18 diagnostic produced two unfilled pullback orders for later winners. An alternative breakout continuation path **may** reduce cash drag but may also worsen chase and losses. Must compare precommitted modes out of sample; do not treat this as already demonstrated. See L-005, L-006.

## Checklist before any recommendation

- Identify historical/current **cutoff**, data provider, session and price adjustment; verify freshness and valid tick.
- State market/sector regime and scan-universe selection without future leakage.
- Independently identify major daily / weekly / monthly acceptance and supply zones.
- Choose trade family and correct order semantics; record buy price, **optional add**, stop, target(s), and cancellation.
- Compute single-entry risk AND post-add risk if applicable, realistic ATR/gap risk, R/R and trade size.
- Separate **PLAN / FILLED / TESTED / LIVE**. Log opportunity costs, misses and all rejected setups.

## Direct references

- Detailed chart judgement: ../.. /ASSISTANT_CHART_DEEP_REVIEW_PROTOCOL.md (repository root, without the inserted space in this explanatory path)
- Architecture: MARKET_STRUCTURE_V3.md at repository root
- Evidence and mistakes: LESSONS.jsonl and CASES.md
- Test outcomes: EXPERIMENTS.md
- Research process: RESEARCH_PROTOCOL.md

**Do not delete CANONICAL rule IDs.** Revisions must preserve IDs as SUPERSEDED with rationale, counterevidence and a linked replacement after independent verification.
