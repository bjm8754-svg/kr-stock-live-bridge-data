# Research, promotion and non-regression protocol

## Evidence ladder

1. **OBSERVATION**: isolated plausible chart observation (including user examples). No claim of repeatability.
2. **DIAGNOSTIC**: historical chart review, restricted-universe retrospective analysis, synthetic test, or known-outcome reconstruction. Useful for detecting mistakes, not predictive performance.
3. **LOCKED OUT-OF-SAMPLE**: cutoff, entire eligible universe, deterministic selection and all proposed prices committed before outcome reveal. Keep poor picks and no-fills.
4. **SHADOW VERIFIED**: forward-time EOD/08:15/09:35/09:40 with checked data freshness, end-to-end recorded orders/decisions and cost model.
5. **PRODUCTION**: separate explicitly authorized cutover. Research must never cause it.

Do not promote levels in steps 1–2 as a measured edge.

## Research loop

- Register question, candidate hypothesis, what would falsify it, baseline comparator and market regimes to test.
- Freeze data, universe, cutoff, selection criteria, price conditions, stop/cancellation, position sizing, handling of not-filled orders, **per-setup holding horizon, review cadence, episode duration, execution-engine revision, action-to-order semantics (especially HOLD), and endpoint accounting** before outcome exposure.
- Keep complete cohort and all rejections; make results reproducible with input provenance and code/data commit.
- Examine fills, ambiguous intrabar order, costs, turnover, drawdown, cash drag and missed winners. Never score 3-session review windows as forced swing exits; **do not count weight-target rebalancing under a HOLD label as genuine uninterrupted holding;** at episode end distinguish unrealized portfolio mark-to-market from fully realized and right-censored trade outcomes. Use market-adjusted benchmark and stress regime.
- Log new mistake as a unique **L-###** append-only LESSONS.jsonl record; connect to a case and experiment.
- Only promote to a CANONICAL rule if independent evidence improves performance/decision validity; otherwise keep HYPOTHESIS. Carry old rule IDs forward with SUPERSEDED annotation rather than deleting.
- Update MASTER + CHANGELOG + MANIFEST revision in **one atomic Git commit**. No model-memory claim is implied.

## Gate conditions and failure policy

Every V3 research session starts with GitHub current-HEAD read (START_HERE). An unverified gate is reported **NOT VERIFIED**; analysis may proceed only with explicitly qualified continuity and must not claim the complete research context.

Integrity automation checks required artifacts, rule consistency, lesson uniqueness and append-only history. It does **not** inspect market prices, schedule scans, trade, or guarantee correctness of the market model. If automation fails, correct the record before claiming persistent advancement.

All changes in this folder are documentation / test infrastructure. Production or scanner algorithm changes require a **separate task, tests and explicit approval**.
