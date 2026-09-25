# Deployment Cutover — Hardened Live Bridge

This is the only manual cutover remaining before real-session E2E. Do not re-enable the ChatGPT 08:15 / 09:35 / 09:40 stock automations until every evidence gate below passes.

## Canonical deployable source

- Worker source: `cloudflare/worker_v3_hardened.mjs`
- expected build fingerprint: `worker_v3_hardened_money_scan_v3`
- Worker name / public host: `kr-stock-live-bridge` / `kr-stock-live-bridge.bjm8754.workers.dev`
- preserve existing KV binding: `STOCK_KV`
- preserve existing weekday 09:00~09:40 KST minute schedule

## Secrets

Two unrelated credentials are required.

1. `WRITE_TOKEN`
   - Cloudflare Worker secret.
   - GitHub Actions secret `CLOUDFLARE_WRITE_TOKEN` must contain the exact same value.
   - Purpose: protect `/watchlist` mutation, `/run-now`, and `/kv-test`.

2. `GITHUB_TOKEN`
   - Cloudflare Worker secret only.
   - Repository-scoped GitHub credential with the narrowest practical permission needed to read/update `live.json` in `bjm8754-svg/kr-stock-live-bridge-data`.
   - Purpose: publish validated 09:35/09:40 `live.json`.
   - Do not reuse `WRITE_TOKEN`.

Never place either token in source code, query strings, Library files, logs, or chat artifacts.

## Atomic cutover order

1. Create/set Worker `WRITE_TOKEN`.
2. Create/set Worker `GITHUB_TOKEN`.
3. Set repository Actions secret `CLOUDFLARE_WRITE_TOKEN` to the same value as Worker `WRITE_TOKEN`.
4. Deploy the exact canonical Worker source while preserving `STOCK_KV` and the schedule.
5. Run GitHub workflow `Verify Cloudflare Worker Deployment`.
6. Require workflow PASS and exact deployed build fingerprint `worker_v3_hardened_money_scan_v3`.
7. Run `Sync Cloudflare Watchlist` and require `watchlist-sync-status.json`:
   - `status=PASS`
   - `mode=POST_BEARER`
   - `reason=NONE`
   - exact current watchlist codes.
8. Keep ChatGPT stock automations OFF until a real KRX session passes the E2E checklist below.

## Deployment verification contract

`Verify Cloudflare Worker Deployment` must prove:

- public read-only `/watchlist` works;
- root `/` returns the exact build fingerprint and required capabilities;
- mutating GET `/watchlist?codes=...` => 405;
- unauthenticated mutating POST => 401;
- unauthenticated `/run-now` => 401;
- unauthenticated `/kv-test` => 401;
- authenticated watchlist POST => `WATCHLIST_SAVED` with exact codes.

Source/workflow presence is not runtime evidence. Only a completed successful workflow run after deployment counts as PASS.

## Real-session E2E

On the first actual KRX trading day after cutover:

- 08:15 current-day watchlist exists and secure sync is PASS.
- 09:00~09:35 minute keys are contiguous and semantically live.
- 09:30 and 09:35 ranked market scans exist.
- 09:35 `live.json` has:
  - current `tradeDate`
  - exact watchlist
  - history 09:00~09:35, count 36
  - `publisher.type=CLOUDFLARE_WORKER_GITHUB_CONTENTS_API`
  - `publisher.version=worker_v3_hardened_money_scan_v3`
  - money-aware `scan.turnoverTop / volumeTop / risingLiquid`
  - `scanDelta` based on 09:30→09:35
- `live-health.json` is PASS for Critical freshness. Market-scan degradation may only be a declared Noncritical warning.
- 09:35 ChatGPT snapshot uses only evidence available at that cutoff.
- 09:40 `live.json` has contiguous history through 09:40, count 41 and 09:35→09:40 `scanDelta`.
- 09:40 final completes Evidence Ledger and NEXT_SESSION write/read-back.

Only after all of the above is PASS may the three ChatGPT stock automations be re-enabled.

## Rollback

If deployment verification fails:

1. Keep the ChatGPT stock automations OFF.
2. Do not weaken authentication or freshness gates to make tests pass.
3. Restore the prior deployed Worker only if read-only continuity is needed; do not restore unauthenticated mutation as an accepted final state.
4. Record the failing endpoint/status in `OPS_SUSTAINABILITY.md`.
5. Fix source/tests first, then redeploy and re-run verification.
