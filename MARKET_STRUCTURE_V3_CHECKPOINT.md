# Market Structure V3 Checkpoint

Saved: 2026-09-29 11:31 KST
Status: PAUSED FOR RESUME

## Last fully validated shadow run
- Workflow: Market Structure V3 Shadow
- Run: 36514173931
- Result: SUCCESS
- Processed universe: 2,591
- Current-trade-date rows: 2,550
- Errors: 0
- Candidates: 120
- Candidate ratio: 4.71%
- Executable: 19
- Watch trigger: 4
- Radar: 97
- Structure warnings: 560
- Generic regression suite: PASS
- Output invariant validator: PASS

## Issue discovered after first full-market shadow
The warning layer was too noisy because weak swing-high/swing-low helper levels could emit FAILED_BREAKOUT / UPPER_REJECTION like true core structure.

## Latest code change saved
- Commit: 4d980428b3f6120a98396f071d216d15bae5d208
- Change: split structural levels into CORE vs SUPPORTING importance; add price-volume-time density levels; only CORE levels may emit strong structure-failure warnings.

## Important distinction
The first shadow PASS predates commit 4d980428..., so this latest refinement still requires a fresh shadow/full-market validation before any cutover.

## Resume order
1. Run/inspect fresh V3 shadow on latest HEAD.
2. Compare structure-warning count and composition versus prior 560-warning baseline.
3. Verify candidate count did not explode or collapse unnaturally.
4. Inspect EXECUTABLE/WATCH_TRIGGER examples for role-state correctness.
5. Check duplicate setup-family overlap and structural R/R integrity.
6. Keep V2 untouched as rollback/control until V3 proves stable over multiple sessions.

## Architecture lock
- V3 core = price + volume + time -> important levels -> role state -> close acceptance/rejection -> setup family -> confirmation -> execution.
- No stock-specific rules.
- No aggregate action score.
- YBM is no longer the governing architecture.
- RSI remains confirmation/warning only.
- Existing collection/automation infrastructure is reused.
