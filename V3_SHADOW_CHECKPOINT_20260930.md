# V3 Shadow Integration Checkpoint — 2026-09-30

Status: PAUSED AT REAL-SESSION SHADOW LIVE CAPTURE
Production cutover: NOT DONE
Production V8.6 / watchlist / live publisher state: UNCHANGED

## Governing architecture

V3, not YBM/V2, is the candidate-discovery/chart-judgement architecture under validation.

Flow:
`full market -> V3 prefilter -> bounded review packet -> assistant deep chart review -> external evidence lanes -> shadow plan -> live confirmation/cancellation`

V2 remains rollback/control only until explicit cutover.

## Completed validation

1. **V3 scanner / canonical invariants — PASS**
   - Run #38: `36589872813`, conclusion SUCCESS.
   - Generic regression PASS.
   - Full-market scan PASS.
   - Canonical invariant validator PASS.
   - Review-packet validator PASS.
   - DeepReviewQueue = 36.

2. **Deep Review quality — PASS**
   - Representative charts were re-read independently from machine setup labels.
   - Machine EXECUTABLE outputs were materially downgraded where location/invalidation/R-R were poor.
   - Aggregate scoring is not used.

3. **Investment integration logic — PASS**
   - Chart states connect to company/revision/catalyst/macro/US-lead/event-risk lanes.
   - External evidence can block chart promotion.
   - Final states remain ATTACK_PLAN / PROBE_PLAN / WATCH / PASS.

4. **08:15 V3 shadow overlay — PASS (contract/replay)**
   - Library overlay created separately from Canonical Master.
   - Production Master not overwritten.
   - First replay: ATTACK=0, PROBE=1, WATCH=6, PASS=1.
   - Shadow candidate for live follow-through: `011200 HMM`.
   - Production watchlist not modified.

5. **Latest-completed-session freshness bug — FIXED**
   - Old workflow incorrectly equated V3 tradeDate with calendar today.
   - V3-specific freshness validator now resolves the latest completed KRX session by independent reference consensus.
   - Semantic freshness regression tests PASS.
   - Run #39 `36652936702`: SUCCESS.
   - During the 2026-09-30 live session it correctly treated the run as a pre-close functional test and skipped canonical commit.

6. **Shadow plan / live-capture contracts — PASS**
   - `scripts/validate_v3_0815_shadow_plan.py`
   - `scripts/test_v3_0815_shadow_plan.py`
   - `scripts/v3_shadow_live_capture.py`
   - `scripts/test_v3_shadow_live_capture.py`
   - Lightweight CI Run #1 `36654222175`: SUCCESS.

## Runtime finding

The existing production intraday path is intentionally not current:
- `watchlist.json` tradeDate = 20260928.
- `watchlist-sync-status.json` tradeDate = 20260928.
- `live.json` tradeDate = 20260928, history through 09:40.
- `live-health.json` last validates 20260928.

This is consistent with the existing sustainability restart rule: the 08:15 / 09:35 / 09:40 ChatGPT stock automations remain OFF until real-session E2E is proven.

Do not treat those 20260928 files as current 20260930 evidence.

## New production-isolated live path

Workflow: `.github/workflows/v3-shadow-live-capture.yml`

Purpose:
- manually capture V3 shadow candidate(s) from 09:00 through 09:40 KST,
- read only the deployed public Worker `/live` and `/scan` endpoints,
- collect exactly 41 minute rows,
- upload short-retention diagnostic artifact only,
- never write Worker KV,
- never update production `watchlist.json`, `live.json`, `live-health.json`, or Library production artifacts.

The workflow fails closed if:
- started after the strict opening window,
- target tradeDate mismatches current KST date,
- candidate payload is missing/invalid,
- market is not open,
- a minute is captured too late,
- the final 09:00~09:40 chain is incomplete.

## Exact next step

On the next actual KRX trading session:
1. Build the V3 08:15 shadow plan from the latest completed-session V3 artifact.
2. Take only ATTACK/PROBE shadow survivors for live follow-through.
3. Before 09:00 KST, dispatch `V3 Shadow Live Capture` with that session's `trade_date` and survivor codes.
4. Require a 41-row 09:00~09:40 artifact PASS.
5. At 09:35/09:40, compare the actual path with the **prewritten** trigger / invalidation / no-chase conditions. Do not redesign the thesis after seeing the path.
6. Record PASS/FAIL and candidate-level follow-through.
7. Only after a reproducible real-session cycle should production V2->V3 cutover be considered.

## Non-negotiable boundary

Until the real-session shadow cycle passes:
- do not overwrite the Canonical V8.6 Master,
- do not switch production `watchlist.json` to V3,
- do not re-enable production 08:15/09:35/09:40 automations merely to manufacture a test,
- do not call stale production live data current,
- do not reintroduce score-based ranking.
