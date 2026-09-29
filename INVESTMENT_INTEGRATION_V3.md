# Investment Integration V3

Status: DESIGN CONTRACT / NOT PRODUCTION CUTOVER  
Date: 2026-09-29

## Objective

The system is optimized for investment decision quality and long-run expected value, not for faithfully reproducing chart-study terminology.

The chart engine is one evidence lane. A final trade plan is created only after assistant deep chart review is combined with company/revision/catalyst/context evidence and an explicit execution/invalidation plan.

## End-to-end flow

```
FULL MARKET
  -> V3 quantitative prefilter
  -> bounded deepReviewQueue
  -> assistant chart deep review
  -> external evidence lanes
  -> premarket plan
  -> live confirmation / cancellation
  -> position sizing and invalidation
```

The machine scanner never has final authority over a trade.

## 1. Chart-review output

Assistant chart review returns exactly one state:

- `ATTACK_CANDIDATE`: structure and location are good enough to move to full investment research.
- `PROBE_CANDIDATE`: asymmetry is attractive but one important chart confirmation is still missing.
- `WATCH`: interesting structure, wrong/unclear current location.
- `REJECT`: damaged, ambiguous, late/extended, poorly located, or machine hypothesis rejected.

Required evidence:
- dominant chart thesis
- current important price/zone
- observable confirmation event
- structural invalidation
- next meaningful resistance/target if visible
- chase/no-chase judgement
- strongest counterargument

A `REJECT` chart cannot be rescued into a current entry by news, narrative or fundamentals. It may remain on a separate future watch list.

## 2. External evidence lanes

External research is recorded as evidence states, not points.

### Company quality
- `SUPPORTIVE`
- `MIXED`
- `ADVERSE`
- `UNKNOWN`

Focus on business quality, balance-sheet constraints, dilution/governance issues and whether the business can plausibly support the chart thesis.

### Earnings / revisions
- `UP_REVISION`
- `STABLE`
- `DOWN_REVISION`
- `UNKNOWN`

Prefer company IR, DART/KRX and broker/FnGuide revision evidence. A one-off accounting effect must be separated from recurring improvement.

### Catalyst
- `ACTIVE`
- `UPCOMING`
- `NONE_IDENTIFIED`
- `UNKNOWN`

Record the catalyst, expected timing and whether the market may already have priced it.

### Industry / macro
- `TAILWIND`
- `NEUTRAL`
- `HEADWIND`
- `UNKNOWN`

Use only factors material to the company thesis.

### Global / US lead price discovery
- `CONFIRMING`
- `NEUTRAL`
- `CONTRADICTING`
- `NOT_MATERIAL`
- `UNKNOWN`

Do not invent a US proxy. If there is no economically meaningful leading market or underlying asset, use `NOT_MATERIAL`.

### Event risk
- `LOW`
- `MODERATE`
- `HIGH`
- `UNKNOWN`

Examples include imminent earnings, binary regulatory decisions, large lockups, major corporate actions or other events that can invalidate normal chart-based risk assumptions.

## 3. Evidence freshness

Every external evidence item must carry:
- source type
- source date
- observation date
- whether it is direct company/regulatory evidence or secondary research

Stale evidence does not silently remain positive. It becomes `UNKNOWN` when its relevance window has expired.

## 4. Investment-plan state

No aggregate score is allowed.

### `ATTACK_PLAN`
Requires:
- chart = `ATTACK_CANDIDATE`
- structural invalidation exists
- no unresolved material contradiction
- revisions/company/context do not materially invalidate the thesis
- event risk is understood and explicitly planned
- current price is not beyond the chart's no-chase boundary

### `PROBE_PLAN`
Used when:
- chart = `PROBE_CANDIDATE`, or
- chart = `ATTACK_CANDIDATE` but one non-fatal external uncertainty remains

A probe must define the exact evidence that permits expansion to full planned size.

### `WATCH`
Used when the thesis may be valid but:
- price is not at an actionable location,
- a confirmation event is missing,
- evidence is materially stale,
- external evidence conflicts without fully invalidating the thesis,
- event risk makes current entry unattractive.

### `PASS`
Used when:
- chart = `REJECT`,
- material business/revision evidence contradicts the thesis,
- structural invalidation has occurred,
- the only remaining argument is narrative rather than observable evidence.

## 5. Premarket vs live responsibilities

Premarket plan uses confirmed prior-session data and current external evidence to define:
- actionable zone
- trigger
- invalidation
- no-chase boundary
- initial size class
- add condition
- cancel condition

Live data does not redesign the thesis from scratch. It answers whether the prewritten conditions are being confirmed or violated.

Machine structural risk/reward is measured from the planned entry reference to structural invalidation and the next meaningful resistance. The current price's distance from that entry reference is carried separately so assistant review can reject a valid structure that has already become a chase.


A strong premarket thesis may expand quickly after the planned trigger confirms; the system must not remain indefinitely at probe size merely because it began as a probe.

## 6. Position sizing

Position size is downstream of thesis quality and invalidation distance.

The system must distinguish:
- `PROBE`: information-gathering exposure
- `CORE`: normal planned exposure after confirmation
- `ATTACK`: higher-conviction exposure only when chart, external evidence and live confirmation align

Size is never increased merely because price moved up. Expansion must be tied to a pre-defined confirmation event while structural invalidation remains valid.

## 7. Anti-anchoring contract

Each daily review starts from the current candidate universe.

Do not promote a candidate because it was:
- previously held,
- previously discussed,
- yesterday's top candidate,
- a familiar sector,
- a management recommendation.

Prior discussion may be consulted only after the current-day evidence has independently qualified the candidate.

## 8. Sustainability boundary

New information belongs in one of three places:

1. **Machine prefilter** — only if objectively measurable and useful for reducing the universe.
2. **Assistant deep review** — contextual chart judgements that should not be reduced to brittle thresholds.
3. **External evidence lane** — company/revision/catalyst/context information.

Do not add a fourth hidden scoring system.

A new feature is accepted only if it improves discovery, timing, risk control or maintainability enough to justify its complexity.
