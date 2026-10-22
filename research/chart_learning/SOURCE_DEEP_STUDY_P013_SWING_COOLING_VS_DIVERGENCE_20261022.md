# SRC-DEEP-013 — Distinguishing daily RSI normalization, true divergence, and weekly swing structure

**Research date:** 2026-10-22 KST · **Stage:** SOURCE-FIRST / research only · **No orders, scanner, S02, market outcome unmasking or production changes.**

## Original evidence examined

**Native Telegram images opened directly in this research pass**
- `image(20260929-144353).png`: visible message by `신 차트의` includes a BTC perpetual TradingView **daily** chart after a rapid upward expansion (upper figure), followed by a **1-hour** chart consolidating near elevated price and a separate lower RSI pane. Chat explicitly describes *daily surge, then sideways price and 1h RSI cooling*. The lower chart has short-term oscillation; the two figures are not synchronized bar-by-bar with exported 1D/1h OHLC or oscillator values.
- `image(20260929-144405).png`: speaker describes **daily RSI above ~80, sideways price while RSI cools toward ~50**, then a *possible* rebound. The chat explicitly calls the attached daily chart a **historical analogy** (`과거차트 빗대어서 설명드립니다`). It displays past completed paths. This teaches a possible mechanism, **not** a sealed prior prediction or a proven RSI50 limit order.

**Source comparators, previously inspected natively in v65**: LG CNS (064400) app daily/weekly `1000052596.jpg`/`1000052598.jpg` with an unverified lower oscillator, and BTC/KRW daily/weekly `1787696307713.jpeg`/`1000056913.jpg` with explicit **Stochastic RSI**, not plain RSI. Their screenshot labels cannot be assumed plain RSI(14). These are **two archived market episodes**, not successful matched RSI divergence instances. Library search for real completed plain-RSI multiweek examples mostly surfaced the **educational RSI poster corpus**; there was no additional independently verified plain-RSI/CVD completed daily-weekly pair found in the targeted search.

## Key original-derived counterexample: cooling is not a verified high-to-high divergence

| Claim type | Price requirement at SAME qualified timeframe | Oscillator requirement | What the reviewed source actually proves |
|---|---|---|---|
| **Momentum cooling** | Price can move sideways or up slowly after prior strong rise | RSI may fall from upper range toward middle | Telegram speaker describes + historically illustrates this. **Can** be consistent with a still-live uptrend; no future guarantee. |
| **Regular bearish divergence** | Two **confirmed completed** price swing highs, with second higher than first | Plain RSI at **corresponding price-swing times** has second lower | NOT proven by price+RSI charts here because the actual paired pivot samples, smoothing and cutoff are not sourced. |
| **Hidden bearish divergence** | Two completed price swing highs, second **lower** than first | RSI at matched price highs second **higher** | Taxonomic definition only; not identified in this archived speaker example. |
| **Weekly-price supply vs hourly momentum** | Weekly prior supply / completed close and distinct hourly price bars | Hourly RSI can cool independently of weekly price | Multi-timescale states may disagree without logical inconsistency. Weekly source `145216` was a **price-only chart**, not weekly RSI divergence proof. |

## Swing-specific decision logic to STUDY, not a validated trading algorithm

1. **Weekly/monthly gate:** price location versus mature support/supply, major highs/lows, participation and risk regime; a weekly high or older consolidation is an actual price-hurdle candidate. A 1h bullish/bearish RSI pattern cannot alone erase it.
2. **Daily thesis:** completed daily base, reclaim or failed acceptance, the actual entry zone and structural invalidation established before later price reaction. Compare whether daily price still respects that thesis while momentum cools.
3. **Intraday 4h/1h disambiguation:** at a *previously identified* daily level, ask whether 1h weakens via lower highs/lower lows and actual broken support, or merely RSI unwinding in a range. These are not equivalent reasons to cancel a planned swing entry.
4. **Matched-pivot rule:** only claim regular/hidden divergence with `instrument, venue, timeframe, exact indicator name & settings, bar_1_end, bar_2_end, RSI_at_price_pivot_1, RSI_at_price_pivot_2, price pivot eligibility, first_knowable_time`. A pivot often becomes known **after** its local extreme, and a backdated label would be future leakage.
5. **No-fill and false confirmation:** A planned support limit can go unfilled during a no-retest continuation, as curated teaching #067 shows; one shallower RSI tick cannot retrospectively justify a better earlier fill. Even a completed daily divergence can remain on a directional market for many bars.
6. **Different risk clocks:** a qualified weekly structural violation, an emergency capital cap, and 1h RSI cooling are **three distinct conditions**. Review every few sessions does not impose a fixed 3-day holding deadline on a multiweek swing.

### Four conditional competing interpretations worth preserving

- A: weekly price trend still above accepted support; daily strong impulse followed by range; 1h RSI falls, price does **not** breach daily support ⇒ momentum normalization **candidate**, not proven bearish divergence or forced liquidation.
- B: weekly supply overhead; daily price makes confirmed higher high but matched daily RSI lower high, followed by a qualified support breakdown ⇒ bearish warning gains context; still not guaranteed execution or return.
- C: weekly declining lower highs; 1h shows an apparent bullish divergence during a weak rebound ⇒ local bounce can coexist with continued weekly downtrend; **not** a multiweek buy by itself.
- D: price makes no second qualified price pivot, but RSI declines ⇒ `COOLING_ONLY`; do **not** silently label regular divergence.

**These scenarios are logical research hypotheses, not four actual chart examples or empirical win-rate findings.**

## Interpretation and evidence status

The added understanding is a tighter **classification rule** between three observable concepts: oscillation normalization, genuine matched-pivot RSI divergence, and higher-timeframe price invalidation. The source gives no authentic multiweek paired plain-RSI series or CVD aggressor/reset data, so do **not** claim verified real divergence, absorption, parameter edge, cross-symbol portability, expert equivalence or model mastery.

Original 91 curated figures all deep-reviewed previously; 69 Library root images remain previously marked inaccessible (no new recount in this batch); authentic video chart frames not reviewed. **Source-study gate remains OPEN; blind market trials, orders and program development remain paused.**
