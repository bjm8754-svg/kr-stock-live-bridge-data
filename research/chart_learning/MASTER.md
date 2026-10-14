# V3 Chart Research MASTER

Version: **v9 / 2026-10-14 KST**. Source of truth for chart judgement continuity. **Not a trading signal.**

## End objective

Build a system that independently **discovers appropriate stocks**, understands market regime and chart context, designs an evidence-backed entry (and optional second buy), structural invalidation and resistance-derived targets, and generates real **risk-adjusted tradable results**. The expert's five recommended plans benchmark competence; they are **not** numerical recipes or demonstrated fills. Accurate-looking levels alone do not demonstrate edge.

Keep the V3 scanner / deep-review / evidence integration / live confirmation architecture. **PRODUCTION remains unchanged until independent validation and explicit user instruction.**

## Minimum measurable ambition (binding user requirement)

**Independent, cumulatively improving trade-judgement AI** is the actual goal. The **minimum bar** is comparable independent candidate discovery and conditional plan quality to the author of the five expert plans in C-001. It is not sufficient to imitate the same stock/levels/style; the quality must be demonstrated on unknown, point-in-time markets and linked to realistically executable economic outcomes. Current status: **NOT YET DEMONSTRATED**. See [MINIMUM_COMPETENCE_BENCHMARK.md](MINIMUM_COMPETENCE_BENCHMARK.md) for M-01 through M-07, the explicit acceptance gate and limitations. No source method or named educator gains priority from being well documented.

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

### R-010 — Analytical pluralism: no single analyst's view governs V3
**Yangbongman (YBM) is ONE VIEW among many, not the centre or master framework.** The same is true of the 91-photo Canonical, Fibonacci, indicator schools, volume/market-profile interpretations, CVD/order-flow, trend-following, fundamentals/catalysts, and any future expert. These sources contain useful **testable ideas**, not mandatory prescriptions. Start from observable market behaviour and the investment problem, then select applicable lenses according to market regime, timeframe, evidence quality and trade horizon. Different lenses may conflict: record the contradiction, prioritize price/volume/time evidence, independently assess the hypotheses, and leave a trade unresolved when evidence is insufficient. Do **not** award points for the number of lenses agreeing, give any source automatic authority, or rebuild the engine around one teacher. Retain each source's original claims and limitations for audit. This is a **user-defined scope rule**, not an empirically verified predictive advantage. See L-009.

### R-011 — Review interval is NOT swing holding horizon
**Never confuse a 3-trading-day decision/review cadence with a three-day swing holding limit or outcome horizon.** A swing thesis can validly survive several weeks or months, depending on structure, market regime, catalyst and risk. Update HOLD / ADD / REDUCE / EXIT decisions at reviews; do not force exit, target achievement or verdict because a scheduled review arrived. Check structural stop breaches continuously at available daily bars; a scheduled deep review must not delay risk exits. Before locking a plan, specify intended thesis **time horizon**, time-based invalidation if justified, structural invalidation, target/catalyst checkpoints and the circumstances that require early exit. Backtests must separate **(a) monitoring/review frequency, (b) per-position lifetime, (c) episode duration and (d) final scoring**. Where a portfolio experiment ends with positions still open, report mark-to-market unrealized P&L and mark unfinished trade outcomes as **right-censored**, not realized winners/losses; preserve capital, fees and benchmark accounting. A 30-session episode may diagnose tactical/short swing judgement but **cannot conclusively evaluate multi-month swings**; add longer independent episodes rather than inventing a universal holding period. See L-010 and C-005.

### R-012 — A HOLD decision must preserve share count
An assistant's `HOLD` signal means **no buy and no discretionary sell**, while structural stop orders remain active; naturally changing portfolio weight is not an instruction to rebalance. `ADD` and `REDUCE` require explicit intention and correct order direction. The legacy S01 runner `scripts/stock_blind_walkforward.py` currently uses target weights to buy/sell **even for `HOLD`**, which may distort turnover, capital allocation and winners held through multiweek trends. It is a known, **UNFIXED** simulator limitation, not evidence of model trading judgement. Existing D00–D04 locked decisions and their baseline replay must NOT be silently rewritten. Strict-HOLD semantics have an isolated, tested **prototype only**, not wired into running S01 or production. See `research/stock_blind/ORDER_SEMANTICS_V2.md`, L-011 and C-006. A separate versioned episode with a frozen engine must evaluate genuine buy/hold/scale/exit behaviours; don't compare PnL across different execution contracts without clear labels.

### R-013 — Data cutoff invariants outrank a boolean futureIncluded flag
Every price/index dataset MUST be clipped by its true timestamp <= locked decision cutoff **before** indicators, scanning, replay-facing chart traces, or assistant inspection. Provider-inclusive end dates can yield the next trading day's OHLCV even when a wrapper claims `futureIncluded: false`. On new card creation compare the two existing holdings' full-resolution closing prices with portfolio mark-to-market state for the same cutoff. Reject daily chart labels after the cutoff (such as `T+1D`). If the cross-check fails, **quarantine that episode's blind performance** rather than refining old decisions with newly observed future information. S01 is known contaminated as of D05; its prior D00–D04 decisions may also have seen next-day bars and cannot be rehabilitated retroactively. The S02 engine is a new isolated research-only fork; its tested synthetics guard essential look-ahead vectors, but only its actual forward run can demonstrate data integrity. See L-012 / C-007 and `research/stock_blind/PROTOCOL_V2.md`.

## HYPOTHESES — research only, not hard-coded into V3

### H-001 — Expert sample may use comparable average-basis risk
On an **unconfirmed** assumption of equal-money 1:2 allocation (first buy one monetary unit, second buy two units), four out of five expert examples showed simulated post-add stop exposure near 8–11%; one exceeded 20%. Tiny sample and possible retrospective selection invalidate adopting a universal 10% rule. The expert's actual capital plan is **not verified**. See L-004.

### H-002 — Three entry modes could reduce missed moves
The restricted Sep-18 diagnostic produced two unfilled pullback orders for later winners. An alternative breakout continuation path **may** reduce cash drag but may also worsen chase and losses. Must compare precommitted modes out of sample; do not treat this as already demonstrated. See L-005, L-006.

## Checklist before any recommendation

- Identify historical/current **cutoff**, data provider, session and price adjustment; verify freshness and valid tick.
- Begin with market evidence, then use relevant analytic perspectives without assuming any named analyst is the controlling view; reconcile disagreements or abstain.
- State market/sector regime and scan-universe selection without future leakage.
- Independently identify major daily / weekly / monthly acceptance and supply zones.
- Choose trade family and correct order semantics; record buy price, **optional add**, stop, target(s), cancellation, and thesis-dependent holding horizon **separate from review frequency**.
- Compute single-entry risk AND post-add risk if applicable, realistic ATR/gap risk, R/R and trade size.
- Separate **PLAN / FILLED / TESTED / LIVE**. Log opportunity costs, misses and all rejected setups.

## Original source inheritance (required)

The earlier learning is **NOT limited to** this concise MASTER. **First read `SOURCE_REGISTRY.md`**. It points to the ChatGPT Library archive of all **91** original 2026-09-28 source PNGs and the `차트공부_CANONICAL_MASTER_FINAL_20260929.docx` (including 91-image index), plus the Yangbongman `KakaoTalkChats.txt` export and original GitHub methodology audit. The original Yangbongman picture files behind text-only `사진` placeholders have **not** been proven fully archived. Never treat image-index summaries as full image inspection, and preserve unresolved source ambiguities.

YBM is **one optional historical analytical lens among multiple perspectives**, not the foundation, controlling school, preferred lens or return to governing V3 rules. Its strongest observable learnings — reference candle, trading-value/volume, base, cloud, price role and real breakout acceptance — remain available for comparative study without reintroducing numeric scoring dogma.

## Direct references

- Detailed chart judgement: ../.. /ASSISTANT_CHART_DEEP_REVIEW_PROTOCOL.md (repository root, without the inserted space in this explanatory path)
- Architecture: MARKET_STRUCTURE_V3.md at repository root
- Evidence and mistakes: LESSONS.jsonl and CASES.md
- Test outcomes: EXPERIMENTS.md
- Research process: RESEARCH_PROTOCOL.md

**Do not delete CANONICAL rule IDs.** Revisions must preserve IDs as SUPERSEDED with rationale, counterevidence and a linked replacement after independent verification.
