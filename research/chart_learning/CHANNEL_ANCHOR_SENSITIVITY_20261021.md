# September 8 annotated-channel anchor sensitivity: why attractive line touches are not a stable signal
**Date:** 2026-10-21 KST  
**Status:** ORIGINAL_PIXELS_DIRECTLY_EXAMINED / GEOMETRY_RECONSTRUCTION / RETROSPECTIVE_DIAGNOSTIC / NO_VERIFIED_TRANSFER.

## Scope, original, and analytic limits
- Single canonical Library-root screenshot: `chart-1(8).png` (1418×920, 637,124 original bytes); same market episode also has low-resolution phone capture `1788851445435.jpeg`. Both already included in BULK-012 and depth-review v41. This is **one more interpretive case, zero additional visually classified images**.
- Inputs are **screen pixels** and **approximate purple-box centers**, NOT exported OHLC, TradingView drawing-object coordinates, pre-event screenshots, executed trades or contemporaneous predictions. Image may have been rescaled; axes/calibration and precise candle OHLC are NOT VERIFIED. No 2h bar-end inference is allowed from the date labels.
- Chart origin convention: image x increases rightward; y increases **downward**. Above a diagonal price line therefore means **smaller y**, not larger y. Projection at x=1175, approximately the early-September purple retest zone; the nearby latest candle cluster is loosely y≈414, with several wicks spreading above/below. Interpretation is illustrative, not a precise event-time fill.

## Source-image reference points and alternative two-point constructions
Approximate candidates chosen from **three pre-identified purple low boxes**, not retrospectively optimized over all candles:

| Label | Image (x,y) | Approx. visual episode | Limits |
| --- | --- | --- | --- |
| A | (118,593) | late-May low/blue internal-rail reaction | Purple-box center, not verified wick low |
| B | (280,568) | early-June low/retest | Box center, nearby wicks vary |
| C | (534,519) | early-July support/retest region | Contemporaneous availability/confirmation uncertain |

For line y(x)=y1+(y2−y1)(x−x1)/(x2−x1):

| Variant | Slope (pixels y/x) | At x=1175, predicted y | Difference vs displayed line (px) | Latest candles vs this line |
| --- | ---: | ---: | ---: | --- |
| A–B | −0.15432 | 429.9 | +29.9 | loose y≈414 **above** the candidate line |
| A–C | −0.17788 | 405.0 | +5.0 | loose y≈414 **below** |
| B–C | −0.19291 | 395.3 | −4.7 | loose y≈414 **below** |
| Published blue interior rail (estimated endpoints ~118,596 and 1175,400) | −0.18543 | 400.0 | 0 | loose y≈414 **below** |

A positive y offset denotes a line appearing **lower in price**, because the picture y-axis increases downward. A–B projects ~**30 image pixels** lower than the published line, roughly **4–5 right-axis price units** under the approximately 5 units/33 pixels local scaling, but NOT a trustworthy price target. The **interpretation of September price location flips** between plausible anchor pairs. This is a structural decision-invariance failure, not evidence that A–B is the true method.

**Endpoint precision amplification:** At projected x1175, changing the B y anchor by just 5 pixels in A–B changes the extrapolation by approximately [(1175−118)/(280−118)]×5≈**32.6 px** (the exact effect also depends on which endpoint is perturbed). Wick/body/box-center choice, visible anti-aliasing and pivot confirmation therefore can overwhelm the estimated ~30px between A–B and the originally drawn channel. Bar-exact price anchors are required.

## Channel parallelism can also be selected retrospectively
The published internal rail is roughly y=596 at x118 and y≈473 at x782. At x236 it projects y≈574. The **upper solid rail** near the late-May purple swing high (x≈236,y≈253) is ~321px above the internal line; the **lower rail** through the deep end-July/early-August marked trough (x≈782,y≈796) is ~323px below it. This visually near-symmetric distance is consistent with a copied/offset parallel channel, but the same geometry is consistent with an analyst fitting **both** extremes after the August trough formed. **Neither authorship nor real-time creation order is visible.** The dramatic channel-floor touch cannot count as ex-ante validation unless a timestamped lower rail predates it.

## What a horizontal baseline says instead
A marked late-August swing high around (x≈965,y≈442) serves as an illustrative **fixed horizontal resistance baseline**. The early-September candles near x1175,y≈414 appear above that earlier swing area, while simultaneously below the originally drawn rising **interior rail** near y400. Thus:
- Horizontal structure: a prior local price high may have been exceeded.
- Sloped structure: a former rising internal support rail may still lie above price and act as potential supply.

Neither is automatically the “correct” buy/sell interpretation. Require the **completed** bar close, persistence, new retest response, number of tested touches, timeframe, volume, and alternative anchor provenance. Do not promote the original line or horizontal baseline to a buy signal on this image.

## Information-set audit: what was available before July?
A–B **could potentially** be established after the B trough and confirmation, well before the C trough; however exact dates and confirmation delay are NOT VERIFIED. A–C **cannot** have been specified until the C pivot became visible and mature enough to classify; B–C likewise. The bottom channel rail's deep early-August touch cannot be used to choose the channel width **before** that low unless an older independent anchor specifies the width. The single September screenshot does not reveal any historical drawing versions. This distinction is **the central falsification issue**, beyond simple slope fit.

## Explicit rival models and future reproducibility gate
1. **Model P (pre-existing channel)**: chart artist selected A/B early, froze slope and upper/lower offsets using available *pre-July* swings. An archived pre-August screen must show identical lines to claim August predictive success.
2. **Model R (retrospective fit)**: A/C or alternate slope chosen after July and channel rail offset selected after the early-August low. The line matches price precisely but offers no prior forecast.
3. **Model H (horizontal swing / box)**: ignore diagonal; identify repeated close/turn/rejection around earlier swing highs and the prior accepted box area, and treat Sep progression as a potential local resistance break with no guaranteed continuation.
4. **Model N (no line)**: use candles/participation/time and risk alone; prevents every outcome being made to fit a nearby slope.

**Next proper test:** verify exact ticker, venue, local 2h candle OHLC and linear/log axis; use a historical cutoff before C, select wick/body/close pivot conventions with explicit tolerance and draw **P/H/N** without viewing August/September; freeze coordinates and direction hypotheses; withhold/reveal later bars, count retests, breakdown, reclaim, nonfills, realized risk and costs, and compare redraw frequency. Only then consider modifying any price-level rule. A single already annotated chart cannot establish hit rate or independently judged profitability.

**Evidence statement:** The *actual screenshot* is directly inspected; the **screen geometry and sensitivity** are reproducibly calculated with the approximate stated coordinates. Exact image-to-bar mapping, true artist-selected pivots, pre-event intent, outcome and economic expectancy remain NOT VERIFIED. Current SRC-STUDY-001 open. Library-root census stays **1,642 = 1,333 classified + 57 inaccessible + 252 unattempted**. Curated 91 originals directly opened 21, independently mastered 0. No scan, S02 D04, orders or production edits.
