# S01 D04 — precommit independent swing review

Status: BLIND_DECISION_FROZEN_BEFORE_FORWARD_OUTCOME
Source-HEAD: `ddb99030a86717dde633b5931c3a06a46d17a202`
Current chart snapshot SHA: `30fa94d999b316861fdc6c367cd24ccdd9a9b530`
Learning gate: revision 7 (canonical R-001 through R-011)
Episode: S01, current step D04, relative session 12, masked stock identities & calendar
Current market: reconstructed 2,592 names, 79 machine candidates, 18 deep-review candidates and 2 existing holdings, 0 stock-scan errors.
Provenance: S01 `current_card.json` and `current_details/{assetId}.json`; no future observations used.
Execution model: rebalance at frozen review close; stop live on each intervening daily bar, fill at stop unless gap down, then open; costs 5 bps buy and 20 bps sell. **This S01 simulator does NOT support waiting limit orders, second buys at contingent levels, or mechanical target sale.** Thus do not call a paper waiting price an executed entry.
Hypothesis horizon: continuation swing for multiple weeks **if structure survives**, never automatic 3-day exit; periodic review every three sessions. The remaining 18 sessions of S01 are too short to adjudicate some multi-week trends. Final episode P&L is mark-to-market, open swing outcomes censored.

## Market/context: why selective despite two-day relief

Masked market KOSPI last close ~2,432.72 and KOSDAQ ~695.59 after a deep relative-window drawdown to recent closes ~2,293.70 and ~643.39. The last two-day rebound has not re-accepted the prior 2,465–2,525 KOSPI or 707–725 KOSDAQ zones. This is **not** evidence of new synchronized leadership. The stocks' prices and price/volume traces, not expert school labels, control these choices. Strong stock-specific relative trend may still survive.

## Existing holdings — independent structural reevaluation

| ID | Now | Position weight | 5/10d close progress | Core structure | Locked decision |
| --- | ---: | ---: | --- | --- | --- |
| `A91ECD3412` | 19,050 | 21.56% | +13.2% / +39.8% | Accepted 16,318–16,733 event-close zone; strong money expansion ~1.73x vs estimated 20D; current close 19,050, recent high 19,490 | HOLD; stop 16,100 (previous 15,450); 19,490 close acceptance checkpoint; target null |
| `A0E433D981` | 86,400 | 15.29% | -2.3% / +6.3% | Higher-frame 75,075 accepted support and MA20>MA60>MA120; prior 87,900–88,350 overhead not yet sustainably reclaimed, money only 0.84x | HOLD core only, stop 74,500; no repeat of invalidated ADD; target null |

**Risk audit (approximate, assumes stop fills without gap):** A91: price-stop distance (19,050-16,100)/19,050 = 15.49% or ~3.1 current ATR; portfolio 21.56% allocation × 15.49% = ~3.34% account exposure. A0E: (86,400-74,500)/86,400=13.77% or ~3.3 ATR; 15.29% × 13.77%=~2.11%. Combined *marked-to-stop hypothetical loss* ~5.45% portfolio, excluding overnight gap/slippage/correlation. Not a measured maximum loss. The stops are under distinct structural levels, **not** derived from a flat 10% prescription. Closing the fast winner solely because the 3-day review arrived would contradict the swing thesis; reversing a failed tactical add is still valid.

**Stronger counterarguments:** A91 price already advanced ~40% in 10 sessions with RSI ~73; a higher-timeframe failure could unwind fast. A0E had a failed 87.9k breakout and retest, and repeated upper resistance may cap appreciation. Continued HOLD is a falsifiable risk-taking decision, not a guaranteed winner.

## Eighteen fresh machine candidates — no machine EXECUTABLE promotion

| Masked ID | Chart reconstruction and limiting evidence | Decision |
| --- | --- | --- |
| `ACAFDFEF25` | Close 38,200 exceeds prior box-upper ~36,467 for two sessions; prior day money expanded, today's ~1.14x; former resistance 36.1–37.0 remains SUPPORT_CANDIDATE, not accepted. At 38.2k price versus 34.4–35.4k structural invalidation yields ~7–10% downside and no confirmed next overhead resistance to justify current-close reward. Pullback to ~36.2–36.7k might improve entry but cannot be represented as a filled conditional order in this engine. | WATCH, no simulated fill |
| `A2A649BDD0` | Close 767,085, ~+23.7% in 10 sessions, ATR 6%, machine stop 593,777 (~22.6% from current); non-tradable adjusted historical prices and broad volatility. The first structural checkpoint 769,055 is already nearby, reward unproven. | REJECT current entry; adjusted tick/source audit needed |
| `AC4007E7C1` | Close 32,600 but -26% 20-day progress; recent single-day bounce meets supply from 34.6–38.3k and the model stop 30,050 does not justify assumed swing reversal. | REJECT |
| `AA2E69ADEF` | Close 70,800 after -16.7% 10-day slide; multiple 71.6–90.8k accepted overhead resistances; reclaimed low-level support not enough for an independent long. | REJECT |
| `AB47AF0AE9` | Close 5,100; current volume/money ~0.3x, 20d -15.8%; bridge resistance at 5.28–5.5k, proposed risk/reward deceptive when using narrow 4,800 stop. | REJECT |
| `A73A81503B` | Close 3,890 after vertical candles with peak volume 10–13x and a later upper rejection; 5d +15% but daily position near bottom of bar and ATR ~12.2%. Stop 2,375 is structurally far. | REJECT chase |
| `A8FA1922F4` | Close 59,000 near 7% of daily range, ATR ~16.8%, current participation ~0.27x, divergence warning, model 56,914 stop too near relative to volatility. | REJECT |
| `A24DE2421A` | Close 4,410, weak 0.13x money, upper rejection + divergence, broad range after failed approach to 5,110. | REJECT |
| `AF7DF030AA` | Close 5,330, MA20<MA60~MA120, recovery toward 5,520 overhead with weak 0.17x money and ATR 16%. | REJECT |
| `A0A6A2265C` | Close 14,010, strong money ~1.78x but overhead 14,462 only ~3.2% away; machine invalidation near 10,873 => 22.4% current risk, no reward room. | REJECT current entry; re-evaluate only after shelf acceptance |
| `A54A814C61` | Close 110,500 below declining/retested 115–126k supply, 20d negative, spring bounce not yet confirmed as higher-frame reversal, current money 0.50x. | REJECT |
| `AC49A9FCAA` | Close 342,500 with money ~1.98x, breakout 319.5k but major immediate 351.2–353k supply; even machine RR ~0.18 at current location. | REJECT chase |
| `AB03C9E66D` | Close 5,100, 20d near flat, structure still confronts 5.3–5.66k upper band, reactive 4.72k stop susceptible to reversal volatility. | REJECT |
| `A93073C827` | Close 22,350 after +71% 10-day move and 194x daily volume shock, now long upper wick; high RSI ~81; inflated breakout extension makes safe contemporary invalidation implausible. | REJECT chase |
| `AE151E637C` | Close 156,700, money ~1.91x, first close above ~156.4k decision zone but historical 158.9–162k supply directly ahead; broader averages mixed. | WATCH acceptance/retest, no buy |
| `A67E866540` | Close 144,200, spring rebound within persistent 20<60<120 MA downtrend and overhead ~152.3k; 10d -9.4%; insufficient reversal proof. | REJECT |
| `AD66E4A5AF` | Close 70,900 on 1.77x money and 1.7x volume, testing 70,300 weekly box top, but old monthly ~71.4k overhead and first day over pivot. | WATCH confirmed acceptance above 70.3–71.4k / better risk location |
| `A3888FBD09` | Close 9,660 in downtrend; proposed stop 9,530 only ~1.35% vs ATR 3.5%; multiple 9.85–11.16k overhead bands. | REJECT |

**Zero immediate new buys is not a win on stock picking:** it is a market- and location-sensitive choice; subsequent missed winners will be logged. No candidate is permanently blacklisted. Three WATCH names are ACAFDFEF25, AD66E4A5AF and AE151E637C. No "source guru" gets privileged explanatory weight.

## Freeze and next grading criteria

1. Commit this review with D04 in the *same Git commit* before exposing any ensuing 3-session prices.
2. Use the pre-existing read-only outcome pipeline to settle stops and mark the account to market; inspect the new blind D05 decision card only **after** commit.
3. Primary questions for next checkpoint: did the 16.1k A91 stop survive as structurally sensible vs whipsaw? Did the A0E 88.35k overhead get accepted/rejected? Did we miss a genuine accepted breakout by declining ACAF/AD66? How much turnover and cash drag resulted?
4. **Do not call that 3-session result a completed multi-week swing outcome.** Hold theses remain active if not invalidated. Compare against full 30/60/90+ session independent episodes later; original S01 stays unchanged.
5. S01 contains price/volume/time and reconstructed exchange universe, but does **not** contain point-in-time verified fundamental/news/catalyst evidence or live execution quality. No production trade or actual return is implied.
