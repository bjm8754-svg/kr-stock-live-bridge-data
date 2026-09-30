# Crypto Blind Walk-Forward V2 — E02 Postmortem

## Result
- Hidden start date (revealed only after all 24 decisions): 2023-02-27
- Initial capital: KRW 10,000,000
- Final capital: KRW 10,074,060.54
- Total return: +0.741%
- Max drawdown: -7.11%
- Peak observed equity during the episode: KRW 10,781,250.15 after D09

## What worked
1. The first V-reversal was not chased. D01-D03 stayed in cash after the initial breakdown.
2. The later trend-bridge/retest was recognized and sized up. D07 introduced 2x sleeves without an arbitrary leverage cap, and D08 produced +8.428% at the account level.
3. Relative strength was used rather than forcing BTC and ETH into the same decision.
4. Oversold RSI was repeatedly rejected as a standalone buy signal.
5. When the major 20/50/100-day structure broke late in the episode, cash was used rather than forcing long exposure.

## What failed
1. Profit retention was poor. Equity reached KRW 10.781m (+7.813%) but finished only slightly above flat.
2. D10 still carried too much directional exposure into a failed continuation. All four sleeves stopped on day 51 and the account lost -3.661% in one interval.
3. After the main trend ended, D12/D17/D18/D19 generated repeated small losses. The system/assistant was still too willing to interpret first reclaims as actionable before a durable new regime had formed.
4. The D19 ETH add was especially instructive: relative strength was real, but the surrounding market regime was still choppy and the 50/100-day role was not stable enough for leverage.
5. The episode shows that finding one excellent ATTACK is not sufficient if subsequent chop is allowed to recycle a large part of the gain back to the market.

## Generalizable lesson — do not hard-code from one episode
The next blind episodes should test, without tuning to E02, whether the assistant can distinguish:
- a true trend bridge/retest worth scaling,
- a first reclaim inside a damaged/choppy regime,
- a mature trend where gains should be protected,
- and a fresh role reversal that deserves a new probe.

Do not add arbitrary scorecards, leverage caps, or one-off moving-average rules from E02. Update the review protocol only if the same failure mode repeats across independent blind episodes.
