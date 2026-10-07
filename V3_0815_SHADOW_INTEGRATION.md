# V3 08:15 Shadow Integration

Status: SHADOW ONLY / PRODUCTION V8.6 UNCHANGED
Date: 2026-09-30

## Purpose

Validate the full V3 investment path before any production cutover:

`latest completed KRX session -> V3 full-market scan -> bounded review shards -> EOD assistant deep chart review staging -> 08:15 overnight-delta integration -> atomic shadow bundle -> live confirmation/cancellation`

This overlay replaces only the V2/YBM discovery and chart-judgement portion during shadow evaluation. It does **not** change the production 08:15 Master, `watchlist.json`, Worker watchlist, 09:35/09:40 production path, or V2 rollback baseline.

## 1. Freshness gate

The authority is the **latest completed KRX session**, not calendar today.

A V3 source is usable only when all are true:
- latest successful `Market Structure V3 Shadow` run is resolved from GitHub,
- generic V3 regression passed,
- canonical invariant validation passed,
- review-packet validation passed,
- full-market scan status is `PASS`,
- `tradeDate` equals the latest completed KRX session by independent reference-session consensus,
- methodology starts with `MARKET_STRUCTURE_V3_`,
- review artifact is available and unexpired.

If any critical condition fails, the V3 scanner lane is `FAIL_CLOSED`. Do not silently fall back to an older V3 candidate set as current evidence.

## 2. Scanner boundary

Machine V3 has only three jobs:
1. compress the full market,
2. package observable price/volume/time evidence,
3. propose hypotheses and mechanically traceable structural references.

Machine `EXECUTABLE`, setup family, or setup state is **not** the final chart decision.

No aggregate quality/action score is allowed.

## 2.5. EOD assistant deep-review staging

The 36-candidate independent chart review is **not** a same-morning 08:15 workload.

After the completed-session V3 scan is committed:
- one scheduled assistant task processes the review queue in three fixed batches of at most 12 candidates,
- each run reviews only the first stale/missing batch,
- successful batches are stored as `v3-eod-deep-review-batch-1.json` through `-3.json`,
- GitHub Actions deterministically validates and merges current batches into `v3-eod-deep-review.json`,
- evening and early-morning retries are idempotent and never reuse an older source session by changing dates.

The merged EOD review is valid only when its source trade date, V3 workflow run id, review-index timestamp, methodology, candidate codes and review order exactly match the current Market Structure V3 handoff/index.

This stage contains chart judgement only. Overnight US price discovery, new disclosures/news, macro/event risk and other information that can change after the Korean close remain deferred to 08:15.

## 3. Deep-review input

Use the latest validated `market-structure-v3-review-index.json` and its size-bounded shards as machine evidence. The assistant EOD staging result is `v3-eod-deep-review.json`.

Hard bounds:
- maximum review candidates: 36,
- family diversity cap remains enforced by the scanner,
- chart evidence includes daily, weekly and monthly traces,
- RSI is read last and remains confirmation/warning only.

For each reviewed candidate, ignore the machine pattern name first and reconstruct:
1. price path + participation + time,
2. important-price hierarchy,
3. current role of those prices,
4. close acceptance/rejection,
5. higher-timeframe context,
6. current location / chase risk,
7. structural invalidation,
8. next meaningful resistance if visible.

Assistant chart state must be exactly one of:
- `ATTACK_CANDIDATE`
- `PROBE_CANDIDATE`
- `WATCH`
- `REJECT`

Every non-REJECT result requires:
- dominant chart thesis,
- important current zone,
- observable confirmation event,
- structural invalidation,
- next meaningful resistance if visible,
- chase/no-chase judgement,
- strongest counterargument.

A machine `EXECUTABLE` may be downgraded or rejected. A machine `RADAR/WATCH_TRIGGER` may be promoted only when the actual chart evidence supports it; the machine label itself is never promotion evidence.

## 4. 08:15 candidate competition

08:15 must first validate and consume the completed `v3-eod-deep-review.json`; it must **not** repeat the full 36-candidate chart review. The EOD chart judgement is frozen before overnight information is integrated.

At 08:15, process only information that can have changed since the Korean close, then compete these sources on equal footing:
- V3 `ATTACK_CANDIDATE` / `PROBE_CANDIDATE` survivors,
- valid NEXT-SESSION seeds,
- economically meaningful US Lead price-discovery challengers,
- material overnight catalyst challengers,
- current holdings requiring an action change.

Do not preserve a candidate merely because it was previously discussed, held, or selected.

## 5. External evidence lanes

Apply `INVESTMENT_INTEGRATION_V3.md` after chart review:
- company quality,
- earnings/revisions,
- catalyst,
- industry/macro,
- global/US lead price discovery,
- event risk.

Each evidence item must retain source date / observation date / source type. Missing evidence remains `UNKNOWN`; do not fill gaps with narrative.

A chart `REJECT` cannot be rescued into a current entry by fundamentals or news.

## 6. Execution plan

Final shadow plan state:
- `ATTACK_PLAN`
- `PROBE_PLAN`
- `WATCH`
- `PASS`

For ATTACK/PROBE, require:
- actionable zone from observed structure,
- trigger,
- structural invalidation,
- no-chase boundary or explicit no-chase condition,
- next meaningful resistance if real,
- structural R/R only when entry + invalidation + target are all observed,
- strongest counterargument,
- external-evidence contradictions explicitly resolved or retained as uncertainty.

Keep current structural R/R and planned structural R/R separate. Current distance from the planned entry is a chase diagnostic, not a reason to move invalidation farther away.

## 6.5. Atomic 08:15 authority and continuity boundary

The operational authority for live Shadow capture is one file: `v3-0815-shadow-bundle.json`.

A GitHub Actions continuity fallback may stage a current-day `MACHINE_CONTINUITY_FALLBACK` bundle before 08:15 so live evidence collection is not lost if the assistant connector write fails. This fallback is degraded diagnostic continuity only and **never** counts as a valid V3 strategy cycle or cutover evidence.

A successful 08:15 assistant run atomically replaces the bundle once with:
- `planOrigin=ASSISTANT_DEEP_REVIEW`,
- `degradedMode=false`,
- `assistantDeepReviewCompleted=true`,
- final ATTACK/PROBE live plans after overnight delta integration.

The live-capture workflow freezes the resolved bundle into the 09:35/09:40 artifacts. Later repository changes cannot redesign the pre-open trigger, invalidation, no-chase boundary, or candidate set.

## 7. Shadow write boundary

During this phase, do **not** write or replace:
- production `/국내주식_0815_ATTACK_PLAN.txt`,
- production `/국내주식_0930_PREFLIGHT_HANDOFF.txt`,
- production `watchlist.json`,
- Cloudflare Worker watchlist,
- production 09:35/09:40 state.

Allowed shadow outputs use explicit V3-shadow names only, for example:
- `국내주식_0815_V3_SHADOW_PLAN.txt`
- `국내주식_0815_V3_SHADOW_EVIDENCE.txt`
- `v3-0815-shadow-watchlist.json` (diagnostic only; never synced to Worker)

## 8. Production-master reuse

Keep these existing V8.6 concepts because they are generic, not YBM-specific:
- KRX session hard gate,
- live semantic freshness gate,
- US Lead price discovery,
- hard filters,
- company quality vs entry readiness separation,
- observed-structure entry/invalidation/R-R rules,
- NO-CHASE,
- Big Macro / event risk,
- 09:35/09:40 live follow-through logic,
- PROBE -> ADD/ATTACK confirmation discipline,
- anti-anchoring.

The shadow overlay replaces the V2/YBM discovery contract, actionScore ranking, YBM traceability requirement, and V2 candidate labels.

## 9. Shadow validation checklist

A shadow cycle passes only if:
- V3 latest-completed-session freshness is PASS,
- review index/shards exist and validate,
- merged EOD assistant deep review exists for the latest completed KRX session and exactly matches the current review index,
- deep review materially exercises independent judgement rather than copying machine readiness,
- the 08:15 live source bundle has `planOrigin=ASSISTANT_DEEP_REVIEW` and `degradedMode=false`,
- no aggregate score is reintroduced,
- ATTACK/PROBE plans have structural invalidation and no-chase logic,
- external evidence is explicitly integrated,
- production files/watchlist remain untouched,
- 09:35/09:40 shadow follow-through can compare live path against the prewritten V3 shadow trigger without redesigning the thesis after the fact.

V2 may be compared afterward as an audit/control only. V2 never votes on whether a V3 candidate survives.

## 10. Cutover condition

Do not cut over merely because one V3 scanner run is green.

First complete a real-session shadow cycle through EOD deep-review staging -> 08:15 overnight-delta integration -> 09:35 -> 09:40 and audit:
- missed high-quality structures,
- false positives,
- bad support/resistance roles,
- chase handling,
- invalidation integrity,
- external-evidence contradictions,
- operational freshness / artifact availability.

Only after the shadow path is operationally reproducible should the production Master be migrated. YBM/V2 remains rollback control until that explicit decision.
