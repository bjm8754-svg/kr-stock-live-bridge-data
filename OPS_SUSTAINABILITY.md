# Sustainability / Operations Status

Evidence-only operating record for `bjm8754-svg/kr-stock-live-bridge-data`.

## Current state

- **Worker source hardening — PASS**
  - canonical source: `cloudflare/worker_v3_hardened.mjs`
  - source commit: `73ba57dffb63a7d55d82176e3006d97cc4571a47`
  - regression test commit: `ff650a8a4ac971f8588f4e83536eea4059977030`
  - CI commit: `a9f4b8644e823c2af756da86fa6bd781b07b8507`
  - CI run: `35974901032` / conclusion `success`
- **Live freshness boundary regression — PASS**
  - test commit: `3e5ad1675c372a3137340beb4ef901326f5363c9`
  - CI commit: `6f1a02d0fd43a9fc051194ac73b1a72e06f5445b`
  - CI run: `35975550058` / conclusion `success`
- **Secure watchlist sync source — DONE**
  - workflow: `.github/workflows/sync-watchlist.yml`
  - hardening commit: `d8cb5d7918de20ac68a8c078a75ef5f1466c6054`
  - self-test trigger commit: `a53be1d306a9b28d4589a07d18cdd0bec4bcd7dc`
- **Secure watchlist sync runtime — PARTIAL**
  - latest `watchlist-sync-status.json` reports `status=FAIL`
  - reason: `MISSING_CLOUDFLARE_WRITE_TOKEN`
  - this is expected fail-closed behavior until the secret exists.
- **Deployed Worker hardening — NOT DONE**
  - GitHub source/test success is not deployment evidence.
  - deployed Worker must be replaced with the canonical source and verified.
- **Deployment security verification workflow — DONE (source only)**
  - workflow: `.github/workflows/verify-cloudflare-deployment.yml`
  - commit: `354f7c2a676e8832ffe4258dbd1912f4313872af`
  - execution result remains `NOT DONE` until secrets/deployment are configured.
- **Live publisher source — PASS (source/test only)**
  - canonical publisher is now versioned inside `cloudflare/worker_v3_hardened.mjs`.
  - source commit: `ffec767d5243970adb2c58afd0f1df03dc072b3a`.
  - publisher regression-test commit: `0508244cce048ff557e47fb395913663a488cce8`.
  - CI run: `35984912894` / conclusion `success`.
  - publish gate requires a complete contiguous 09:00~09:35 or 09:00~09:40 KV minute chain before writing `live.json`; incomplete history records FAIL and does not publish.
  - **runtime remains NOT DONE** until the canonical Worker is deployed with `GITHUB_PUBLISH_TOKEN` and an actual GitHub `live.json` commit is verified.
- **Scanner durability / feature-contract execution — PASS**
  - feature-contract commit: `87b3e492974869c63c701223e951a399f8a1e937`
  - replay run: `35977284215` / conclusion `success`
  - baseline full-market scan run: `35977284250` / conclusion `success`
  - chart-discovery regression commits: `790b0f7c22749937115b427ff6179741867de5e1`, `da0f7467fe692e46b1f798ed95c1570bee3732fc`
  - post-fix replay run: `35983214293` / conclusion `success`
  - post-fix full-market scan run: `35983214306` / conclusion `success`
  - on the 2026-09-24 non-trading day, both full-market validations passed and the canonical commit step was correctly `skipped`.
- **Current canonical scan migration — PARTIAL**
  - `longterm-scan.json` is compact instead of the old ~6.5 MB payload.
  - current 2026-09-23 source predates the chart-grade layer, so `compatibility.chartCandidatesAvailable=false`; empty `chartCandidates` must not be interpreted as no candidates.
- **Real KRX trading-day E2E after hardening — NOT DONE**.

## Manual deployment checklist

1. Deploy `cloudflare/worker_v3_hardened.mjs` to Worker `kr-stock-live-bridge` while preserving the `STOCK_KV` binding.
2. Set a strong Cloudflare Worker secret named `WRITE_TOKEN`.
3. Set GitHub Actions secret `CLOUDFLARE_WRITE_TOKEN` to the same value.
4. Set Cloudflare Worker secret `GITHUB_PUBLISH_TOKEN` to a repository-scoped token that can update `live.json` only as narrowly as practical.
5. Run `Verify Cloudflare Worker Deployment` manually. It must confirm:
   - public read-only `/watchlist` returns the current codes;
   - unauthenticated mutating GET is `405`;
   - unauthenticated mutating POST is `401`;
   - authenticated POST returns `WATCHLIST_SAVED` with exact codes.
6. Re-run `Sync Cloudflare Watchlist`; require current-date `watchlist-sync-status.json` with `status=PASS`, `mode=POST_BEARER`, `reason=NONE`.
7. At 09:35/09:40 verify the deployed Worker writes `live.json` with `publisher.type=CLOUDFLARE_WORKER_GITHUB_CONTENTS_API`, exact watchlist, contiguous history and a matching `last_publish_status=PASS`.
8. On the next real KRX session, verify 08:15 -> watchlist sync -> 09:00~09:40 minute history -> live-health -> 09:35 -> 09:40 -> Evidence/NEXT_SESSION.

## Restart rule

Do not re-enable the 08:15 / 09:35 / 09:40 ChatGPT stock automations until the remaining `NOT DONE` / `UNKNOWN` sustainability items above are resolved and the real-session E2E passes.
