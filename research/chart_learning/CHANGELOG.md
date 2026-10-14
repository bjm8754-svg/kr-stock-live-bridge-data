# Immutable learning change history

## 2026-10-14 — Revision 8 — Preserve HOLD semantics, isolate corrected order planner

- Found from `scripts/stock_blind_walkforward.py` that S01 rebalances any selected holding to `capitalPct` at each review independent of the nominal `HOLD`, `ADD` or `REDUCE` action label; legacy S01 therefore cannot unambiguously demonstrate genuine uninterrupted swing holding.
- Registered canonical R-012, lesson L-011 and case C-006. E-004/S01 is flagged LEGACY_REBALANCE_METHODOLOGY, and D04 outcome remains PENDING while replay runs.
- Added a **standalone, unit-tested but NOT integrated** order-intent v2 prototype and specification under `research/stock_blind/`: HOLD preserves quantities, ADD buys, REDUCE sells, ENTER opens and omitted existing position exits.
- Research CI tests the new pure planner without historical data downloads, orders, repo writes or production interaction.
- Historical S01 decisions, legacy simulation engine, live scanners and Production were NOT changed. A new versioned episode will be needed for fair strict-HOLD performance tests; v2 PnL is NOT VERIFIED.

## 2026-10-14 — Revision 7 — Separate three-day review from weeks-long swing horizon

- Confirmed existing S01 `stepSessions=3` is a periodic decision/review window, **NOT a required holding duration**; `episodeSessions=30` is the finite experiment window, not a sufficient assessment of multi-month swings.
- Examined actual replay code: positions persist across review cycles and structural stops check intervening daily bars. Final portfolio mark-to-market is not proof that open trades closed profitably.
- Added canonical R-011, mistake L-010 and case C-005 to prevent this analytical regression; updated research protocol, experiment scorecard, session start contract and validator.
- **Did not** modify S01, its locked decisions, shadow scan / auto-trade code or Production. Longer independent episodes need separate test design before implementation.
- No claim of improved predictive or realized returns.

## 2026-10-14 — Revision 6 — Explicit minimum competency goal

- Recorded user's binding requirement: **at least the independent chart selection and conditional plan-design quality of the analyst who authored the five example plans**; surpassing this is the longer-term goal.
- Created MINIMUM_COMPETENCE_BENCHMARK.md (M-01–M-07) for original stock discovery, coherent level plans, risk and execution, regime awareness, fair tests, and cumulative, non-regressing improvement.
- Restated that no named teacher is privileged, that matching the five prices is not a benchmark pass, and that the benchmark expert's **realized investment performance is unknown**.
- Added reference to MASTER / START_HERE / EXPERIMENTS / AGENTS, with read-and-test requirement. No model weight training, V3 algorithm change, production cutover, or profit claim.

## 2026-10-14 — Revision 5 — Non-regression assertion correction
- Revision 4 core documentation integrity passed but the additional test asserted a non-existent spelling of the correctly documented rule. Corrected the exact test phrase to check the actual `Yangbongman (YBM) is ONE VIEW among many` contract, retaining R-010 and L-009 unchanged.
- No trading engine, scanning, production or data files changed.

## 2026-10-14 — Revision 4 — Analytical pluralism and no privileged teacher
- User corrected the framing: **Yangbongman is one analytical view among many**, never V3's default or controlling lens. The existence of archived YBM material does not establish analytical priority.
- Added R-010 and L-009; explicitly require independent price/volume/time and market-regime judgement before choosing applicable study lenses, with disagreements recorded rather than forcibly averaged.
- Updated startup, source registry, MASTER and repository-aware agent directions to prevent regression into one-teacher imitation. This is a framing/scope correction, **not measured improvement in returns**.
- No change to V3 scanner/production/market-data workflows.

## 2026-10-14 — Revision 3 — Source-status consistency fix
- Retained all source references, lesson IDs and rules; explicitly labelled Yangbongman photo completeness as `UNVERIFIED` to match the source validator and manifest.
- Revision 2 integrity check failed on a status-token mismatch; did not claim PASS. Revision 3 repairs it without changing research conclusions or production.

## 2026-10-14 — Revision 2 — Original photo studies and Yangbongman source inheritance

- Verified 91/91 numbered PNG files in ChatGPT Library `/차트공부_원자료_20260928/images/` with no missing or duplicated 001–091 labels.
- Located `차트공부_CANONICAL_MASTER_FINAL_20260929.docx` and its 91-image source index, plus the earlier system-validation audit.
- Located Yangbongman text export `KakaoTalkChats.txt` in Library and source-vs-proxy audits `YBM_METHOD_AUDIT.md`, `YBM_V2_METHOD.md` in GitHub.
- Did **not** claim completeness of Yangbongman photo media: text export's '사진' placeholders are not images.
- Added SOURCE_REGISTRY.md and mandatory original-source lookup to START_HERE, AGENTS and MASTER; validator requires registry and reference links. CI cannot verify external Library assets.
- No changes to V3 production, chart algorithms or verified trading performance.

## 2026-10-14 — Revision 1 — Initial continuity gate

- Established research/chart_learning as the durable V3 learning authority, connected from README, AGENTS and the existing deep-review protocol.
- Converted recurring analytic errors into eight immutable lesson IDs (L-001 to L-008), nine CANONICAL guardrails (R-001 to R-009) and two unconfirmed hypotheses (H-001, H-002).
- Documented the five external expert recommendations as **a competence benchmark, not proof of actual fills**.
- Archived retrospective 2026-09-18 selection-biased 33-stock / 3-plan result, including two **unfilled** winners, without claiming blind predictive success.
- Added a lightweight repository integrity validator and path-scoped CI; no scheduler, production market-data fetch or trading write.
- No new predictive edge, improved PnL, or live trading readiness is claimed.

Future entries must specify prior and new revision, preserved rule IDs, linked lessons, evidence quality, adverse examples and exact validation result. An absent test is recorded as NOT TESTED, never as PASS.
