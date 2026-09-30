# Korean Stock Blind Portfolio Replay

Status: RESEARCH / PRODUCTION-ISOLATED

## Purpose

Test the actual swing-investing loop the live system is intended to support:

1. full-market discovery,
2. assistant deep chart review,
3. entry / initial sizing,
4. ongoing position management,
5. fresh full-market discovery while positions are open,
6. HOLD / ADD / REDUCE / EXIT / ROTATE capital decisions,
7. benchmark-aware evaluation.

This is not a replacement for the live-session E2E test. It is a historical blind laboratory for chart judgement, portfolio management and capital rotation.

## Blind integrity

- The episode calendar start is hidden until the final result.
- Candidate stock codes and names are replaced by stable episode-local asset IDs until final reveal.
- Current cards contain no future bars and no calendar dates.
- A decision must be committed before the next review window is generated.
- Locked decisions are never rewritten after seeing later data.
- The generator may internally access future data only to settle an already-locked interval; future data is never written into the current card.

## Historical universe

The replay attempts to reconstruct the KOSPI/KOSDAQ universe that existed at each hidden review date.

- Current KRX listings are included only when their listing date is on or before the hidden cutoff.
- KRX delisted listings are added when they were still listed at the hidden cutoff.
- SPACs are excluded to match the live V3 scanner.
- Current trading-value metadata is never used for a historical decision. Historical liquidity is estimated only from bars available through the cutoff.

This materially reduces survivorship bias. It is still a research reconstruction, not an exchange-certified security-master snapshot.

## Market engine

The test reuses the production-isolated Market Structure V3 machine engine without changing its methodology:

price + volume + time -> important price zones -> role state -> close acceptance/rejection -> setup hypothesis -> confirmation -> execution proposal.

The machine remains only a universe compressor. The assistant must independently deep-review the supplied chart traces according to `ASSISTANT_CHART_DEEP_REVIEW_PROTOCOL.md`.

## Portfolio rules

- Initial capital: KRW 10,000,000.
- Long-only Korean equities and cash.
- Maximum gross capital allocation: 100%.
- No margin, credit, futures or leverage.
- Review cadence and episode length are defined in `ACTIVE_EPISODE.json`.
- Existing positions remain visible even if they drop out of the new discovery queue.
- Fresh discovery continues at every review while positions are open.
- The assistant may HOLD, ADD, REDUCE, EXIT or ROTATE.
- A stated target is a planning reference, not a mandatory hold-until-target instruction.
- A better new opportunity may justify realizing an existing position before its original target.
- Adding to a loser is allowed only when the underlying structural thesis remains valid and the new price improves expected value; price decline alone is never a reason to add.

## Decision file contract

Each `Dxx.json` declares the desired portfolio after the current review.

Required top-level fields:
- `step`
- `thesis`
- `portfolio`

Each portfolio item requires:
- `assetId`
- `capitalPct`
- `action`: `ENTER`, `HOLD`, `ADD`, `REDUCE`, or `ROTATE_IN`
- `stop`: structural invalidation price; null only when the position is intentionally managed at the next review without a live structural stop
- `target`: next meaningful resistance/target area; may be null when no honest structural target is visible
- `reason`

Optional top-level `exits` can document `EXIT` / `ROTATE_OUT` reasoning for names removed from the portfolio.

The sum of `capitalPct` may not exceed 100.

## Execution model

- Portfolio changes execute at the hidden review-session close.
- Sells are processed before buys.
- A small configurable transaction-cost/slippage proxy is charged on turnover.
- Between reviews, declared structural stops remain live. A gap below the stop exits at the first available open; otherwise the stop price is used when the session low reaches it.
- A stopped position remains cash until the next review.
- Targets are not mechanically sold between reviews unless a later protocol version explicitly adds target orders. They guide assistant review and rotation decisions.

## What this test validates

Strongly relevant:
- discovery selectivity,
- chart interpretation,
- entry location,
- structural invalidation,
- sizing,
- holding winners,
- adding after confirmation,
- avoiding blind averaging down,
- recognizing deterioration,
- capital rotation when a superior setup appears,
- excessive turnover / premature exits.

Not fully validated here:
- point-in-time earnings revisions,
- historical broker consensus,
- historical news/catalyst quality,
- live intraday confirmation,
- actual bid/ask market impact.

Those belong to later point-in-time evidence lanes and the live-session E2E test.

## Final scoring

At episode completion reveal and record:
- start date and asset mapping,
- final capital and total return,
- max drawdown,
- turnover and transaction costs,
- average invested capital / cash utilization,
- number of entries, exits and rotations,
- KOSPI and KOSDAQ buy-and-hold returns over the same hidden interval,
- position-level contribution where available.

A profitable result is not automatically a pass. The portfolio must be judged against the market regime, opportunity set, drawdown and avoidable under-participation or overtrading.
