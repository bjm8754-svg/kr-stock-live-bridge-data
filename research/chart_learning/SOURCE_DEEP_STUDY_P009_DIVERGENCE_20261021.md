# SRC-DEEP-009 — Divergence source study: RSI, price progress and CVD evidence boundaries

**Date:** 2026-10-21. **Source-first research, not independent market testing or a trading rule.** No S02, scanner, orders or production changes.

## Direct source reinspection
- Original curated `002_1000059605.jpg`: synthetic lower price lows accompanied by shallower declines and higher RSI troughs. Illustrates *decelerating downside*, not confirmed price reversal.
- `007_1000059613.jpg`: specifically links two qualified **price lows L2<L1** to **RSI lows R2>R1**. It says the price can continue downward. Later support/reaction and price progress remain unknown.
- `010_1000059619.jpg`: compares price up / RSI down and price down / RSI up; says 70/30 are not absolute execution buttons. Graphic is education, not a timestamped traded case.
- Actual Telegram `image(20260929-144527).png` (displayed sender `신 차트의`, user alias `차트의신` unverified): BTCUSDT.P *15m* TradingView embedded in chat. Cyan ellipse marks an **earlier** high RSI region around 70; *current plotted RSI readout* is around **44.56** at screenshot right. An alert text about RSI crossing **70** refers to a previous event, not simultaneously measured present RSI. There is a declining price move in the same frame. **Cannot certify bearish divergence:** a qualified pair of two price swing highs and their timestamp-aligned RSI highs is not established.

## Precise four-case RSI divergence taxonomy (definitions, not user-source performance findings)
| Type | Price at 2 matched **completed** swing points | RSI at corresponding points | Cautious inference |
|---|---|---|---|
| Regular bullish | lower low | higher low | Bearish momentum may be weakening; reversal **possible**, not guaranteed |
| Regular bearish | higher high | lower high | Bullish momentum may be weakening; reversal **possible**, not guaranteed |
| Hidden bullish | higher low | lower low | Potential uptrend-continuation configuration, not an automatic buy |
| Hidden bearish | lower high | higher high | Potential downtrend-continuation configuration, not an automatic sell |

Regular bearish and regular bullish are illustrated by parts of the original 91; **hidden divergence taxonomy is added as a comparison framework and has not been empirically substantiated by the cited originals**. Price must be compared at genuine sequential pivots with an explicit pivot rule. RSI must be sampled at the **same price-pivot bar timestamps**, not retrofitted to the indicator's convenient nearby peaks. Opposite-sign differences in arbitrary chart points are not verified divergences.

## Temporal traps to avoid
- **Current RSI lower ≠ bearish divergence.** A falling RSI while price is higher may be *cooling momentum*; regular bearish divergence requires higher *completed price swing highs* and lower RSI values at their corresponding times. The Telegram source supplies a useful negative control.
- Pivot lows/highs themselves become confirmed only **after** enough later completed bars. A detector that labels a signal at the pivot bar using right-side bars is future leakage unless it reports the later first-knowable timestamp.
- Price and RSI must use **identical instrument/venue/adjustment, candle interval, RSI length/smoothing and a fixed available-data cutoff**; 15m RSI, 1h RSI and still-forming daily RSI are separate measures. An alarm's firing time is not the indicator value on later screenshot.
- RSI divergence can persist for many bars while price keeps trending, especially around strong underlying structural support/resistance. A divergence alone cannot establish entry, stop, target or position size.

## CVD divergence is a different dataset and mechanism
CVD (cumulative volume delta) accumulates estimated **aggressive buy volume minus aggressive sell volume**, typically from classified trades; this is not simply total bar volume and is not RSI. Valid interpretation requires the **aggressor classification method, symbol, trading venue/coverage, derivatives/spot distinction, contract units, anchor/reset interval, timestamps and trading-session handling**.
- Price **fails** to progress above a frozen resistance while CVD rises → *candidate* passive sell-side absorption of aggressive buying, **or** conflicting venues, hidden liquidity, a major size replenishment, offsetting supply / volume-classification artifacts. **Absorption is not proven** without valid microstructure / order-flow evidence.
- Price falls to lower lows while CVD fails to make matching lower lows → possible sell-pressure exhaustion / bid absorption, **not** a mandatory long.
- CVD high-to-high comparison across **different resets** (daily vs weekly vs session reset) is invalid. A positive CVD absolute number across sessions cannot by itself establish strength.
- Price range / 'volume void' requires **volume-at-price profile** to verify; time-volume histograms cannot certify absent price-level trading.
- The reviewed primary RSI education slides and Telegram screenshot contain **no independent valid aggressive-side trade tape or synchronized CVD series**. Thus these CVD cases are falsifiable *research questions*, **NOT observed wins or verified actual CVD signals**.

## Next source-only checklist
1. From each image, classify `PRICE_RSI_REGULAR / HIDDEN / MOMENTUM_COOLING / PIVOTS_UNPROVEN / CVD_DATA_MISSING` with factual source evidence and no retroactive labeling.
2. For any price-RSI divergence, retain `bar_1_time, bar_2_time, pivot_1_first_knowable, pivot_2_first_knowable, RSI_config, settled_candle_status, historical_support_resistance`.
3. For CVD, first locate original chart **with trade-flow data**, identify `anchor_reset` and venue before classifying. If none exists, **mark NOT_VERIFIED**, never infer from ordinary volume.
4. Continue other accessible Library handwritten examples and video-frame provenance. Do **not** restart suspended EXP-SRC-001, S02, market scanner, independent trading case, backtest or production coding.

**Limit:** Source understanding has improved, but `imagesIndependentlyMasteredCount=0`, `unseenChartTransferDemonstrated=false`, and economic edge remains unverified.
