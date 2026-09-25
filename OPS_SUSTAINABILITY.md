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
- **Explicit watchlist trade-date binding — PASS (source/test)**
  - Worker source commit: `688369894d180b4d1b150e787cc5add3a4d507f9`
  - regression-test commit: `cbaf4d0be0f4333361875311f512050c92d19d55`
  - CI run: `36122775314` / conclusion `success`
  - Worker KV now stores `{tradeDate,codes}`; scheduled capture fails closed before minute collection when the watchlist date is stale.
  - sync workflow trade-date commit: `1b234d6bcd29187b670a011d889b531ad205a97e`
  - runtime secure sync is now verified PASS; see `Secure watchlist sync runtime` below.
- **Secure watchlist sync source — DONE**
  - workflow: `.github/workflows/sync-watchlist.yml`
  - hardening commit: `d8cb5d7918de20ac68a8c078a75ef5f1466c6054`
  - self-test trigger commit: `a53be1d306a9b28d4589a07d18cdd0bec4bcd7dc`
- **Secure watchlist sync runtime — PASS**
  - secure migration run `36125633721` concluded `success`.
  - next-session staging sync run `36125788350` concluded `success`.
  - latest verified contract: `status=PASS`, `mode=POST_BEARER`, `cloudflareStatus=WATCHLIST_SAVED`, `reason=NONE`.
- **Deployed Worker hardening — PASS**
  - deployed runtime build `worker_v3_hardened_money_scan_v3` verified by public probe.
  - full deployment security verification run `36125721271` concluded `success`.
- **Canonical deployed-build fingerprint — PASS (source/test only)**
  - expected build: `worker_v3_hardened_money_scan_v3`
  - Worker build commit: `4bd6cedad8692a263864ddc8b3719999c171945a`
  - regression-test commit: `118a38779da6f91650c654c8573e1c59b72a6eab`
  - v2 fingerprint/test commit: `7ac059717131c543d18cc20f41760ba3c076bb8d`
  - baseline CI run: `36121815540` / conclusion `success`
  - v2 Worker regression run: `36122879058` / conclusion `success`
  - deployment verifier now checks the exact build fingerprint and required capabilities before accepting runtime PASS.
- **Deployment security verification — PASS (runtime)**
  - workflow: `.github/workflows/verify-cloudflare-deployment.yml`
  - runtime run `36125721271` concluded `success` after secrets/deployment were configured.
- **Live publisher source — PASS (source/test only)**
  - canonical publisher is now versioned inside `cloudflare/worker_v3_hardened.mjs`.
  - source commit: `ffec767d5243970adb2c58afd0f1df03dc072b3a`.
  - publisher regression-test commit: `0508244cce048ff557e47fb395913663a488cce8`.
  - CI run: `35984912894` / conclusion `success`.
  - publish gate requires a complete contiguous 09:00~09:35 or 09:00~09:40 KV minute chain before writing `live.json`; incomplete history records FAIL and does not publish.
  - deployed build and credential path are now verified; actual 09:35/09:40 `live.json` publication on a real KRX session remains NOT DONE.
- **Scanner durability / feature-contract execution — PASS**
  - feature-contract commit: `87b3e492974869c63c701223e951a399f8a1e937`
  - replay run: `35977284215` / conclusion `success`
  - baseline full-market scan run: `35977284250` / conclusion `success`
  - chart-discovery regression commits: `790b0f7c22749937115b427ff6179741867de5e1`, `da0f7467fe692e46b1f798ed95c1570bee3732fc`
  - post-fix replay run: `35983214293` / conclusion `success`
  - post-fix full-market scan run: `35983214306` / conclusion `success`
  - on the 2026-09-24 non-trading day, both full-market validations passed and the canonical commit step was correctly `skipped`.
- **Cross-sectional execution-level precision invariants — PASS**
  - validator source: `scripts/validate_scan_precision.py`
  - initial validator commit: `58a5ddb2dd53f99afcc6a07d0490b21816627737`
  - workflow integration: `f996142cd898e02d4cf4b3ae55cb237aebfc2ddb`
  - first run `36121950677` correctly exposed an invalid test invariant rather than a scanner defect.
  - corrected invariant commit: `cdb4e911612d152f1144bb92cc10ea038e9202f6`
  - final full-market run: `36122568757` / conclusion `success`; self-tests, full scan, execution-level invariant validation and output validation all passed.
- **Post-R/R full-market regression — PASS**
  - scanner invalidation/R-R commit: `834f13b92cbe0b5eb64dfe03d40ff281faded45e`
  - regression-test commit: `38c033e1dfcb5287ca4b53f004772ecfc2abb937`
  - replay run: `35987234904` / conclusion `success`
  - full-market scan run: `35987234840` / conclusion `success`
  - self-test, full KOSPI/KOSDAQ scan and output validation all passed; canonical commit was skipped because the run did not have a new current trading-day payload.
- **Current canonical scan migration — PASS**
  - migration run `36126406033` concluded `success` from the validated full-scan artifact of the latest completed session.
  - `longterm-scan.json` read-back SHA `846e2999f729c5a92deb49779f7e5070317a00f5`.
  - `schemaVersion=YBM_BRIEF_V2`, `status=PASS`, `tradeDate=20260923`, `chartCandidates=119`, `qualifiedPool=74`, `briefingCandidates=2`, `riskWarnings=86`.
- **Master publisher contract read-back — PASS**
  - Library Canonical Master: V8; latest read-back confirms the current v3 Worker/publisher contract.
  - read-back confirms canonical Worker source `cloudflare/worker_v3_hardened.mjs`, fail-closed publication at 09:35/09:40, Worker Secret `GITHUB_TOKEN`, publisher identity and runtime read-back requirement.
- **Money-aware intraday ranked scan — PASS (source/test)**
  - Worker commit: `b933e27a701aaee99a645d562df3878dbd37d8fe`.
  - regression-test commit: `54d7c2adfb27caf0d25e2736d4b68ea6e283178f`.
  - CI run: `35986527136` / conclusion `success`.
  - stores 09:30/09:35/09:40 ranked scans and publishes absolute turnover plus 5-minute turnover/volume deltas.
  - this is explicitly a ranked-scan discovery layer, not a claim of exhaustive full-market same-time statistics.
- **Live-health scan degradation boundary — PASS**
  - commits: `3b3c12baf1568803222f66e76ab1f717eb774ad4`, `7815e3f354f8d85af6a66f3fb4d66237cd755afd`.
  - CI run: `35986620061` / conclusion `success`.
  - missing/partial scan evidence is Noncritical warning-only and cannot masquerade as 'no change'.
- **Real-session E2E validator — PASS (validator/test)**
  - validator commit: `df460f9bbe6251de16b7388de879efde5ae48c1b`
  - test commit: `f2c182b673921b778da6dd27ecc81ceb91c9ba76`
  - CI workflow commit: `a14832dbcb0741ebf4ed2992e42c804807f1102e`
  - baseline CI run: `36122315157` / conclusion `success`
  - v2 E2E test run: `36122907705` / conclusion `success`
  - manual verification workflow: `.github/workflows/verify-real-session-e2e.yml` (commit `7073385a27acee365e73b3ce281b169bcc234db7`)
  - hardened Worker deployment is PASS; runtime E2E remains NOT DONE until a real KRX session produces current 09:35/09:40 evidence.
- **Real KRX trading-day E2E after hardening — NOT DONE**.

- **Deployment cutover runbook — DONE**
  - `DEPLOY_CUTOVER.md`
  - commit: `d85c812f219dee46259370f555e2d6e8b4b8a8b1`

## Cutover / remaining runtime checklist

1. **DONE** — deploy canonical Worker with `STOCK_KV` preserved.
2. **DONE** — configure Worker `WRITE_TOKEN`.
3. **DONE** — configure matching GitHub Actions `CLOUDFLARE_WRITE_TOKEN`.
4. **DONE** — reuse verified repository-scoped Worker `GITHUB_TOKEN` for `live.json` publication.
5. **PASS** — deployment/security verification run `36125721271`.
6. **PASS** — secure POST_BEARER watchlist sync; 2026-09-28 staging run `36125788350`.
7. **NOT DONE** — on a real KRX session, verify 09:35/09:40 `live.json` publisher identity, exact watchlist, contiguous history and matching publication evidence.
8. **NOT DONE** — complete full 08:15 -> sync -> 09:00~09:40 -> live-health -> 09:35 -> 09:40 -> Evidence/NEXT_SESSION E2E.

## Restart rule

Do not re-enable the 08:15 / 09:35 / 09:40 ChatGPT stock automations until the remaining `NOT DONE` / `UNKNOWN` sustainability items above are resolved and the real-session E2E passes.


## Runtime deployment probe

- **Public deployed Worker probe — PASS**
  - read-only probe workflow: `.github/workflows/probe-cloudflare-public.yml`.
  - post-deploy probe job `108039989785`: `build=worker_v3_hardened_money_scan_v3`.
  - post-staging probe job `108041584860`: `watchlistTradeDate=20260928`, `watchlistCount=9`.


- **Manual E2E watchlist staging — PASS / staged for 2026-09-28**
  - workflow: `.github/workflows/stage-e2e-watchlist.yml` remains available for manual staging.
  - actual 2026-09-28 staging was committed directly in `watchlist.json` with codes preserved; secure sync run `36125788350` concluded `success`.
  - the three ChatGPT stock automations remain OFF pending real-session E2E.


## Secure runtime cutover

- **Secure runtime cutover — PASS**
  - Cloudflare deployed build: `worker_v3_hardened_money_scan_v3`.
  - public runtime probe re-run job `108039989785`: build fingerprint PASS.
  - repository secret `CLOUDFLARE_WRITE_TOKEN` was added manually by the user; the secret value is not recorded in source/logs.
  - secure watchlist migration run `36125633721`: conclusion `success`.
  - `watchlist-sync-status.json`: `status=PASS`, `mode=POST_BEARER`, `cloudflareStatus=WATCHLIST_SAVED`, `reason=NONE`.
  - full deployment security verification run `36125721271`: conclusion `success`; exact build, public read, 405 mutating GET, 401 unauthenticated mutation/run-now/kv-test, authenticated POST and exact tradeDate/codes all passed.
- **Next-session infrastructure staging — PASS**
  - staged watchlist tradeDate: `20260928`; existing nine codes preserved.
  - staging commit: `0f6100f9dae246e166f66c97041a7bc754bd8885`.
  - secure sync run `36125788350`: conclusion `success`.
  - public probe re-run job `108041584860`: `build=worker_v3_hardened_money_scan_v3`, `watchlistTradeDate=20260928`, `watchlistCount=9`.
  - this is infrastructure-only staging; the three ChatGPT stock automations remain OFF pending real-session E2E.


- **Future-staged watchlist validation noise — FIXED**
  - future-date staging had caused an expected red `Validate Live Freshness` failure on the holiday/current date.
  - workflow fix commit: `4cdf8c25af002f72f96a9bffea8eebd584eec05e`.
  - verification run: `36125961071` / conclusion `success`; semantic freshness/health write/enforce steps were intentionally skipped and `FUTURE_WATCHLIST_STAGING_PASS` completed.
  - same-day and past-date live validation remain fail-closed.
