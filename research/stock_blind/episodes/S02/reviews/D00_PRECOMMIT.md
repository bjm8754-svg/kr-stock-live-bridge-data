# S02 D00 — independent blind swing entry and reservation audit

**LOCK BEFORE ANY FORWARD BAR / NOT A REAL INVESTMENT**
Source HEAD: `141b052d054bd23cb69f35e754bcfec718947c32`; S02 `current_card.json` blob SHA: `70e7300871532cd820e4abcfc5f50c043aec2b6a`.
Snapshot: episode `S02`, relative session `0`, `futureIncluded=false`, no positions, initial simulated KRW 10,000,000. Reconstructed 2,768 active KOSPI/KOSDAQ candidates, analyzed 2,768, errors 0, machine candidates 177, deep candidates 18. Candlestick daily T+0 close equals each card close; no T+1D daily trace was observed. No post-cutoff card, fill log, or future outcome accessed.

## Market first, not scanner labels

Masked KOSPI 3,019.18, -5.63% / 20 observed sessions; KOSDAQ 983.20, -5.31% / 20. Their last three daily closes continue downward. This is a deteriorating market, not an indiscriminate breakout-buy context. Two long-lived relative-strength structures are selected for **conditional lower-price bids**; rejection/non-fill is acceptable. No assumption of company news, sector catalysts, live execution, or trade-by-trade CVD that the input lacks. No guru method is treated as privileged.

## Two independently chosen BUY_LIMIT reservations

| Asset | Cutoff close (NOT fill) | Precommitted FIRST BUY_LIMIT | Structural stop | Objective | Max reserved budget | Expiry (only if still unfilled) |
| --- | ---: | ---: | ---: | --- | ---: | ---: |
| `ADDC44271E` | 237,500 | **232,000** | 215,500 | **Trend-managed; target null**, no defensible measured historical overhead beyond 237,500 | 10% | Session 15 |
| `A8608C9A61` | 26,650 | **24,800** | 23,300 | **28,000** sell limit, below observed 28,300 prior rejection | 10% | Session 12 |

Both bids remain **unfilled at decision lock**, so invested ratio=0%, liquid cash=100%, uninvested cash outside reservation budget=80%. Nominal combined maximum first-leg mark-to-stop account risk after hypothetical fills is approximately 10%×(232k-215.5k)/232k + 10%×(24.8k-23.3k)/24.8k = **1.32%** plus potential gap risk, fee drag and correlation. This is NOT a worst-case loss guarantee. Both sizes fit cash budgets for whole-share fills (around 4 shares at 232k and 40 at 24.8k before fees), and do not assume a forced equal weighting or 1:2 tranche ratio. No automatic second buy; the expert-style optional additional tranche is absent where it has no independent structural justification.

`ADDC44271E`: daily/weekly/monthly support and progressive higher lows survived recent pullbacks while both masked broad indices rolled lower; current close 237,500 is at the highest accepted area, not a favorable first entry. Lower bid 232k revisits the 230.3–233.7k prior decision/swing zone. Invalidates at 215.5k beneath the accepted ~216.3–223.6k distribution. Risks ~7.11% of filled purchase or about 2.7 daily ATRs; hold for multiweek continuation **only if the price structure survives**. Absent defensible overhead resistance, no fabricated numerical profit target. At reviews assess whether a new high is accepted, whether 232k/220k support holds, and trailing stop only on evidence. For this study, `target:null` means no simulated profit-taking order, not an unbounded claim.

`A8608C9A61`: rising MAs and relative-strength advance, but an attempted high of 28.3k failed to extend despite elevated ~1.35x turnover and closed at 26.65k. This could be sell-side absorption at supply. Buying the current price would poorly compensate this. Patient first bid at 24.8k tests former accepted 24.65–25.08k support, invalidation 23.3k beneath accepted 23.38k area. First objective 28k prior to observed 28.3k rejection; upside from bid +12.90%, structural risk -6.05%, gross reward/risk ~2.13 (before buy/sell costs and unfavorable gap fills). If the pullback never occurs, **the correct result is a non-fill, not a win**.

**Execution is a real simulation contract, not a narrative:** BUY_LIMIT must be crossed after decision cutoff; if open<=limit and >stop, fill at open (price improvement), else require intraday low strictly below the limit and assume fill at limit; low exactly at limit alone is an ambiguous queue/nonfill. Stop loss is applied conservatively on same daily bar if both touched, and longer than 3-session waiting is explicitly permitted. Positions do not rebalance under HOLD. SELL_LIMIT objective triggers only on held stocks in subsequent bars; stop has precedence on ambiguous bars. No broker orders. Both expiry counters are measured from S02 session 0, not calendar dates.

## Full 18-name decision audit

| Masked asset | Decision | Ex-ante evidence and why it wins, waits, or fails |
| --- | --- | --- |
| `AC43539425` | REJECT | 44,200; recent break over old box has stalled under 46,071–47,135 accepted supply. Most recent lower close with ~0.70x turnover; machine stop 43,700 is only 1.13% of close versus 2.48% ATR and ignores accepted 42,640 lower support. Its reported 3.74R relies on too-tight invalidation. |
| `A2073AAE20` | REJECT | 173,022 after +15.5% 10 sessions, ~4.72% daily ATR, suggested 142,488 stop 17.65% below price and no supported overhead target. Adjusted-looking fractional tick levels prohibit a clean executable limit. |
| `A2452E7F51` | WATCH | 499,000 below 20D 513,200 and 60D 506,275, -6.2% 20-day; strong 468,000–493,000 support but the post-break rally failed near 510,000 and 520,000 overhead. Needs support acceptance and improved location. |
| `A2713D36F3` | REJECT | 50,552 below declining 20/60/120 averages, down -17.1% in 40 sessions. Claimed 49,865 structural stop is only ~1.36% vs ~3.4% ATR, numerical 9.32R an artifact of tiny stop. Deteriorating price. |
| `A7AC80CE11` | REJECT | 259,271 sits in overlapping 255,784–275,997 decision/supply zone and is within ~3% of multiple resistances; machine stop 256,811 is ~0.95% vs 3.73% ATR. Prices look adjusted/untradeable as displayed. |
| `ADDC44271E` | CONDITIONAL_LIMIT | Rising 20/60/120 averages, monthly 235k then 237.5k high, durable 216.3–223.6k shelf and 230.3–233.7k first retest candidate. No chase of 237,500; WAIT bid 232,000, stop 215,500, no fabricated target. 10% cash budget, expire after S02 session 15 if unfilled. |
| `AC33AE232D` | WATCH | 59,600 is below 20D 64,505 following -12.7% ten-session retrace, but remains above 60D 52,039. Preemptive 56,100 machine entry lacks observed strength confirmation; ~6.15% ATR and recent high volatility warrant restraint. |
| `AFAB59CAA7` | REJECT | 14,036 in downtrend below 20/60/120 MAs, -8.2% 20 sessions; machine stop 13,873 only ~1.16% vs ~2.9% ATR. Recent session close near low and no confirmation of support. |
| `A8608C9A61` | CONDITIONAL_LIMIT | Strong longer trend but high-volume failed extension: 28,300 intraday both prior and cutoff, cutoff close 26,650 lower with 1.35x traded value. Do NOT pay close. WAIT 24,800 near 24.65–25.08k support; structural stop 23,300 below prior 23.38–23.82k support, 28,000 target ahead of observed 28,300 supply. 10% budget, 12-session expiry. |
| `A49DD63579` | REJECT | 46,800 under 20D 48,755, 20d -5.4%, upper 48.45–50.9k supply; next reference 45.1k but prior support just broken, machine RR1.28 insufficient after market-risk adjustment. |
| `AA425265DE` | REJECT | 6,080 after -13.3% ten sessions, volume only ~0.28x normal, close below 6,145 breakdown watch. Machine 5,920 invalidation ~2.6% vs 6.94% ATR, not meaningful structural stop. |
| `AED475BEAC` | WATCH | 13,900 with 2.08x trading value, but prior extraordinary 48x/17x shocks indicate unstable supply. 14,200 failed breakout, 14,676–14,950 overhead nearby; from current to 12,650 stop risk ~9% for ~5.6% first reward, RR~0.62. Could revisit after true acceptance or much lower valid entry. |
| `A81A3CDA8C` | WATCH | 7,993 after +25.3% in 20 sessions; RSI divergence, 0.52x money and 8,199–8,281 supply immediately above. Wait for confirmed acceptance or supported retest near 7.62k rather than chase. |
| `ACF7E6F8DE` | REJECT | 22,900 after -18.4% in 20 sessions, below 20D 27,045 with 23.2–24.5k broken-role overhead, weak participation. Proposed 21,817 stop too close to turbulent 5.65% ATR; reversal unproven. |
| `A3B7B61465` | REJECT | 39,000 after +27.2% in 40 sessions but current money only 0.28x; resistance 41,077 imminent and 31,500 suggested stop ~19.2% distant, R/R~0.28. |
| `A6EC5F3065` | REJECT | 68,000 below all 20/60/120 averages, 20-day down -4%, latest candle closes at its low despite 1.59x turnover—potential fresh distribution. 67,262 nominal stop tight vs real loss. |
| `AB1A0FB409` | REJECT | 74,059 +27.5% in 40 sessions and ~1.53x value, but 76,289 resistance only ~3% overhead, wide ~14.25% stop to 63,506 and upper rejection/divergence. Machine RR0.21: late chase. |
| `A56584A7F8` | REJECT | 49,750 closes at daily low below 20D 51,423 with 0.49x participation and repeated upper failure near 50–53.7k; valid support 48.4–49.6k not enough to prove rebound. |

## What would invalidate my reasoning?

1. The broader index fall accelerates: reduce or cancel waiting bids on future reviews based on newly visible *then-current* data, not hindsight. Existing resting orders cannot know a future narrative; their protective stop/gap contract remains explicit.
2. If `ADDC44271E` never trades at 232k, count this as missed upside if it rises. No target success or invested PnL may be attributed to that unfilled order. If it fills but structurally fails through 215.5k, treat it as a true wrong swing read.
3. If `A8608C9A61` retraces under support and trades through 23.3k, distinguish stop-out versus next-open gap and evaluate whether the initial high-volume 28.3k rejection warned of exhaustion. If 28k is hit after a real fill, include all fees and target execution.
4. First review after 3 sessions evaluates **orders, fills, invalidation and new context**. It does not force expiry or liquidation for a multiweek thesis.
5. Compare opportunity cost of the 80% unreserved cash and all missed winners among 16 rejected names; do not reward holding cash simply because a weak market was observed.
6. Even with this repaired buy-limit simulator, adjusted OHLCV, historical listings, exchange tick sizes, market/sector events and queue-depth execution are NOT fully point-in-time independently certified. Status is **RESEARCH ONLY** and never evidence of actual investment skill at D00.

## Frozen evaluation plan

Before revealing the next three sessions, commit this audit **with** the matching `decisions/D00.json` atomically. On next masked card, score filled versus pending, exact bid execution, same-bar stop, target/stop, costs and relative market performance; keep right-censored positions active. Continue until at least the full 60-session study; out-of-sample proof across regimes is required before any skill claim.
