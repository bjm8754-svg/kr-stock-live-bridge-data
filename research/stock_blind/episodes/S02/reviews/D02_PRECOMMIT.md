# S02 D02 — Independent swing decision, precommitted before next 3 masked sessions

**Source HEAD:** `b72faae80603797a389ea1de94bc423fa6129ab8`; **Card SHA:** `b7062bc93f9c77551ded00355338d1ffbf765901`; **State SHA:** `15fbf14c23ead1d0a54f259e0b47697bbc55e633`. S02 step=2, relativeSession=6, episode 60 sessions; V3 learning revision=11. Research only; ZERO real brokerage activity.

## Actual outcome of D01 (not a profitability claim)

- Simulated equity **KRW 10,000,000**, cash **100%**, return **0.00%**, drawdown **0%**, fee and turnover **KRW 0**, shares **0**, no limit buy ever filled yet.
- **A8608C9A61** first limit 24,800 was actually canceled in the replay with `CANCEL_USER` at relative session 3. That is a decision execution, **not proof of a good exit or avoided loss**. This canceled symbol is absent from the new pending and new top-18 charts; missed rebound/winner cannot be scored from current input and must be tracked with a strictly cutoff-bounded follow-up dataset later.
- **ADDC44271E** FIRST 232,000 still unfilled after lows 237,500 / 237,000 / 237,000 in the next observed three sessions. It is not a bought winning/losing stock. Last close 239,000, with ATR 2.56%, declining from recent 248,500 high; 237–239k zone has survived but additional failed high warning. 
- KOSPI previous step 2,959.46 → **2,944.41** (-0.51%), KOSDAQ 953.43 → **953.47** (roughly flat). Twenty-observation close-based movement approximately -6.91%/-8.07%. Final market session lifted from a prior selloff; no established bull trend. Whole universe reconstituted **2,764**, scanned **2,764**, errors **0**, mechanical candidates **170**, analyst reviewed **18**.

## Decision 1 — KEEP original waiting ADDC bid

Original order **232,000**, structural stop **215,500**, frozen budget **10%**, expiry relative session **15**, no ADD. Chart has rising 20/60/120D MA at 233,400 / 225,183 / 217,650, recent lows 237,500→237,000→237,000 (old 237k box top) and falling participation following the exceptional upside volume around the 248,500 high (recent estimated value ~0.6, 1.03, 0.70× 20d). Trend pullback is not *yet* a high-volume breakdown. The 232k bid is below today's 239k and around an older 230.34–233.66k support and rising MA20, so waiting is economically meaningful. **Strong objection:** 248,500 is now accepted resistance and price momentum is contracting. A drop below 237–238k may be a failed breakout; avoid treating any down-price fill as guaranteed support. New evidence can prompt cancellation at a later review; do not look ahead.

## Decision 2 — independently select NEW relative-strength A245 conditional lower reservation

**A2452E7F51** (KOSPI, masked): last 564,000, open557k/high568k/low547k, current ATR ~3.31% close, MA20=516,750, MA60=515,858, MA120=479,617. 40-session range **483,000–545,000** with repeated highs (five touches) and earlier rejection around 555–556k. Three rising decisive price closes **531k→552k→564k**, accompanied by ~2.27×→4.19×→2.12× estimated trading value, demonstrate *actual price progress with participation*. Weekly and monthly histories previously show failed upper tests at 555–556k; latest close **564k above those areas** suggests acceptance is beginning but not yet retested. This is original chart logic, not a scanner instruction.

- **FIRST reserved price: ₩533,000**, near the 526,355–538,680 historic close/decision zone, 5.50% below cutoff close and below prior 545k range ceiling. A retest could be healthy base organization; could also be a failure after break beneath 545k. This is a conditional patient bid; **not a next-open buy**.
- **Structural protective stop: ₩505,000**, below 507–512k earlier defended support and ~516k 20/60 averages. The whole prior range is 483–545k; 505k stop is NOT the entire box lower boundary and could be whipsawed if old base holds 492k. Risk from reservation 5.25%, about 1.6 current daily ATR; after daily gap or a single high-range candle, realized loss can be greater.
- **Full-exit target: null / trend-managed**. The first known high 573k provides ~7.50% gross from bid (about 1.43R before costs). A genuine multiweek trend opportunity would require price to push through and **accept above the previously observed 573k supply**. Do not invent a second higher objective or credit it as certain. On filling then rejection near 573k, reassess hold/trim/exit according to the next frozen review, with daily protective stop active; no automatic forced exit at three sessions.
- **Budget 11%** of KRW 10m, enabling **2 whole shares** at reserved 533k with fees inside 1.1m (gross ~1.066m, 10.66% actually deployed). For two shares and normal stop sale at 505k, *nominal* account risk ~~₩56,000 (0.56%), exclusive of slip, gap, fees. **No ADD** because no defensible separate second entry. Unfilled expiry at relative session **18**, distinct from swing holding horizon.
- **Strongest counterargument:** This is only the first close clearly above 555–556k resistance, and retreat all the way to 533k under prior 545k ceiling might signal a bull trap; important that prior buying effort not disappear. If it advances without a fill, register missed leader, do not market chase.

**Portfolio if both first limits fill at their quoted prices:** initial ADDC 4 whole shares (~₩928k) plus A245 2 whole shares (~₩1.066m) before fees; nominal combined ordinary-stop loss ≈₩66k+₩56k = **₩122k (~1.22% account)** plus potential gap/fee/correlation losses. If neither fills, stays KRW10m cash 100%, no claim of earning anything. Combined resting *budgets* 10%+11%=**21%** are not holdings or invested weights.

## Full-machine-compressed 18-candidate independent assessment

| Asset | Verdict | Price/participation/structure-based reason |
| --- | --- | --- |
| `A7C85F621C` | WATCH | KOSDAQ 3,465, 3,005–3,330 base reclaimed, but 5.62× then 5.16× turnover days did NOT break/hold 3,565 resistance; 3,820 further supply. Fresh close 3,465 on 1.30×, improving but waiting for conclusive price progress vs absorption at 3,500–3,565. A 3,330 bid with a stop below 3,165–3,200 has poor reward to immediate 3,565 ceiling. |
| `A9E0518E89` | WATCH | 284,500 on 2.0× turnover and strong close, BUT previous weekly/monthly 294,000 prior high only 3.34% overhead, ATR5.05% and old 263.7k incomplete support acceptance; no attractive fresh bid. |
| `A6AA95570F` | REJECT | 34,300 with 7.86% ATR, 40,850 20-day peak, RSI divergence; current 0.70× value despite bounce, support ~33.2k ambiguous; small near-target reward versus big volatility. |
| `A6D21613F0` | REJECT | 40,215, high→near-low close with ~2.09× value at 39.9k support test; could be supply distribution. MA20 41,878 overhead and 38.2k farther support; avoid catching fresh downside impulse. |
| `A2452E7F51` | **NEW CONDITIONAL LIMIT** | 564k after volume-backed 531→552→564k trend, 483–545k old box and 555–556k old supply broken; reserve 533k near real base consensus, stop505k; must accept through 573k to validate multweek extension. |
| `AAF897EBA8` | WATCH | 16,550, consecutive stronger closes but last value0.57× and RSI bearish divergence, 17,450 20-day high close supply; no favorable protected bid today. |
| `ADCBA76A71` | REJECT | 92k, 20D average99.35k overhead, after violent fall from ~114.5k; bounce value0.64×, price recovery still not accepted. |
| `AB1A0FB409` | REJECT | 67,088 adjusted fractional, decline from 79,673 high, lower-close on ~0.38×, overlapping 67.1–74k supply and ATR6.91%; unrealistic execution units. |
| `A4A981F9AB` | WATCH PRIORITY | 27,850, genuine 24,300–27,500 range acceptance and fresh 27,400 low reclaim of 27,500. But 28,600 high only ~2.7% overhead from current and low participation0.9×. A limit 27,500 with a stop under real 26,750 role gives ~2.73% risk for ~4% high return; case needs deeper acceptance or sustained supply removal. |
| `ACC6E3D0E1` | WATCH PRIORITY | 47,250 after very large one-day 40,200→47,250 rally on 5.01× money: price progress REAL, but ~18% day and prior 40–45k whipsaws make fresh high chase unacceptable. Need multiple-day acceptance above old 45.2k high or controlled 41.5–43k retest (not preemptive one-shot limit against a giant event bar). |
| `AAE5C85B45` | REJECT | 39,970, value ratio only0.10×, ATR11.61%, repeatedly failed 41–46k, below MA20/60; no liquidity/structural edge. |
| `A958B0DB98` | REJECT | 52,400 at ATR15.53%, down from 89,100 20-day peak, below MA20 69,660/MA60 57,428, 49–55k support far too wide; reversal unproven. |
| `A12514418F` | WATCH | Quiet 10,700 high over former 10,550 cap, ATR1.57% and 41 contacts at box upper, but last value0.70× and little acceleration. Trade only with evidence of new price acceptance and sufficient risk-adjusted upside. |
| `ABAB0762F8` | REJECT | 2,705, earlier 32× turnover spike failed to establish persistent higher prices, ATR8.88%, recent 2,576–3,073 choppy range and fractional adjusted looking ticks. |
| `AD65181745` | REJECT | 22,215, below 20/60/120 falling MAs, lower support 21.6k but overhead 23.7–26k not reclaimed, thin value0.38×. |
| `AE2478B68B` | WATCH | 30,453, 28.45–29.1k support and rising short/medium average, but historical next 31,710 nearby resistance, ATR6.31%, ratio0.62×, not enough payoff room. |
| `A3AD88B157` | REJECT | 4,840, down under declining MA20 5,586 and MA60 6,181, ATR13.32% and money0.28×, no safe first entry. |
| `A45D6240AA` | WATCH | 8,175 bounce from 7,625, but ratio0.36×, daily ATR7.8%, repeated 8,288–8,825 supply overhead and prior high9,175 remains remote; no supported asymmetric first order. |

## Independence, test honesty, and research debt

1. **All 18 inspected ≠ all 2,764 deeply read.** Scanner may miss future winners outside shortlist; failure of selection must be assessed separately (M-01 expert goal).
2. **D01 cancellation opportunity-cost surveillance gap:** The just-canceled `A8608C9A61` disappears from new pending-specific and top-18 cards. Without an outcome chart, *cannot* determine if avoiding it saved loss or missed a favorable rebound. The simulation's cancel event is verified; the economic decision is not. Fix only in a separately tested, point-in-time bounded research path, do not peek at future bars to justify D01.
3. The two pending orders remain independent capped-risk simulations, not live purchases. BUY_LIMIT order fills require future low strictly below limit if open above limit, as precommitted; intraday exact touches are not guaranteed fills.
4. Today's A245 entry 533k is inside prior box: the reversal-case failure risk is explicitly registered. A simulation result cannot make it structurally correct by hindsight. Multiweek HOLD decisions must not add/sell merely to restore weights.
5. Some historical vendor-adjusted stock prices have invalid KRX tick fractions, not acceptable as future broker order prices. The selected 533k/505k are valid integer won values at current face value but still require cross-provider corporate-action validation.
6. Evaluation after next session block: read exact filled/nonfilled order events, cash usage, daily stops, missed opportunities, index backdrop; then re-read held/pending and 18 refreshed charts before D03 lock. No single attractive plan is proof of expert-level skill or economic edge.

**Locking this analysis and `decisions/D02.json` in one Git commit now, before revealing any next hidden session.**
