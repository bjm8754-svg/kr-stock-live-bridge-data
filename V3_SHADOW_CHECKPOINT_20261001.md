# V3 Shadow Checkpoint — 2026-10-01

Status: CATCH-UP REPLAY PASS / REAL-SESSION E2E STILL PENDING
Production cutover: NOT DONE
Production V8.6 / watchlist.json / live.json / live-health.json: UNCHANGED BY CATCH-UP PATH

## What was corrected today

- Legacy production ChatGPT 08:15 / 09:35 / 09:40 automations were mistakenly re-enabled, then disabled again.
- New V3 SHADOW ChatGPT automations are enabled for weekdays:
  - 08:15 KST: build V3 shadow plan + `v3-0815-shadow-watchlist.json`
  - 09:37 KST: evaluate the 09:35 shadow evidence
  - 09:42 KST: evaluate the 09:40 shadow evidence
- `.github/workflows/v3-shadow-session-capture.yml` is scheduled at 08:47 KST weekdays and starts before 09:00.
- It reads only `v3-0815-shadow-watchlist.json`, requires `SHADOW_ONLY` and `productionWriteAllowed=false`, and creates separate 09:35 (36-row) and 09:40 (41-row) artifacts.
- Contract CI for the scheduled V3 shadow session workflow passed: run `36796989193`.
- The Worker `/live?codes=...` path directly fetches requested codes and is independent of the saved production watchlist, so a stale production watchlist does not block V3 shadow read-only capture.

## Why 2026-10-01 was not a real-time E2E

The 08:15 V3 shadow plan was not run in real time. By the time the issue was corrected, 09:35 and 09:40 had also passed. Therefore no real-time PASS is claimed for 2026-10-01.

Production Worker history for 20261001 had 0 rows because the production watchlist was still dated 20260928 and the Worker scheduled publisher correctly failed closed on the trade-date mismatch.

## 2026-10-01 catch-up replay procedure

1. Resolved the final 2026-09-30 V3 scheduled scan:
   - run `36686304188` — SUCCESS
   - artifact `11084930018`
   - review packet count = 36
2. Reconstructed the 08:15 decision using only information available by 08:15 KST.
3. Froze the decision before reading any 2026-10-01 09:00+ intraday prices:
   - plan commit `18a360f8a4a255911cd861d09cd18844f46f7d5e`
   - watchlist commit `35ae976e4abeb347f945b73c7ba8fa841c73bec0`
4. Final live-follow candidates were PROBE only:
   - `010950` S-Oil
   - `000250` 삼천당제약
   - `039030` 이오테크닉스
5. Worker history could not be reused because 10/1 history was empty.
6. Naver historical intraday endpoint returned HTTP 410 and was rejected.
7. Yahoo 1-minute fallback recovered exact 09:00~09:40 data with no interpolation:
   - run `36799631355` — SUCCESS
   - evidence commit `75b7670f1c4eb713e72aedb2e98c288e6ee89609`
   - all 3 candidates = 41 exact one-minute rows
8. Replayed the prewritten conditions without redesigning them after seeing prices.

## Catch-up result

### 09:35
- S-Oil `010950`: INVALIDATED
  - frozen invalidation 157,300
  - first close below it at 09:11 = 156,900
  - 09:35 close = 156,500
  - 164,800 trigger never reached
- 삼천당제약 `000250`: CONFIRMED
  - held above 170,275
  - first break above 174,800 at 09:32; close 175,100
  - 09:35 close = 176,000
- 이오테크닉스 `039030`: CONFIRMED
  - held above 505,500
  - 09:10 close = 526,000; 09:11 close = 529,000
  - 09:35 close = 536,000

09:35 evaluation commit: `0adeb277d9c4120016c855aee85079c9955b26c0`

### 09:40
- S-Oil: INVALIDATED maintained; 09:40 close = 155,300
- 삼천당제약: CONFIRMED maintained; 09:40 close = 180,700
- 이오테크닉스: CONFIRMED maintained; 09:40 close = 540,000

09:40 evaluation commit: `e3335ed8ffb85432c5dd6400a766046307e4e4de`

Result: `CATCHUP_REPLAY_PASS`
Real-time result: `NOT_TESTED`

## Production isolation proof

Compare `35ae976e4abeb347f945b73c7ba8fa841c73bec0` -> `e3335ed8ffb85432c5dd6400a766046307e4e4de` changed only catch-up workflow/script/evidence/evaluation files. Production `watchlist.json`, `live.json`, and `live-health.json` were not changed.

## Next real-session requirement — 2026-10-02

No new construction should be needed in the morning. The purpose is live verification only:

1. 08:15 V3 SHADOW automation must create and read-back the current-day plan/watchlist.
2. 08:47 V3 Shadow Session Capture must resolve that handoff and already be running before 09:00.
3. 09:00~09:35 artifact must contain exactly 36 rows.
4. 09:37 automation must evaluate only the prewritten 08:15 conditions.
5. 09:00~09:40 artifact must contain exactly 41 rows.
6. 09:42 automation must finalize the shadow cycle.
7. Production files must remain unchanged.
8. Only if all above pass may the day be labeled REAL_SESSION_E2E_PASS.

Do not call the 2026-10-01 catch-up replay a real-time E2E PASS.
