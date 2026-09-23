#!/usr/bin/env python3
"""Daily KRX long-term chart/flow scanner.

Purpose: replace manual HTS condition-search/chart-sweep work.
Primary setup: MA600 structural breakout + strong bullish candle + capital-flow expansion.
News/catalyst is intentionally NOT used.

Price history: FinanceDataReader/Naver (long history; adjusted-price behavior follows FDR).
Current daily turnover/market cap: KRX listing via FinanceDataReader.
"""

from __future__ import annotations
import argparse, concurrent.futures as cf, datetime as dt, json, math, re, urllib.parse, urllib.request
from collections import Counter
from pathlib import Path

import FinanceDataReader as fdr
import pandas as pd

KST = dt.timezone(dt.timedelta(hours=9))


def rnum(x, n=2):
    if x is None or pd.isna(x) or not math.isfinite(float(x)):
        return None
    return round(float(x), n)


def pct(a, b):
    if b is None or pd.isna(b) or float(b) == 0:
        return None
    return (float(a) / float(b) - 1.0) * 100.0


def sma(s: pd.Series, n: int):
    return s.rolling(n, min_periods=n).mean()


def parse_int_text(v):
    if v is None:
        return 0
    s = str(v).replace(",", "").replace("+", "").strip()
    if s in ("", "-", "N/A", "None"):
        return 0
    try:
        return int(float(s))
    except Exception:
        return 0


def fetch_investor_flow(code: str, limit: int = 20):
    """Public Naver investor trend. Used only to enrich chart candidates."""
    qs = urllib.parse.urlencode({"code": code})
    url = f"https://m.stock.naver.com/front-api/stock/domestic/trend?{qs}"
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 longterm-scan/1.0",
            "Referer": f"https://m.stock.naver.com/domestic/stock/{code}/total",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    rows = payload.get("dealTrendInfos", payload) if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        return {"status": "BAD_SCHEMA", "rows": 0}
    rows = rows[:limit]
    norm = []
    for x in rows:
        if not isinstance(x, dict):
            continue
        f = parse_int_text(x.get("foreignerPureBuyQuant"))
        o = parse_int_text(x.get("organPureBuyQuant"))
        ind = parse_int_text(x.get("individualPureBuyQuant"))
        vol = parse_int_text(x.get("accumulatedTradingVolume"))
        norm.append({
            "bizdate": str(x.get("bizdate", "")),
            "foreign": f, "institution": o, "individual": ind, "volume": vol,
            "foreignHoldRatio": x.get("foreignerHoldRatio"),
        })
    def agg(n):
        rr = norm[:n]
        fv = sum(x["foreign"] for x in rr)
        ov = sum(x["institution"] for x in rr)
        vv = sum(x["volume"] for x in rr)
        return {
            "foreignNetShares": fv,
            "institutionNetShares": ov,
            "combinedNetShares": fv + ov,
            "netParticipationPct": rnum((fv + ov) / vv * 100.0) if vv else None,
        }
    return {
        "status": "OK",
        "source": "NAVER_PUBLIC_INVESTOR_TREND",
        "latestBizdate": norm[0]["bizdate"] if norm else None,
        "foreignHoldRatio": norm[0]["foreignHoldRatio"] if norm else None,
        "rows": len(norm),
        "d1": agg(1),
        "d5": agg(min(5, len(norm))),
        "d20": agg(min(20, len(norm))),
    }


def current_listing():
    # Prefer direct KRX same-day listing; fall back to FDR cache if KRX blocks the request.
    try:
        from FinanceDataReader.krx.listing import KrxMarcapListing
        df = KrxMarcapListing("KRX").read().copy()
    except Exception:
        df = fdr.StockListing("KRX").copy()
    code_col = "Code" if "Code" in df.columns else "Symbol"
    df[code_col] = df[code_col].astype(str).str.zfill(6)
    df = df[df[code_col].str.fullmatch(r"\d{6}")].copy()
    if "Market" in df.columns:
        df = df[df["Market"].isin(["KOSPI", "KOSDAQ"])]
    if "Name" in df.columns:
        df = df[~df["Name"].astype(str).str.contains(r"스팩|SPAC", case=False, regex=True, na=False)]
    out = []
    for _, x in df.iterrows():
        out.append({
            "code": x[code_col],
            "name": str(x.get("Name", x[code_col])),
            "market": str(x.get("Market", "")),
            "amount": float(x["Amount"]) if "Amount" in df.columns and pd.notna(x.get("Amount")) else None,
            "marcap": float(x["Marcap"]) if "Marcap" in df.columns and pd.notna(x.get("Marcap")) else None,
        })
    return out


def latest_cross(close: pd.Series, ma: pd.Series, lookback: int):
    start = max(1, len(close) - lookback)
    for i in range(len(close) - 1, start - 1, -1):
        if pd.notna(ma.iloc[i]) and pd.notna(ma.iloc[i-1]):
            if close.iloc[i-1] <= ma.iloc[i-1] and close.iloc[i] > ma.iloc[i]:
                return i
    return None


def analyze(meta, cfg):
    code = meta["code"]
    start = (dt.date.today() - dt.timedelta(days=int(cfg["historyCalendarDays"]))).isoformat()
    df = fdr.DataReader(code, start)
    if df is None or len(df) < 601:
        return {"status": "INSUFFICIENT_HISTORY", **meta, "rows": 0 if df is None else len(df)}
    need = ["Open", "High", "Low", "Close", "Volume"]
    if any(c not in df.columns for c in need):
        return {"status": "BAD_SCHEMA", **meta, "columns": list(df.columns)}
    df = df[need].dropna().copy()
    if len(df) < 601:
        return {"status": "INSUFFICIENT_HISTORY", **meta, "rows": len(df)}

    periods = [int(x) for x in cfg["maPeriods"]]
    for p in periods:
        df[f"MA{p}"] = sma(df["Close"], p)

    cur, prev = df.iloc[-1], df.iloc[-2]
    ma600, pma600 = cur["MA600"], prev["MA600"]
    if pd.isna(ma600) or pd.isna(pma600):
        return {"status": "INSUFFICIENT_HISTORY", **meta, "rows": len(df)}

    typical = (df["Open"] + df["High"] + df["Low"] + df["Close"]) / 4.0
    tv_est = typical * df["Volume"]
    avg20_tv = tv_est.iloc[-21:-1].mean() if len(df) >= 21 else tv_est.iloc[:-1].mean()
    cur_tv = meta.get("amount") if meta.get("amount") and meta["amount"] > 0 else float(tv_est.iloc[-1])
    tv_quality = "KRX_EXACT_CURRENT__HIST20_ESTIMATED" if meta.get("amount") else "ESTIMATED"
    tv_ratio = cur_tv / avg20_tv if avg20_tv and avg20_tv > 0 else None

    avg20_vol = df["Volume"].iloc[-21:-1].mean() if len(df) >= 21 else df["Volume"].iloc[:-1].mean()
    vol_ratio = float(cur["Volume"]) / avg20_vol if avg20_vol and avg20_vol > 0 else None
    body_pct = pct(cur["Close"], cur["Open"])
    chg_pct = pct(cur["Close"], prev["Close"])
    rng = float(cur["High"] - cur["Low"])
    close_loc = float((cur["Close"] - cur["Low"]) / rng) if rng > 0 else 0.5

    cross600 = bool(prev["Close"] <= pma600 and cur["Close"] > ma600)
    dist600 = pct(cur["Close"], ma600)
    near600 = bool((not cross600) and cur["Close"] <= ma600 and dist600 is not None and abs(dist600) <= float(cfg["nearMa600Pct"]))
    failed600 = bool(cur["High"] > ma600 and cur["Close"] <= ma600 and (tv_ratio or 0) >= float(cfg["minTurnoverRatio20"]))

    high120 = float(df["High"].iloc[-121:-1].max()) if len(df) >= 121 else None
    box120 = bool(high120 and cur["Close"] > high120)

    cross_idx = latest_cross(df["Close"], df["MA600"], int(cfg["acceptanceLookbackSessions"]))
    days_since = None if cross_idx is None else len(df) - 1 - cross_idx
    acceptance = False
    if cross_idx is not None and days_since is not None and days_since >= 1:
        tol = float(cfg["acceptanceUnderMaTolerancePct"]) / 100.0
        acceptance = True
        for j in range(cross_idx + 1, len(df)):
            if pd.notna(df["MA600"].iloc[j]) and df["Close"].iloc[j] < df["MA600"].iloc[j] * (1 - tol):
                acceptance = False
                break
        acceptance = acceptance and cur["Close"] > ma600

    reaccel = False
    if acceptance and days_since is not None and 2 <= days_since <= int(cfg["acceptanceLookbackSessions"]):
        left = max(cross_idx, len(df) - 11)
        prev_high = df["High"].iloc[left:-1].max()
        reaccel = bool(cur["Close"] > prev_high and (tv_ratio or 0) >= float(cfg["reaccelerationTurnoverRatio20"]))

    lb = min(len(df) - 1, int(cfg["corporateActionGuardLookback"]))
    moves = df["Close"].pct_change().iloc[-lb:].abs()
    jump_mask = moves > float(cfg["corporateActionJumpPct"]) / 100.0
    anomaly = list(moves[jump_mask].index.strftime("%Y%m%d"))

    strong = bool(
        cross600
        and (body_pct or -999) >= float(cfg["strongBodyPct"])
        and (tv_ratio or 0) >= float(cfg["strongTurnoverRatio20"])
        and close_loc >= float(cfg["strongCloseLocation"])
        and cur_tv >= float(cfg["minTurnoverWatchKrw"])
        and not anomaly
    )

    if reaccel:
        signal = "REACCELERATION"
    elif strong:
        signal = "BREAKOUT_600_STRONG"
    elif cross600:
        signal = "BREAKOUT_600"
    elif failed600:
        signal = "FAILED_BREAKOUT_600"
    elif acceptance:
        signal = "ACCEPTANCE_600"
    elif near600:
        signal = "NEAR_BREAKOUT_600"
    else:
        signal = "NONE"

    if strong: grade = "A"
    elif cross600 and cur_tv >= float(cfg["minTurnoverWatchKrw"]) and (tv_ratio or 0) >= float(cfg["minTurnoverRatio20"]): grade = "B"
    elif cross600: grade = "C"
    elif near600: grade = "WATCH"
    else: grade = "NONE"

    score = 0
    score += 35 if cross600 else 0
    score += 18 if (tv_ratio or 0) >= float(cfg["strongTurnoverRatio20"]) else (8 if (tv_ratio or 0) >= float(cfg["minTurnoverRatio20"]) else 0)
    score += 10 if cur_tv >= float(cfg["strongTurnoverKrw"]) else (5 if cur_tv >= float(cfg["minTurnoverWatchKrw"]) else 0)
    score += 10 if (body_pct or -999) >= float(cfg["strongBodyPct"]) else 0
    score += 8 if close_loc >= float(cfg["strongCloseLocation"]) else 0
    score += 7 if box120 else 0
    score += 5 if (vol_ratio or 0) >= float(cfg["volumeRatio20"]) else 0
    score += 5 if pd.notna(cur.get("MA240")) and cur["Close"] > cur["MA240"] else 0
    score += 8 if acceptance else 0
    score += 10 if reaccel else 0
    score -= 50 if anomaly else 0

    mas, dists = {}, {}
    for p in periods:
        v = cur.get(f"MA{p}")
        mas[str(p)] = rnum(v, 2)
        dists[str(p)] = rnum(pct(cur["Close"], v), 2) if pd.notna(v) else None

    return {
        "status": "OK", "code": code, "name": meta["name"], "market": meta["market"],
        "tradeDate": df.index[-1].strftime("%Y%m%d"), "signal": signal, "grade": grade, "score": score,
        "close": rnum(cur["Close"], 0), "open": rnum(cur["Open"], 0), "high": rnum(cur["High"], 0), "low": rnum(cur["Low"], 0),
        "dayChangePct": rnum(chg_pct), "bodyPct": rnum(body_pct), "closeLocation": rnum(close_loc, 3),
        "ma": mas, "distanceToMaPct": dists, "cross600": cross600, "near600": near600,
        "box120Breakout": box120, "high120Prev": rnum(high120, 2),
        "tradingValue": rnum(cur_tv, 0), "avg20TradingValueEstimated": rnum(avg20_tv, 0),
        "tradingValueRatio20Estimated": rnum(tv_ratio), "tradingValueQuality": tv_quality,
        "volume": rnum(cur["Volume"], 0), "avg20Volume": rnum(avg20_vol, 0), "volumeRatio20": rnum(vol_ratio),
        "marketCap": rnum(meta.get("marcap"), 0), "turnoverToMarketCapPct": rnum(cur_tv/meta["marcap"]*100) if meta.get("marcap") else None,
        "daysSinceCross600": days_since, "acceptance600": acceptance, "reacceleration": reaccel,
        "rows": len(df), "dataWarnings": [f"PRICE_JUMP>{cfg['corporateActionJumpPct']}%:{','.join(anomaly[-3:])}"] if anomaly else []
    }


def sortit(xs):
    return sorted(xs, key=lambda x: (x.get("score",0), x.get("tradingValueRatio20Estimated") or 0, x.get("tradingValue") or 0), reverse=True)


def run(cfg):
    uni = current_listing()
    if len(uni) < int(cfg["minUniverseCount"]):
        return {"status":"FAIL_UNIVERSE","generatedAtKst":dt.datetime.now(KST).isoformat(),"universeCount":len(uni)}

    results, errors = [], []
    with cf.ThreadPoolExecutor(max_workers=int(cfg["maxWorkers"])) as ex:
        fm = {ex.submit(analyze, m, cfg):m for m in uni}
        for fut in cf.as_completed(fm):
            m = fm[fut]
            try: results.append(fut.result())
            except Exception as e: errors.append({"code":m["code"],"name":m["name"],"error":f"{type(e).__name__}: {e}"})

    ok = [x for x in results if x.get("status")=="OK"]
    insufficient = [x for x in results if x.get("status")=="INSUFFICIENT_HISTORY"]
    dates = Counter(x.get("tradeDate") for x in ok if x.get("tradeDate"))
    td = dates.most_common(1)[0][0] if dates else None
    cur = [x for x in ok if x.get("tradeDate")==td]
    strong = sortit([x for x in cur if x["signal"]=="BREAKOUT_600_STRONG"])
    breaks = sortit([x for x in cur if x["signal"] in ("BREAKOUT_600_STRONG","BREAKOUT_600")])
    near = sortit([x for x in cur if x["signal"]=="NEAR_BREAKOUT_600"])
    acc = sortit([x for x in cur if x["signal"] in ("ACCEPTANCE_600","REACCELERATION")])
    failed = sortit([x for x in cur if x["signal"]=="FAILED_BREAKOUT_600"])
    allc = sortit([x for x in cur if x["signal"]!="NONE"])

    # Enrich only the highest-ranked chart/flow candidates with foreign/institution flow.
    # This avoids turning the scanner into thousands of extra investor-trend requests.
    flow_n = min(int(cfg.get("flowEnrichTopN", 60)), len(allc))
    flow_errors = []
    if flow_n > 0:
        with cf.ThreadPoolExecutor(max_workers=min(8, int(cfg["maxWorkers"]))) as ex:
            fm2 = {ex.submit(fetch_investor_flow, x["code"], int(cfg.get("flowLookbackSessions", 20))): x for x in allc[:flow_n]}
            for fut in cf.as_completed(fm2):
                x = fm2[fut]
                try:
                    x["investorFlow"] = fut.result()
                except Exception as e:
                    x["investorFlow"] = {"status": "ERROR", "error": f"{type(e).__name__}: {e}"}
                    flow_errors.append({"code": x["code"], "error": f"{type(e).__name__}: {e}"})

    er = len(errors)/max(1,len(uni)); sr = (len(ok)-len(cur))/max(1,len(ok))
    status = "PASS" if er <= float(cfg["maxErrorRatioForPass"]) and sr <= float(cfg["maxStaleRatioForPass"]) else "PARTIAL"
    lim = int(cfg["maxPerBucket"])
    return {
        "status":status, "generatedAtKst":dt.datetime.now(KST).isoformat(), "tradeDate":td,
        "methodologyVersion":cfg["methodologyVersion"],
        "primaryLogic":"MA600 structural breakout + turnover expansion + bullish close quality",
        "notes":[
            "News/catalyst is intentionally excluded.",
            "MA600 is primary; MA240/1000/1200 and 120-session box are secondary evidence.",
            "A-grade is a chart/flow candidate, not a buy signal.",
            "Current trading value is exact KRX Amount when available; 20-session comparison is estimated from typical price x volume."
        ],
        "thresholds":{k:cfg[k] for k in ["nearMa600Pct","strongBodyPct","strongTurnoverRatio20","minTurnoverRatio20","strongCloseLocation","minTurnoverWatchKrw","strongTurnoverKrw","volumeRatio20","acceptanceLookbackSessions"]},
        "coverage":{"universe":len(uni),"ok":len(ok),"currentTradeDate":len(cur),"insufficientHistory":len(insufficient),"fetchErrors":len(errors),"staleRows":len(ok)-len(cur),"errorRatio":round(er,4),"staleRatio":round(sr,4),"tradeDateCounts":dict(dates.most_common(5)),"flowEnriched":flow_n,"flowErrors":len(flow_errors)},
        "counts":{"strongBreakouts":len(strong),"allBreakouts":len(breaks),"nearBreakouts":len(near),"acceptanceOrReacceleration":len(acc),"failedBreakouts":len(failed),"allCandidates":len(allc)},
        "strongBreakouts":strong[:lim],"breakouts":breaks[:lim],"nearBreakouts":near[:lim],"acceptance":acc[:lim],"failedBreakouts":failed[:lim],
        "allCandidates":allc[:int(cfg["maxAllCandidates"])],"sampleErrors":errors[:30],"sampleFlowErrors":flow_errors[:20]
    }


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--config",default="longterm-scan-config.json"); ap.add_argument("--output",default="longterm-scan.json"); a=ap.parse_args()
    cfg=json.loads(Path(a.config).read_text(encoding="utf-8")); out=run(cfg)
    tmp=Path(a.output+".tmp"); tmp.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8"); tmp.replace(a.output)
    print(json.dumps({"status":out.get("status"),"tradeDate":out.get("tradeDate"),"coverage":out.get("coverage"),"counts":out.get("counts")},ensure_ascii=False,indent=2))
    return 0 if out.get("status") in ("PASS","PARTIAL") else 2

if __name__=="__main__": raise SystemExit(main())
