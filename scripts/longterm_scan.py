#!/usr/bin/env python3
"""Daily KRX structural chart/flow scanner - YBM Swing V2.

Observable-only implementation:
long decline/base -> long-MA recovery -> money-backed reference candle ->
supply/resistance digestion -> real/weak breakout -> retest/reacceleration.

No hidden operator/accumulation intent is inferred.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime as dt
import json
import math
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

import FinanceDataReader as fdr
import numpy as np
import pandas as pd

KST = dt.timezone(dt.timedelta(hours=9))


def json_default(obj):
    if isinstance(obj, np.generic):
        return obj.item()
    if isinstance(obj, (pd.Timestamp, dt.datetime, dt.date)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def rnum(x, n=2):
    if x is None or pd.isna(x):
        return None
    try:
        x = float(x)
    except Exception:
        return None
    return round(x, n) if math.isfinite(x) else None


def pct(a, b):
    if a is None or b is None or pd.isna(a) or pd.isna(b) or float(b) == 0:
        return None
    return (float(a) / float(b) - 1.0) * 100.0


def sma(s, n):
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


def fetch_investor_flow(code, limit=20):
    qs = urllib.parse.urlencode({"code": code})
    url = f"https://m.stock.naver.com/front-api/stock/domestic/trend?{qs}"
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 longterm-scan/2.0",
            "Referer": f"https://m.stock.naver.com/domestic/stock/{code}/total",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    rows = payload.get("dealTrendInfos", payload) if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        return {"status": "BAD_SCHEMA", "rows": 0}
    norm = []
    for x in rows[:limit]:
        if not isinstance(x, dict):
            continue
        foreign = parse_int_text(x.get("foreignerPureBuyQuant"))
        inst = parse_int_text(x.get("organPureBuyQuant"))
        indiv = parse_int_text(x.get("individualPureBuyQuant"))
        vol = parse_int_text(x.get("accumulatedTradingVolume"))
        norm.append({
            "bizdate": str(x.get("bizdate", "")),
            "foreign": foreign,
            "institution": inst,
            "individual": indiv,
            "volume": vol,
            "foreignHoldRatio": x.get("foreignerHoldRatio"),
        })

    def agg(n):
        rr = norm[:n]
        fv = sum(x["foreign"] for x in rr)
        iv = sum(x["institution"] for x in rr)
        vv = sum(x["volume"] for x in rr)
        return {
            "foreignNetShares": fv,
            "institutionNetShares": iv,
            "combinedNetShares": fv + iv,
            "netParticipationPct": rnum((fv + iv) / vv * 100.0) if vv else None,
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


def add_indicators(df, cfg):
    df = df.copy()
    for p in [int(x) for x in cfg["maPeriods"]]:
        df[f"MA{p}"] = sma(df["Close"], p)

    high9 = df["High"].rolling(9, min_periods=9).max()
    low9 = df["Low"].rolling(9, min_periods=9).min()
    high26 = df["High"].rolling(26, min_periods=26).max()
    low26 = df["Low"].rolling(26, min_periods=26).min()
    high52 = df["High"].rolling(52, min_periods=52).max()
    low52 = df["Low"].rolling(52, min_periods=52).min()
    tenkan = (high9 + low9) / 2.0
    kijun = (high26 + low26) / 2.0
    df["CLOUD_A"] = ((tenkan + kijun) / 2.0).shift(26)
    df["CLOUD_B"] = ((high52 + low52) / 2.0).shift(26)

    typical = (df["Open"] + df["High"] + df["Low"] + df["Close"]) / 4.0
    df["TV_EST"] = typical * df["Volume"]
    df["AVG20_TV_EST"] = df["TV_EST"].shift(1).rolling(20, min_periods=10).mean()
    df["TV_RATIO20_EST"] = df["TV_EST"] / df["AVG20_TV_EST"]
    df["AVG20_VOL"] = df["Volume"].shift(1).rolling(20, min_periods=10).mean()
    df["VOL_RATIO20"] = df["Volume"] / df["AVG20_VOL"]
    df["DAY_RETURN_PCT"] = df["Close"].pct_change() * 100.0
    df["BODY_PCT"] = (df["Close"] / df["Open"] - 1.0) * 100.0
    rng = (df["High"] - df["Low"]).replace(0, np.nan)
    df["CLOSE_LOC"] = ((df["Close"] - df["Low"]) / rng).fillna(0.5)
    return df


def cloud_snapshot(row):
    a, b = row.get("CLOUD_A"), row.get("CLOUD_B")
    if pd.isna(a) or pd.isna(b):
        return {"top": None, "bottom": None, "state": "UNAVAILABLE"}
    top, bot = max(float(a), float(b)), min(float(a), float(b))
    close = float(row["Close"])
    state = "ABOVE" if close > top else ("BELOW" if close < bot else "INSIDE")
    return {"top": rnum(top, 2), "bottom": rnum(bot, 2), "state": state}


def rolling_event_mask(df, cfg):
    """Historical observable proxy for a money-backed large bullish reference candle."""
    return (
        (df["Close"] > df["Open"])
        & (df["DAY_RETURN_PCT"] >= float(cfg["deoyangbongMinReturnPct"]))
        & (df["TV_EST"] >= float(cfg["deoyangbongMinTradingValueKrw"]))
        & (df["VOL_RATIO20"] >= float(cfg["deoyangbongMinVolumeRatio20"]))
        & (df["CLOSE_LOC"] >= float(cfg["deoyangbongMinCloseLocation"]))
    ).fillna(False)


def event_info(df, idx):
    x = df.iloc[idx]
    return {
        "date": df.index[idx].strftime("%Y%m%d"),
        "open": rnum(x["Open"], 0),
        "close": rnum(x["Close"], 0),
        "high": rnum(x["High"], 0),
        "low": rnum(x["Low"], 0),
        "dayReturnPct": rnum(x["DAY_RETURN_PCT"]),
        "tradingValueEstimated": rnum(x["TV_EST"], 0),
        "volumeRatio20": rnum(x["VOL_RATIO20"]),
        "closeLocation": rnum(x["CLOSE_LOC"], 3),
    }


def latest_event_position(mask, max_lookback, exclude_last=True):
    end = len(mask) - (1 if exclude_last else 0)
    start = max(0, end - max_lookback)
    vals = np.where(mask.iloc[start:end].values)[0]
    return None if len(vals) == 0 else start + int(vals[-1])


def ma_slope_pct(series, lookback):
    if len(series) <= lookback or pd.isna(series.iloc[-1]) or pd.isna(series.iloc[-1-lookback]):
        return None
    return pct(series.iloc[-1], series.iloc[-1-lookback])


def abc_features(df, cfg):
    """ABC heuristic anchored to the base that existed BEFORE a recent MA600 recovery.

    This avoids a common false negative in mature C-stage charts: once price has already
    advanced strongly, the current last-120-session range no longer resembles the old B base.
    """
    n = len(df)
    if n < int(cfg["minLongHistoryRows"]) or pd.isna(df.iloc[-1].get("MA600")):
        return {
            "track": "NEW_LISTING",
            "state": "NOT_APPLICABLE_LONG_MA",
            "score": 0,
            "aDeclinePct": None,
            "bRangePct": None,
            "ma600Slope60Pct": None,
            "cActive": False,
            "cross600Today": False,
            "bPlus": False,
            "cStartDate": None,
        }

    cur = df.iloc[-1]
    c_active = bool(pd.notna(cur["MA600"]) and cur["Close"] > cur["MA600"])
    cross_flags = (
        (df["Close"].shift(1) <= df["MA600"].shift(1))
        & (df["Close"] > df["MA600"])
    ).fillna(False)
    search_start = max(1, n - int(cfg["abcCSearchLookbackSessions"]))
    cross_pos = np.where(cross_flags.iloc[search_start:].values)[0]
    c_pos = (search_start + int(cross_pos[-1])) if len(cross_pos) else None

    # If C has started, inspect the base immediately before that recovery.
    # Otherwise inspect the current pre-session base.
    base_end = c_pos if c_pos is not None else n - 1
    base_choices = []
    for w in [int(x) for x in cfg.get("abcBaseWindowCandidates", [cfg["abcBaseLookbackSessions"]])]:
        if base_end >= w:
            seg = df.iloc[base_end-w:base_end]
            if len(seg) >= 20:
                lo, hi = float(seg["Low"].min()), float(seg["High"].max())
                rr = (hi / lo - 1.0) * 100.0 if lo > 0 else None
                if rr is not None:
                    base_choices.append((w, rr))
    acceptable = [x for x in base_choices if x[1] <= float(cfg["abcBaseMaxRangePct"])]
    if acceptable:
        b_window, b_range = sorted(acceptable, key=lambda x: x[0], reverse=True)[0]
    elif base_choices:
        b_window, b_range = sorted(base_choices, key=lambda x: x[1])[0]
    else:
        b_window, b_range = None, None
    base_start = max(0, base_end - (b_window or int(cfg["abcBaseLookbackSessions"])))

    slope_ref = c_pos if c_pos is not None else n - 1
    slope_lb = int(cfg["abcMaSlopeLookbackSessions"])
    slope600 = None
    if slope_ref - slope_lb >= 0:
        v1, v0 = df["MA600"].iloc[slope_ref], df["MA600"].iloc[slope_ref-slope_lb]
        if pd.notna(v1) and pd.notna(v0):
            slope600 = pct(v1, v0)

    # A is measured over the long window ending at C-start/current base end, allowing
    # the trough to occur inside the B base after the long decline.
    a_end = max(base_end, 1)
    a_start = max(0, a_end - int(cfg["abcAWindowSessions"]))
    ahist = df.iloc[a_start:a_end]
    a_decline = None
    if len(ahist) >= 120:
        peak_i = int(np.argmax(ahist["High"].values))
        peak = float(ahist["High"].iloc[peak_i])
        after = ahist.iloc[peak_i:]
        trough = float(after["Low"].min()) if len(after) else peak
        a_decline = (peak - trough) / peak * 100.0 if peak > 0 else None

    a_ok = bool(a_decline is not None and a_decline >= float(cfg["abcMinDeclinePct"]))
    b_ok = bool(
        b_range is not None
        and b_range <= float(cfg["abcBaseMaxRangePct"])
        and slope600 is not None
        and abs(slope600) <= float(cfg["abcMa600MaxAbsSlopePct"])
    )

    # B+ proxy: meaningful money/volume arrived around the C transition, not merely
    # sometime in the distant recent window.
    b_plus = False
    if c_pos is not None:
        w0, w1 = max(0, c_pos - 5), min(n, c_pos + 11)
        around = df.iloc[w0:w1]
        b_plus = bool(
            b_ok
            and ((around["TV_EST"] >= float(cfg["deoyangbongMinTradingValueKrw"]))
                 & (around["VOL_RATIO20"] >= float(cfg["bPlusMinVolumeRatio20"]))).fillna(False).any()
        )

    score = (30 if a_ok else 0) + (30 if b_ok else 0) + (30 if c_active else 0) + (10 if b_plus else 0)
    if a_ok and b_ok and c_active:
        state = "C_ACTIVE"
    elif a_ok and b_ok:
        state = "B_BASE"
    elif a_ok and c_active:
        state = "C_RECOVERY_NONCLASSIC_BASE"
    elif a_ok:
        state = "A_TO_B"
    elif c_active:
        state = "LONG_MA_RECOVERY_NONCLASSIC"
    else:
        state = "NONE"

    return {
        "track": "LONG_HISTORY",
        "state": state,
        "score": int(score),
        "aDeclinePct": rnum(a_decline),
        "bRangePct": rnum(b_range),
        "bWindowSessions": int(b_window) if b_window is not None else None,
        "ma600Slope60Pct": rnum(slope600),
        "cActive": bool(c_active),
        "cross600Today": bool(c_pos == n - 1),
        "bPlus": bool(b_plus),
        "cStartDate": df.index[c_pos].strftime("%Y%m%d") if c_pos is not None else None,
    }

def round_levels(price):
    if price <= 0:
        return []
    digits = int(math.floor(math.log10(price))) + 1
    base = 10 ** max(0, digits - 2)
    steps = sorted(set([base, 5 * base, 10 * base]))
    vals = set()
    for step in steps:
        k = math.floor(price / step)
        for j in range(max(1, k - 2), k + 5):
            vals.add(float(j * step))
    return sorted(v for v in vals if v > 0)


def cluster_levels(levels, tolerance_pct):
    xs = sorted([x for x in levels if x[0] and x[0] > 0], key=lambda z: z[0])
    groups = []
    for p, w, source in xs:
        if not groups:
            groups.append({"items": [(p, w, source)]})
            continue
        g = groups[-1]
        sw = sum(b for _, b, _ in g["items"])
        center = sum(a*b for a, b, _ in g["items"]) / max(1e-9, sw)
        if abs(p / center - 1.0) * 100.0 <= tolerance_pct:
            g["items"].append((p, w, source))
        else:
            groups.append({"items": [(p, w, source)]})

    out = []
    for g in groups:
        items = g["items"]
        sw = sum(w for _, w, _ in items)
        center = sum(p*w for p, w, _ in items) / sw
        out.append({
            "line": center,
            "low": min(p for p, _, _ in items),
            "high": max(p for p, _, _ in items),
            "weight": sw,
            "sourceCount": len(set(s for _, _, s in items)),
            "sources": sorted(set(s for _, _, s in items)),
        })
    return out


def build_core_resistance(hist, reference_price, cfg):
    """Build resistance only from pre-current data to prevent look-ahead leakage."""
    if len(hist) < 30 or reference_price <= 0:
        return None

    lo_bound = reference_price * (1 - float(cfg["coreLineBelowReferenceTolerancePct"]) / 100.0)
    hi_bound = reference_price * (1 + float(cfg["coreLineMaxDistancePct"]) / 100.0)
    levels = []

    mask = rolling_event_mask(hist, cfg)
    event_positions = np.where(mask.values)[0][-int(cfg["coreEventLookbackCount"]):]
    for i in event_positions:
        row = hist.iloc[i]
        for field, weight in (("Open", 3.0), ("Close", 4.0), ("High", 2.0)):
            p = float(row[field])
            if lo_bound <= p <= hi_bound:
                levels.append((p, weight, f"DEOYANGBONG_{field.upper()}"))

    sw = int(cfg["swingHalfWindow"])
    start = max(sw, len(hist) - int(cfg["coreSwingLookbackSessions"]))
    for i in range(start, len(hist) - sw):
        h = float(hist["High"].iloc[i])
        if h >= float(hist["High"].iloc[i-sw:i+sw+1].max()) and lo_bound <= h <= hi_bound:
            levels.append((h, 2.0, "SWING_HIGH"))

    vp = hist.iloc[-min(len(hist), int(cfg["coreDensityLookbackSessions"])):].copy()
    vp = vp[(vp["Close"] >= lo_bound * 0.95) & (vp["Close"] <= hi_bound * 1.02)]
    if len(vp) >= 20:
        pmin, pmax = float(vp["Low"].min()), float(vp["High"].max())
        if pmax > pmin:
            bins = int(cfg["coreDensityBins"])
            edges = np.linspace(pmin, pmax, bins + 1)
            inds = np.digitize(vp["Close"].values, edges) - 1
            vols = []
            for bi in range(bins):
                vv = float(vp.loc[inds == bi, "Volume"].sum()) if np.any(inds == bi) else 0.0
                vols.append((vv, (edges[bi] + edges[bi+1]) / 2.0))
            for _, center in sorted(vols, reverse=True)[:int(cfg["coreDensityTopBins"])]:
                if lo_bound <= center <= hi_bound:
                    levels.append((float(center), 2.0, "CANDLE_DENSITY"))

    for p in round_levels(reference_price):
        if lo_bound <= p <= hi_bound:
            levels.append((p, 1.0, "ROUND_FIGURE"))

    last = hist.iloc[-1]
    for field, label, weight in (
        ("CLOUD_A", "CLOUD_EDGE", 1.5),
        ("CLOUD_B", "CLOUD_EDGE", 1.5),
        ("MA240", "MA240", 0.8),
        ("MA480", "MA480", 1.0),
        ("MA600", "MA600", 1.3),
        ("MA1000", "MA1000", 1.3),
    ):
        if field in hist.columns and pd.notna(last.get(field)):
            p = float(last[field])
            if lo_bound <= p <= hi_bound:
                levels.append((p, weight, label))

    clusters = cluster_levels(levels, float(cfg["coreClusterTolerancePct"]))
    if not clusters:
        return None

    touch_hist = hist.iloc[-min(len(hist), int(cfg["coreTouchLookbackSessions"])):]
    tol = float(cfg["coreTouchTolerancePct"]) / 100.0
    for c in clusters:
        line = c["line"]
        touches = int(((touch_hist["High"] >= line*(1-tol)) & (touch_hist["Low"] <= line*(1+tol))).sum())
        c["touches"] = touches
        c["score"] = c["weight"] + min(touches, 6) * 0.6 + c["sourceCount"] * 0.5
        c["distancePct"] = pct(line, reference_price)

    candidates = [c for c in clusters if lo_bound <= c["line"] <= hi_bound]
    if not candidates:
        return None
    candidates.sort(key=lambda c: (c["score"], -abs(c["distancePct"] or 999)), reverse=True)
    best = candidates[0]
    pad = float(cfg["coreZonePaddingPct"]) / 100.0
    return {
        "line": rnum(best["line"], 2),
        "zoneLow": rnum(min(best["low"], best["line"]*(1-pad)), 2),
        "zoneHigh": rnum(max(best["high"], best["line"]*(1+pad)), 2),
        "score": rnum(best["score"], 2),
        "touches": int(best["touches"]),
        "sourceCount": int(best["sourceCount"]),
        "sources": best["sources"],
        "distanceFromReferencePct": rnum(best["distancePct"]),
        "candidateCount": len(candidates),
    }


def classify_breakout(break_core, cur_tv, tv_ratio, vol_ratio, close_loc, relative_prior, cfg):
    if not break_core:
        return "NO_BREAK"
    money_ok = (
        cur_tv >= float(cfg["jindolMinTradingValueKrw"])
        and (tv_ratio or 0) >= float(cfg["jindolMinTurnoverRatio20"])
        and (vol_ratio or 0) >= float(cfg["jindolMinVolumeRatio20"])
    )
    acceptance_ok = close_loc >= float(cfg["jindolMinCloseLocation"])
    relative_ok = relative_prior is None or relative_prior >= float(cfg["jindolMinRelativePriorMoney"])
    return "JINDOL_CONFIRMED" if money_ok and acceptance_ok and relative_ok else "GADOL_RISK"


def analyze_frame(meta, raw_df, cfg):
    if raw_df is None:
        return {"status": "NO_DATA", **meta}
    need = ["Open", "High", "Low", "Close", "Volume"]
    if any(c not in raw_df.columns for c in need):
        return {"status": "BAD_SCHEMA", **meta, "columns": list(raw_df.columns)}

    df = raw_df[need].dropna().copy()
    if len(df) < int(cfg["minNewListingRows"]):
        return {"status": "INSUFFICIENT_HISTORY", **meta, "rows": len(df)}
    df = add_indicators(df, cfg)

    cur, prev = df.iloc[-1], df.iloc[-2]
    long_track = len(df) >= int(cfg["minLongHistoryRows"]) and pd.notna(cur.get("MA600"))

    avg20_tv = cur.get("AVG20_TV_EST")
    cur_tv_est = float(cur["TV_EST"])
    cur_tv = float(meta["amount"]) if meta.get("amount") and meta["amount"] > 0 else cur_tv_est
    tv_quality = "KRX_EXACT_CURRENT__HIST_ESTIMATED" if meta.get("amount") else "ESTIMATED"
    tv_ratio = cur_tv / float(avg20_tv) if pd.notna(avg20_tv) and float(avg20_tv) > 0 else None
    avg20_vol = cur.get("AVG20_VOL")
    vol_ratio = float(cur["Volume"]) / float(avg20_vol) if pd.notna(avg20_vol) and float(avg20_vol) > 0 else None

    body_pct = pct(cur["Close"], cur["Open"])
    chg_pct = pct(cur["Close"], prev["Close"])
    close_loc = float(cur["CLOSE_LOC"])
    cloud = cloud_snapshot(cur)

    lb = min(len(df) - 1, int(cfg["corporateActionGuardLookback"]))
    moves = df["Close"].pct_change().iloc[-lb:].abs()
    jump_mask = moves > float(cfg["corporateActionJumpPct"]) / 100.0
    anomaly = list(moves[jump_mask].index.strftime("%Y%m%d"))
    recent_moves = moves.iloc[-int(cfg["recentDataWarningLookbackSessions"]):]
    recent_anomaly = list(recent_moves[recent_moves > float(cfg["corporateActionJumpPct"]) / 100.0].index.strftime("%Y%m%d"))

    events = rolling_event_mask(df, cfg)
    prior_event_pos = latest_event_position(events, int(cfg["priorIgnitionLookbackSessions"]), exclude_last=True)
    prior_event = event_info(df, prior_event_pos) if prior_event_pos is not None else None
    prior_tv = float(df["TV_EST"].iloc[prior_event_pos]) if prior_event_pos is not None else None
    rel_prior_money = cur_tv / prior_tv if prior_tv and prior_tv > 0 else None

    current_deoyang = bool(
        cur["Close"] > cur["Open"]
        and (chg_pct or -999) >= float(cfg["deoyangbongMinReturnPct"])
        and cur_tv >= float(cfg["deoyangbongMinTradingValueKrw"])
        and (vol_ratio or 0) >= float(cfg["deoyangbongMinVolumeRatio20"])
        and close_loc >= float(cfg["deoyangbongMinCloseLocation"])
    )
    current_deoyang_preferred = bool(
        current_deoyang and (chg_pct or -999) >= float(cfg["deoyangbongPreferredReturnPct"])
    )

    abc = abc_features(df, cfg)
    core = build_core_resistance(df.iloc[:-1], float(prev["Close"]), cfg)

    break_core = False
    pre_jindol_raw = False
    if core:
        zhi = float(core["zoneHigh"])
        break_core = bool(prev["Close"] <= zhi and cur["Close"] > zhi)
        dist = pct(core["line"], cur["Close"])
        pre_jindol_raw = bool(not break_core and dist is not None and 0 <= dist <= float(cfg["preJindolMaxDistancePct"]))

    avg_liquid = bool(pd.notna(avg20_tv) and float(avg20_tv) >= float(cfg["discoveryMinAvg20TradingValueKrw"]))
    recent_reference = bool(
        prior_event_pos is not None
        and (len(df) - 1 - prior_event_pos) <= int(cfg["preJindolPriorReferenceLookbackSessions"])
    )
    d600_abs = None
    if long_track and pd.notna(cur.get("MA600")):
        d600_abs = abs(pct(cur["Close"], cur["MA600"]) or 999)
    abc_candidate = bool(
        avg_liquid and (
            abc.get("state") == "C_ACTIVE"
            or (
                abc.get("state") == "B_BASE"
                and d600_abs is not None
                and d600_abs <= float(cfg["abcCandidateMaxDistanceMa600Pct"])
            )
        )
    )
    core_quality = bool(
        core
        and float(core.get("score") or 0) >= float(cfg["preJindolMinCoreScore"])
        and int(core.get("sourceCount") or 0) >= int(cfg["preJindolMinCoreSourceCount"])
    )
    pre_jindol = bool(
        pre_jindol_raw
        and avg_liquid
        and core_quality
        and (
            abc.get("bPlus")
            or abc_candidate
            or recent_reference
            or not long_track
        )
    )

    breakout_class = classify_breakout(
        break_core, cur_tv, tv_ratio, vol_ratio, close_loc, rel_prior_money, cfg
    )
    core_distance_now = pct(core["line"], cur["Close"]) if core else None

    ma, ma_dist = {}, {}
    for p in [int(x) for x in cfg["maPeriods"]]:
        v = cur.get(f"MA{p}")
        ma[str(p)] = rnum(v, 2) if pd.notna(v) else None
        ma_dist[str(p)] = rnum(pct(cur["Close"], v), 2) if pd.notna(v) else None

    cross600 = near600 = False
    if long_track:
        cross600 = bool(prev["Close"] <= prev["MA600"] and cur["Close"] > cur["MA600"])
        d600 = pct(cur["Close"], cur["MA600"])
        near600 = bool(
            not cross600 and cur["Close"] <= cur["MA600"]
            and d600 is not None and abs(d600) <= float(cfg["nearMa600Pct"])
        )

    recent_anchor_pos = latest_event_position(events, int(cfg["acceptanceLookbackSessions"]), exclude_last=True)
    retest_ok = reaccel = False
    anchor = None
    retest_supply = {
        "pullbackTradingValueToAnchor": None,
        "pullbackVolumeToAnchor": None,
        "supplyDry": False,
    }
    if recent_anchor_pos is not None:
        anchor = event_info(df, recent_anchor_pos)
        anchor_close = float(df["Close"].iloc[recent_anchor_pos])
        anchor_open = float(df["Open"].iloc[recent_anchor_pos])
        anchor_tv = float(df["TV_EST"].iloc[recent_anchor_pos])
        anchor_vol = float(df["Volume"].iloc[recent_anchor_pos])
        hold_line = max(anchor_open, anchor_close * (1 - float(cfg["anchorCloseUnderTolerancePct"]) / 100.0))
        post = df.iloc[recent_anchor_pos+1:]
        if len(post):
            # On a reacceleration day, judge supply contraction on the intervening pullback,
            # excluding today's renewed demand. If today is the first rest day, use today.
            pullback = post.iloc[:-1] if len(post) >= 2 else post
            pb_tv = float(pullback["TV_EST"].max()) if len(pullback) else 0.0
            pb_vol = float(pullback["Volume"].max()) if len(pullback) else 0.0
            pb_tv_ratio = pb_tv / anchor_tv if anchor_tv > 0 else None
            pb_vol_ratio = pb_vol / anchor_vol if anchor_vol > 0 else None
            supply_dry = bool(
                pb_tv_ratio is not None
                and pb_vol_ratio is not None
                and pb_tv_ratio <= float(cfg["retestMaxPullbackTradingValueRatio"])
                and pb_vol_ratio <= float(cfg["retestMaxPullbackVolumeRatio"])
            )
            retest_supply = {
                "pullbackTradingValueToAnchor": rnum(pb_tv_ratio),
                "pullbackVolumeToAnchor": rnum(pb_vol_ratio),
                "supplyDry": supply_dry,
            }
            price_hold = bool(
                float(post["Close"].min()) >= hold_line
                and cur["Close"] >= anchor_close * (1 - float(cfg["anchorCloseUnderTolerancePct"]) / 100.0)
            )
            retest_ok = bool(price_hold and supply_dry)
            if len(post) >= 2:
                prior_high = float(post["High"].iloc[:-1].max())
                reaccel = bool(
                    retest_ok and cur["Close"] > prior_high
                    and (tv_ratio or 0) >= float(cfg["reaccelerationTurnoverRatio20"])
                    and close_loc >= float(cfg["reaccelerationMinCloseLocation"])
                )

    yey = False
    if len(df) >= 3:
        first, rest, now = df.iloc[-3], df.iloc[-2], df.iloc[-1]
        first_event = bool(events.iloc[-3])
        controlled_rest = bool(
            rest["Close"] < rest["Open"]
            and rest["Close"] >= first["Open"]
            and rest["Low"] >= first["Open"] * (1 - float(cfg["yangEumYangMaxUnderFirstOpenPct"]) / 100.0)
        )
        final_up = bool(
            now["Close"] > now["Open"] and now["Close"] > rest["High"]
            and (tv_ratio or 0) >= float(cfg["yangEumYangMinTurnoverRatio20"])
        )
        yey = bool(first_event and controlled_rest and final_up)

    new_listing_setup = False
    if not long_track:
        ev_pos = latest_event_position(events, int(cfg["newListingEventLookbackSessions"]), exclude_last=False)
        if ev_pos is not None:
            since = df.iloc[ev_pos:]
            if len(since) >= 3:
                lo, hi = float(since["Low"].min()), float(since["High"].max())
                rng_pct = (hi / lo - 1.0) * 100.0 if lo > 0 else None
                new_listing_setup = bool(
                    rng_pct is not None and rng_pct <= float(cfg["newListingMaxPostEventRangePct"])
                )

    gaodol_actionable = bool(
        breakout_class == "GADOL_RISK"
        and (
            cur_tv >= float(cfg["gaodolMinTradingValueKrw"])
            or (tv_ratio or 0) >= float(cfg["gaodolMinTurnoverRatio20"])
        )
    )

    if recent_anomaly:
        signal = "DATA_WARNING"
    elif reaccel or yey:
        signal = "REACCELERATION"
    elif breakout_class == "JINDOL_CONFIRMED":
        signal = "JINDOL_CONFIRMED"
    elif gaodol_actionable:
        signal = "GADOL_RISK"
    elif retest_ok:
        signal = "RETEST_OK"
    elif current_deoyang and abc.get("cActive"):
        signal = "DEOYANGBONG_C_TRIGGER"
    elif pre_jindol:
        signal = "PRE_JINDOL"
    elif abc.get("bPlus") and avg_liquid:
        signal = "B_PLUS"
    elif abc_candidate:
        signal = "ABC_CANDIDATE"
    elif new_listing_setup:
        signal = "NEW_LISTING_SETUP"
    elif cross600:
        signal = "MA600_BREAKOUT"
    elif near600:
        signal = "NEAR_MA600"
    else:
        signal = "NONE"

    money_score = 0
    if cur_tv >= float(cfg["veryStrongTradingValueKrw"]):
        money_score += 20
    elif cur_tv >= float(cfg["jindolMinTradingValueKrw"]):
        money_score += 14
    elif cur_tv >= float(cfg["discoveryMinTradingValueKrw"]):
        money_score += 6
    if (tv_ratio or 0) >= 2:
        money_score += 8
    elif (tv_ratio or 0) >= 1.3:
        money_score += 4
    if (vol_ratio or 0) >= 2:
        money_score += 8
    elif (vol_ratio or 0) >= 1.5:
        money_score += 4
    if close_loc >= 0.7:
        money_score += 4

    structure_score = int(abc.get("score", 0))
    if cloud["state"] == "ABOVE":
        structure_score += 8
    if core:
        structure_score += min(12, int(round(float(core["score"]))))
    if current_deoyang:
        structure_score += 10
    if breakout_class == "JINDOL_CONFIRMED":
        structure_score += 18
    if retest_ok:
        structure_score += 8
    if reaccel or yey:
        structure_score += 15
    if recent_anomaly:
        structure_score -= 60
    elif anomaly:
        structure_score -= 8
    raw_score = max(0, structure_score + money_score)
    total_score = min(100, raw_score)

    structural_grade = "STRONG" if total_score >= 80 else ("GOOD" if total_score >= 65 else ("WATCH" if total_score >= 50 else "EARLY"))
    money_band = (
        "VERY_STRONG_300B_PLUS" if cur_tv >= float(cfg["veryStrongTradingValueKrw"])
        else "YBM_CORE_100B_PLUS" if cur_tv >= float(cfg["jindolMinTradingValueKrw"])
        else "DISCOVERY_30B_PLUS" if cur_tv >= float(cfg["discoveryMinTradingValueKrw"])
        else "LIGHT"
    )

    warnings = []
    if anomaly:
        warnings.append(f"HIST_PRICE_JUMP>{cfg['corporateActionJumpPct']}%:{','.join(anomaly[-3:])}")
    if recent_anomaly:
        warnings.append(f"RECENT_PRICE_JUMP>{cfg['corporateActionJumpPct']}%:{','.join(recent_anomaly[-3:])}")
    if tv_quality == "ESTIMATED":
        warnings.append("CURRENT_TRADING_VALUE_ESTIMATED")

    return {
        "status": "OK",
        "code": meta["code"],
        "name": meta["name"],
        "market": meta["market"],
        "tradeDate": df.index[-1].strftime("%Y%m%d"),
        "track": "LONG_HISTORY" if long_track else "NEW_LISTING",
        "signal": signal,
        "structuralGrade": structural_grade,
        "score": int(total_score),
        "rawScore": int(raw_score),
        "close": rnum(cur["Close"], 0),
        "open": rnum(cur["Open"], 0),
        "high": rnum(cur["High"], 0),
        "low": rnum(cur["Low"], 0),
        "dayChangePct": rnum(chg_pct),
        "bodyPct": rnum(body_pct),
        "closeLocation": rnum(close_loc, 3),
        "ma": ma,
        "distanceToMaPct": ma_dist,
        "cross600": bool(cross600),
        "near600": bool(near600),
        "cloud": cloud,
        "abc": abc,
        "deoyangbong": {"today": bool(current_deoyang), "preferred15Pct": bool(current_deoyang_preferred), "latestPrior": prior_event},
        "coreResistance": core,
        "distanceToCorePct": rnum(core_distance_now),
        "breakCoreResistance": bool(break_core),
        "breakoutClass": breakout_class,
        "preJindol": bool(pre_jindol),
        "retestOk": bool(retest_ok),
        "retestSupply": retest_supply,
        "reacceleration": bool(reaccel),
        "yangEumYang": bool(yey),
        "recentReferenceCandle": anchor,
        "newListingSetup": bool(new_listing_setup),
        "money": {
            "band": money_band,
            "tradingValue": rnum(cur_tv, 0),
            "tradingValueEstimatedFromOhlcv": rnum(cur_tv_est, 0),
            "avg20TradingValueEstimated": rnum(avg20_tv, 0),
            "tradingValueRatio20Estimated": rnum(tv_ratio),
            "tradingValueQuality": tv_quality,
            "volume": rnum(cur["Volume"], 0),
            "avg20Volume": rnum(avg20_vol, 0),
            "volumeRatio20": rnum(vol_ratio),
            "relativeToPriorReferenceMoney": rnum(rel_prior_money),
            "marketCap": rnum(meta.get("marcap"), 0),
            "turnoverToMarketCapPct": rnum(cur_tv/meta["marcap"]*100.0) if meta.get("marcap") else None,
        },
        "rows": len(df),
        "dataWarnings": warnings,
    }


def analyze(meta, cfg):
    start = (dt.date.today() - dt.timedelta(days=int(cfg["historyCalendarDays"]))).isoformat()
    df = fdr.DataReader(meta["code"], start)
    return analyze_frame(meta, df, cfg)


SIGNAL_PRIORITY = {
    "REACCELERATION": 100,
    "JINDOL_CONFIRMED": 95,
    "RETEST_OK": 90,
    "DEOYANGBONG_C_TRIGGER": 85,
    "PRE_JINDOL": 80,
    "B_PLUS": 70,
    "ABC_CANDIDATE": 60,
    "NEW_LISTING_SETUP": 55,
    "MA600_BREAKOUT": 45,
    "NEAR_MA600": 35,
    "GADOL_RISK": 25,
    "DATA_WARNING": 0,
    "NONE": -1,
}


def is_briefing_candidate(x, cfg):
    """Strict next-session discovery layer.

    The full state map stays in allCandidates/radarCandidates so early structures are
    not lost. briefingCandidates is intentionally narrower and is the layer meant to
    be summarized exhaustively in the next 08:15 plan.
    """
    sig = x.get("signal")
    money = x.get("money") or {}
    core = x.get("coreResistance") or {}
    abc = x.get("abc") or {}
    ref = (x.get("deoyangbong") or {}).get("latestPrior") or {}
    avg_tv = money.get("avg20TradingValueEstimated") or 0
    tv = money.get("tradingValue") or 0
    tv_ratio = money.get("tradingValueRatio20Estimated") or 0
    vol_ratio = money.get("volumeRatio20") or 0
    dist_core = x.get("distanceToCorePct")
    core_score = core.get("score") or 0

    if sig in ("REACCELERATION", "JINDOL_CONFIRMED", "DEOYANGBONG_C_TRIGGER"):
        return True

    if sig == "RETEST_OK":
        return bool(
            (x.get("retestSupply") or {}).get("supplyDry")
            and (ref.get("tradingValueEstimated") or 0) >= float(cfg["deoyangbongMinTradingValueKrw"])
            and avg_tv >= float(cfg["discoveryMinAvg20TradingValueKrw"])
        )

    if sig == "PRE_JINDOL":
        return bool(
            avg_tv >= float(cfg["briefingMinAvg20TradingValueKrw"])
            and core_score >= float(cfg["briefingMinCoreScore"])
            and dist_core is not None
            and 0 <= dist_core <= float(cfg["briefingPreJindolMaxDistancePct"])
            and (
                abc.get("bPlus")
                or (ref.get("tradingValueEstimated") or 0) >= float(cfg["deoyangbongMinTradingValueKrw"])
                or (abc.get("score") or 0) >= float(cfg["briefingAbcMinScore"])
            )
        )

    if sig == "B_PLUS":
        return bool(avg_tv >= float(cfg["briefingMinAvg20TradingValueKrw"]))

    if sig == "ABC_CANDIDATE":
        return bool(
            avg_tv >= float(cfg["briefingMinAvg20TradingValueKrw"])
            and (abc.get("score") or 0) >= float(cfg["briefingAbcMinScore"])
            and dist_core is not None
            and 0 <= dist_core <= float(cfg["briefingPreJindolMaxDistancePct"])
        )

    if sig == "NEW_LISTING_SETUP":
        return bool(
            avg_tv >= float(cfg["briefingMinAvg20TradingValueKrw"])
            and (ref.get("tradingValueEstimated") or 0) >= float(cfg["deoyangbongMinTradingValueKrw"])
        )

    if sig == "MA600_BREAKOUT":
        return bool(
            tv >= float(cfg["discoveryMinTradingValueKrw"])
            and tv_ratio >= float(cfg["jindolMinTurnoverRatio20"])
            and vol_ratio >= float(cfg["jindolMinVolumeRatio20"])
        )

    return False


def sortit(xs):
    return sorted(
        xs,
        key=lambda x: (
            SIGNAL_PRIORITY.get(x.get("signal"), 0),
            x.get("rawScore", x.get("score", 0)),
            ((x.get("money") or {}).get("tradingValueRatio20Estimated") or 0),
            ((x.get("money") or {}).get("tradingValue") or 0),
        ),
        reverse=True,
    )


def run(cfg):
    uni = current_listing()
    if len(uni) < int(cfg["minUniverseCount"]):
        return {"status": "FAIL_UNIVERSE", "generatedAtKst": dt.datetime.now(KST).isoformat(), "universeCount": len(uni)}

    results, errors = [], []
    with cf.ThreadPoolExecutor(max_workers=int(cfg["maxWorkers"])) as ex:
        fm = {ex.submit(analyze, m, cfg): m for m in uni}
        for fut in cf.as_completed(fm):
            m = fm[fut]
            try:
                results.append(fut.result())
            except Exception as e:
                errors.append({"code": m["code"], "name": m["name"], "error": f"{type(e).__name__}: {e}"})

    ok = [x for x in results if x.get("status") == "OK"]
    insufficient = [x for x in results if x.get("status") == "INSUFFICIENT_HISTORY"]
    bad_schema = [x for x in results if x.get("status") == "BAD_SCHEMA"]
    dates = Counter(x.get("tradeDate") for x in ok if x.get("tradeDate"))
    td = dates.most_common(1)[0][0] if dates else None
    cur = [x for x in ok if x.get("tradeDate") == td]

    bucket_names = [
        "REACCELERATION", "JINDOL_CONFIRMED", "RETEST_OK", "DEOYANGBONG_C_TRIGGER",
        "PRE_JINDOL", "B_PLUS", "ABC_CANDIDATE", "GADOL_RISK",
        "NEW_LISTING_SETUP", "MA600_BREAKOUT", "NEAR_MA600", "DATA_WARNING"
    ]
    by_signal = {name: sortit([x for x in cur if x["signal"] == name]) for name in bucket_names}
    allc = sortit([x for x in cur if x["signal"] != "NONE"])
    briefing = sortit([x for x in allc if is_briefing_candidate(x, cfg)])
    risk_warnings = sortit([x for x in allc if x.get("signal") == "GADOL_RISK"])
    briefing_codes = {x["code"] for x in briefing}
    risk_codes = {x["code"] for x in risk_warnings}
    radar = sortit([x for x in allc if x["code"] not in briefing_codes and x["code"] not in risk_codes])

    # Candidate flow enrichment is briefing-first, then risk warnings, then the broad radar.
    flow_pool = []
    seen = set()
    for x in briefing + risk_warnings + allc:
        if x["code"] not in seen:
            seen.add(x["code"])
            flow_pool.append(x)
    flow_n = min(int(cfg.get("flowEnrichTopN", 60)), len(flow_pool))
    flow_errors = []
    if flow_n:
        with cf.ThreadPoolExecutor(max_workers=min(8, int(cfg["maxWorkers"]))) as ex:
            fm2 = {
                ex.submit(fetch_investor_flow, x["code"], int(cfg.get("flowLookbackSessions", 20))): x
                for x in flow_pool[:flow_n]
            }
            for fut in cf.as_completed(fm2):
                x = fm2[fut]
                try:
                    x["investorFlow"] = fut.result()
                except Exception as e:
                    x["investorFlow"] = {"status": "ERROR", "error": f"{type(e).__name__}: {e}"}
                    flow_errors.append({"code": x["code"], "error": f"{type(e).__name__}: {e}"})

    er = len(errors) / max(1, len(uni))
    sr = (len(ok) - len(cur)) / max(1, len(ok))
    candidate_ratio = len(allc) / max(1, len(cur))
    briefing_ratio = len(briefing) / max(1, len(cur))
    status = "PASS" if (
        er <= float(cfg["maxErrorRatioForPass"])
        and sr <= float(cfg["maxStaleRatioForPass"])
        and candidate_ratio <= float(cfg["maxCandidateRatioForPass"])
        and len(briefing) <= int(cfg["maxBriefingCandidatesForPass"])
    ) else "PARTIAL"
    lim = int(cfg["maxPerBucket"])
    counts = {name: len(xs) for name, xs in by_signal.items()}
    counts["allCandidates"] = len(allc)
    counts["briefingCandidates"] = len(briefing)
    counts["riskWarnings"] = len(risk_warnings)
    counts["radarCandidates"] = len(radar)

    def take(name):
        return by_signal[name][:lim]

    return {
        "status": status,
        "generatedAtKst": dt.datetime.now(KST).isoformat(),
        "tradeDate": td,
        "methodologyVersion": cfg["methodologyVersion"],
        "primaryLogic": "ABC/base + MA240/480/600/1000 + Deoyangbong + core resistance + money quality + Jindol/Gadol + retest/reacceleration",
        "sourceBoundary": {
            "sourceDerived": [
                "ABC long decline -> long base -> MA600 recovery/N-wave framing",
                "MA600/MA1000 major anchors; MA240 earlier recovery clue",
                "large bullish reference candle and its open/close as primary support/resistance evidence",
                "previous high/candle-density/round figure as secondary support/resistance evidence",
                "both volume and trading value matter; KRW 100bn is the taught minimum money reference",
                "cloud/overhead supply, Neomoneomo digestion, Jindol/Gadol, Yang-Eum-Yang",
            ],
            "implementationInference": [
                "exact ABC windows/range/slope thresholds",
                "resistance clustering weights/tolerances",
                "relative-money threshold and structural score",
                "new-listing mini-track thresholds",
            ],
        },
        "notes": [
            "News/catalyst is intentionally excluded.",
            "No hidden operator/accumulation intent is inferred.",
            "StructuralGrade is this system's grade, not the source teacher's S/A/B grade.",
            "Current trading value is exact KRX Amount when available; historical trading value is estimated from typical price x volume.",
            "Core resistance is built from pre-current data only to avoid look-ahead leakage.",
        ],
        "coverage": {
            "universe": len(uni),
            "ok": len(ok),
            "currentTradeDate": len(cur),
            "insufficientHistory": len(insufficient),
            "badSchema": len(bad_schema),
            "fetchErrors": len(errors),
            "staleRows": len(ok) - len(cur),
            "errorRatio": round(er, 4),
            "staleRatio": round(sr, 4),
            "tradeDateCounts": dict(dates.most_common(5)),
            "flowEnriched": flow_n,
            "flowErrors": len(flow_errors),
            "candidateRatio": round(candidate_ratio, 4),
            "briefingCandidateRatio": round(briefing_ratio, 4),
        },
        "counts": counts,
        "reacceleration": take("REACCELERATION"),
        "jindol": take("JINDOL_CONFIRMED"),
        "retest": take("RETEST_OK"),
        "deoyangC": take("DEOYANGBONG_C_TRIGGER"),
        "preJindol": take("PRE_JINDOL"),
        "bPlus": take("B_PLUS"),
        "abc": take("ABC_CANDIDATE"),
        "gaodol": take("GADOL_RISK"),
        "newListing": take("NEW_LISTING_SETUP"),
        "ma600": sortit(take("MA600_BREAKOUT") + take("NEAR_MA600"))[:lim],
        "warnings": take("DATA_WARNING"),
        "briefingCandidates": briefing,
        "riskWarnings": risk_warnings,
        "radarCandidates": radar[:int(cfg["maxAllCandidates"])],
        "allCandidates": allc[:int(cfg["maxAllCandidates"])],
        "sampleErrors": errors[:30],
        "sampleFlowErrors": flow_errors[:20],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="longterm-scan-config.json")
    ap.add_argument("--output", default="longterm-scan.json")
    args = ap.parse_args()

    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    out = run(cfg)
    payload = json.dumps(out, ensure_ascii=False, indent=2, default=json_default)
    tmp = Path(args.output + ".tmp")
    tmp.write_text(payload, encoding="utf-8")
    tmp.replace(args.output)
    preview = []
    for x in (out.get("briefingCandidates") or [])[:20]:
        preview.append({
            "code": x.get("code"),
            "name": x.get("name"),
            "signal": x.get("signal"),
            "score": x.get("score"),
            "coreLine": (x.get("coreResistance") or {}).get("line"),
            "tradingValue": (x.get("money") or {}).get("tradingValue"),
        })
    print(json.dumps({
        "status": out.get("status"),
        "tradeDate": out.get("tradeDate"),
        "methodologyVersion": out.get("methodologyVersion"),
        "coverage": out.get("coverage"),
        "counts": out.get("counts"),
        "topPreview": preview,
    }, ensure_ascii=False, indent=2, default=json_default))
    return 0 if out.get("status") in ("PASS", "PARTIAL") else 2


if __name__ == "__main__":
    raise SystemExit(main())
