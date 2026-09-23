# Long-term MA600 Swing Scanner

## Purpose
This scanner replaces manual HTS condition-search/chart-sweep work. It is intentionally **price/turnover/structure-first** and does not attempt to discover news or catalysts.

## Core interpretation
The primary setup is not "MA600 is magic." It is:
1. long decline/base or long congestion,
2. capital/turnover expansion,
3. structural breakout centered on MA600 and nearby supply zones,
4. close/acceptance above the breakout,
5. pullback with weaker supply,
6. reacceleration.

MA240/MA1000/MA1200 and the prior 120-session high are secondary evidence.

## Output
`longterm-scan.json` contains:
- `BREAKOUT_600_STRONG`
- `BREAKOUT_600`
- `NEAR_BREAKOUT_600`
- `ACCEPTANCE_600`
- `REACCELERATION`
- `FAILED_BREAKOUT_600`

An A/B/C/WATCH grade is a **chart/flow discovery grade**, not an automatic buy signal.

## Turnover logic
Do not use a rigid "KRW 100bn = real breakout" rule.
The scanner combines:
- absolute trading value,
- current vs estimated 20-session average trading value,
- volume expansion,
- close location,
- bullish body size,
- market-cap-normalized turnover when available.

The current session's KRX `Amount` is used when available. Historical 20-session turnover comparison is estimated as typical price × volume and is explicitly labeled estimated.

## Schedule
GitHub Actions runs on weekdays after the Korean close. Stale/holiday data is detected and is not committed.

## Downstream use
The intended pipeline is:
`after-close scan -> next 08:15 candidate selection -> watchlist.json -> Cloudflare/live bridge -> 09:35/09:40 minute-path validation`.

Candidates from this scanner must compete with other valid candidates; they are not automatically promoted into the attack plan.
