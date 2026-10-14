# S02 D01 — Independent multi-timeframe swing judgement (LOCKED BEFORE NEXT REPLAY)

**Evaluation category:** POINT-IN-TIME RESEARCH / NOT ACTUAL TRADING / NO CLAIM OF EDGE
**Decision input:** Git HEAD `b27143af4389bfa4c22d6771f54845478122ecaf`; `current_card.json` blob `ef4cbbcd796d2e04bbc6ba2edbbbb563275ee9e3`; `state.json` blob `d11550dfad274c0b169703ba9c0d2b13c621ff21`.
**Checkpoint:** step=1 / relativeSession=3 of 60; learning revision 11 / CANONICAL R-001–R-015 loaded; market scanner is only an evidence compressor; 18 entire new chart packets examined + separate traces for both existing pending symbols.
**Temporal gate:** no D02/future-price card inspected. Daily card bars end T+0D. Weekly T+1D and monthly T+24D labels represent incomplete period-end *buckets*, not extra underlying future daily sessions. Pending prices were matched to the final daily closes.

## Market and capital discipline

The observed masked KOSPI closes 3,019.18 at D00 and **2,959.46 at D01 (-1.98%)**; KOSDAQ 983.20 → **953.43 (-3.03%)**. Both fell hard in the two previous sessions, then bounced on the final observed session. Interpret as volatile drawdown with an uncertain reflex rebound, NOT proof of a fresh bull or a nonstop crash. Reconstructed universe **2,766** stocks, scan errors **0**, machine candidates **167**, reviewed deep candidates **18**. Historical KRX listings and chart adjustments remain incompletely exchange-certified. No forced exposure merely because the screen returns 18 names.

Starting/snapshot equity KRW **10,000,000**, cash **100%**, two **unfilled** first bids, **zero invested shares**, PnL **0.00%**, zero recorded costs, no stops. The 232,000-limit strong-name reservation never filled despite interim high 248,500: mark-to-market gain from 237,500 to 242,000 is **NOT a realized return**. The weak-name original bid likewise never filled. Post-decision maximum cash reserved is **10%**, total equity still cash until a later qualifying fill. Opportunity cost and nonfill remain important evaluation outcomes.

## Frozen review decision

| Asset | Initial thesis versus T+3 evidence | Decision | Historical frozen order |
| --- | --- | --- | --- |
| `ADDC44271E` | Price 242,000 vs 20D 231,425, 60D 223,867, 120D 216,417; 237k box top has been exceeded, highs 244,500→248,500→247,500, latest close 242,000. Prior 230.5–233.5k support near MA20 still exists. Last upper candle closed below its open, participation normal 0.86–0.90x after preceding expansion 1.74–1.97x; bearish RSI divergence and upper supply warning. | **KEEP_PENDING** | FIRST 232,000; stop 215,500; 10% budget; expiry session 15 unchanged; NO second tranche |
| `A8608C9A61` | New high 28,600 fails, recent closes 27,550→26,800→25,900; latest low 25,100 and close 25,900. 25,080 support has held at close, but 24,800 pending bid would require trading below 24,875 lower edge of that accepted support zone. Latest value ~1.18x, pullback activity not contracting; daily ATR% 5.16 and limit-stop 6.05% = only ~1.17 ATR, while overhead rejection at 27.55–28.6k strengthened. | **CANCEL** | Remove prior FIRST 24,800/23,300/28,000, unfilled; no replacement market order |

**KEEP objection:** Newly accepted 234.06–238.19k zone would have to weaken before a 232k lower bid executes. Its 7.11% stop risk is ~2.5 daily ATR and its first 248.5k revisit provides only ~1R gross; continued breakout and trend extension are **unproven**. This remains a capped-risk, small-size trend-following optionality hypothesis, not proven upside. If weakness becomes accepted below important supports, cancel rather than buy simply because the price is low.

**CANCEL objection:** The stronger 24.0–25.1k historical box/support is not conclusively destroyed; future price could dip to 24.8k and rebound to 28k. Canceling sacrifices potential opportunity. The decision instead favors avoiding a conditional *falling-knife* fill after a second failed 28.6k high and expanded volatility made 23.3k protection unusually exposed. That forecast must be measured against any future missed rebound, not rationalized retrospectively.

## Independent entire 18-candidate audit (machine labels not accepted as decisions)

| Asset | Chart-first state | Evidence, rejected flaw / re-entry condition |
| --- | --- | --- |
| `ADDC44271E` | **KEEP_PENDING existing** | Rising 20/60/120 MAs, genuine prior box 206.5–237k, last accepted 234–238k with leadership in weak tape; cannot chase 242k upper test; 232k patient limit has structural but unconfirmed future retest logic; no newly purchased position. |
| `A7AD778970` | WATCH / no trade | 35,514 adjusted-looking, high 39,127 rejected with 2.01x traded value, daily ATR 6.65%, nearby short-range invalidation cannot be justified; deeper 26.9k shelf too distant. Chart demonstrates demand but buying after an extension exposes wide drawdown. |
| `A45D6240AA` | WATCH | 7,875 below MA20 7,942 after 9,150 high retraced, ratio .50 and ATR 7.75%; 7.30–7.83k support has not shown confirmed price acceptance following upper failure. |
| `A505ADBA83` | REJECT | 226,697 sits below falling MA20 239,532/MA60 243,310/MA120 255,407; 221.9–226.6k floor support not enough to reverse overhead supply, traded value .58x; adjusted-looking price granularity. |
| `A3E368ED3E` | WATCH | 8,720 above rising 20/60/120; broke 8,670 box upper on prior money spike but stalled under 8,920 highs, previous close fell to 8,610. T+0 bounce 8,720 only .73x; meaningful stop below 7.9–8.0k is wide vs nearby 8.9k high. Seek new acceptance before a price reservation. |
| `ADCBA76A71` | REJECT | 89,900 after collapse from 110,500, below MA20 99,140, ATR 7.98%, 85.9k support tested but no multi-day reversal confirmed; high drawdown risk. |
| `A8D37E97AC` | REJECT | 8,820 with .24x value and 10.29% ATR, failed 10.3k range and 8.4–8.8k indecisive role, no convincing support-volume defense. |
| `A1258338EF` | WATCH | 12,898 flat three closes under 13,146 observed high with ultra-low .83% ATR, 12,385–12,699 acceptance but weak fresh price progress. Odd adjusted price ticks need independent validity check before any executable limit. |
| `A5F009F0C4` | **WATCH priority** | 21,600, prior 18,900–21,450 box, broke toward 22,150 on relative value 2.96x then 2.24x; latest low 21,150 and close 21,600 at 1.13x suggests first retest attempt. But retest/upper-role acceptance remains short and nearest 22,150 overhead gain is only 2.55%; structural stop toward 19–20k much farther. No asymmetric first-entry/stop/target proven, don't force order; re-evaluate if 21.45k support persists with quality volume and room above 22.15k opens. |
| `AE97585B00` | REJECT | 11,500 at 9.12% ATR after 13,300 peak and extraordinary 10.11x turnover, latest low close weaker on .79x; 11.34k level has turbulent nearby supply up to 12.2k, false rebound risk. |
| `AED475BEAC` | WATCH | 15,350, daily support ~14.68–15.20k, improved close but prior ~54.5x and ~17.6x turnover shocks, 17.45k overhead and lower reference 11.55k, current RR poor; don't chase after impulse. |
| `ACBE3BB43C` | REJECT | 22,950 after 27,450 supply test and 22,850 near-close selloff on ~4.90x volume; latest 0.45x is not proven accumulation; 22–23.65k role ambiguous. |
| `A3658CAE97` | REJECT | 4,550, trading value .15x, ATR 10.17%, 4.14–4.78k broad congestion overlaps price: structural stop vs upside undefined. |
| `A5A342D7FF` | WATCH | 9,360 reclaimed from low 8,600 with .93x value; 10,150 known upper supply, 8,400–8,600 support, no favorable risk/reward after fill risk. |
| `A100467D6D` | REJECT | 6,120 below 20/60/120 averages after falling from 7,480; box floor ~5,970 could be support but money .56x, no acceptance/reversal confirmed. |
| `A92C3EF6DB` | REJECT | 2,905, ATR 11.49%, 3,745 prior high to 2.77–2.81k lower test, .35x trading value and 3,320 supply nearby: a volatile bounce is not a stable trend entry. |
| `A98A64A061` | REJECT | 20,069, ATR 8.27%, 23,292 recent high rejected, ~21,827 accepted overhead; machine-adjusted fractional price and shallow recent support~18.77k limit execution unverified. |
| `A77ED669B9` | REJECT | 12,825 below MA20 13,626/MA60 13,398, recent 15,900 high to 12,400 low, .25x value; no stable recovery from drawdown. |

## Research assumptions, future test and error policy

- The 18 visible symbols are only the machine-compressed top set of the 2,766-stock snapshot, **not** independent proof that no omitted candidate can outperform. A future winner outside this set is a discovery failure to investigate, not retroactively credit.
- The rejected `A8608C9A61` may recover; future missed winner gets recorded. The retained `ADDC44271E` may gap below stop and lose; still count it. No rewrites once bars are revealed.
- The scanner's machine `EXECUTABLE` classification does **not** give permission to buy. Structural invalidation, overhead room, realistic daily volatility, true money/price acceptance and market regime are more important.
- If a later order fills, strict HOLD preserves original shares, stops apply every session, no default next-open market purchases; D02 follow-up is 3 sessions later **review**, not a 3-day holding limit or an expiry.
- A candidate's weekly `T+1D` / monthly `T+24D` label is a partial bucket's nominal period end; no future daily observation exposed. Price-data adjusting, news point-in-time, true order book/liquidity/costs are still limitations. Scoring demands filled/unfilled, commissions, benchmark, cash drag, stop-out, and right-censored swings.
- This is the decision **before** D01 is executed/replayed; no outcome or future price is cited and no expert-grade or profitability claim is warranted.

**Frozen summary:** KEEP_PENDING `ADDC44271E`; CANCEL `A8608C9A61`; no new entries. Decision written together with `decisions/D01.json` as a single atomic Git commit; only then should the engine reveal next three historical sessions.
