from __future__ import annotations

import math
import numpy as np
import pandas as pd


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


def add_indicators(raw, cfg):
    df = raw.copy()
    periods = sorted(set(int(x) for x in cfg["maPeriods"]))
    for p in periods:
        df[f"MA{p}"] = df["Close"].rolling(p, min_periods=p).mean()

    typical = (df["Open"] + df["High"] + df["Low"] + df["Close"]) / 4.0
    df["TV_EST"] = typical * df["Volume"]
    df["AVG20_TV_EST"] = df["TV_EST"].shift(1).rolling(20, min_periods=10).mean()
    df["TV_RATIO20_EST"] = df["TV_EST"] / df["AVG20_TV_EST"]
    df["AVG20_VOL"] = df["Volume"].shift(1).rolling(20, min_periods=10).mean()
    df["VOL_RATIO20"] = df["Volume"] / df["AVG20_VOL"]
    df["DAY_RETURN_PCT"] = df["Close"].pct_change() * 100.0
    rng = (df["High"] - df["Low"]).replace(0, np.nan)
    df["CLOSE_LOC"] = ((df["Close"] - df["Low"]) / rng).fillna(0.5)

    prev_close = df["Close"].shift(1)
    tr = pd.concat([
        df["High"] - df["Low"],
        (df["High"] - prev_close).abs(),
        (df["Low"] - prev_close).abs(),
    ], axis=1).max(axis=1)
    atr_n = int(cfg.get("atrPeriod", 14))
    df["ATR"] = tr.rolling(atr_n, min_periods=atr_n).mean()
    df["ATR_PCT"] = df["ATR"] / df["Close"] * 100.0

    rsi_n = int(cfg.get("rsiPeriod", 14))
    delta = df["Close"].diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1.0 / rsi_n, adjust=False, min_periods=rsi_n).mean()
    avg_loss = loss.ewm(alpha=1.0 / rsi_n, adjust=False, min_periods=rsi_n).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100.0 - 100.0 / (1.0 + rs)
    rsi = rsi.where(avg_loss > 0, 100.0)
    rsi = rsi.where(avg_gain > 0, 0.0)
    df["RSI"] = rsi
    return df


def rsi_context(df, cfg):
    out = {
        "period": int(cfg.get("rsiPeriod", 14)),
        "value": None,
        "slope": None,
        "direction": "UNAVAILABLE",
        "divergence": "NONE",
        "priceFirst": True,
        "auto7030Trigger": False,
    }
    if df is None or len(df) < 30 or "RSI" not in df:
        return out

    cur = df["RSI"].iloc[-1]
    if pd.isna(cur):
        return out
    slope_n = int(cfg.get("rsiSlopeSessions", 5))
    old = df["RSI"].iloc[-1-slope_n] if len(df) > slope_n else np.nan
    slope = float(cur - old) if pd.notna(old) else None
    threshold = float(cfg.get("rsiSlopeMeaningfulPoints", 2.0))
    direction = "FLAT"
    if slope is not None and slope >= threshold:
        direction = "STRENGTHENING"
    elif slope is not None and slope <= -threshold:
        direction = "WEAKENING"

    lb = min(len(df), int(cfg.get("rsiDivergenceLookbackSessions", 60)))
    half = int(cfg.get("rsiDivergenceSwingHalfWindow", 3))
    min_price = float(cfg.get("rsiDivergenceMinPriceDiffPct", 1.0))
    min_rsi = float(cfg.get("rsiDivergenceMinRsiDiffPoints", 3.0))
    sub = df.iloc[-lb:]
    lows, highs = [], []
    for i in range(half, len(sub)-half):
        if float(sub["Low"].iloc[i]) <= float(sub["Low"].iloc[i-half:i+half+1].min()):
            lows.append(i)
        if float(sub["High"].iloc[i]) >= float(sub["High"].iloc[i-half:i+half+1].max()):
            highs.append(i)

    divergence = "NONE"
    if len(lows) >= 2:
        a, b = lows[-2], lows[-1]
        pa, pb = float(sub["Low"].iloc[a]), float(sub["Low"].iloc[b])
        ra, rb = sub["RSI"].iloc[a], sub["RSI"].iloc[b]
        if pd.notna(ra) and pd.notna(rb) and pb <= pa*(1-min_price/100.0) and float(rb) >= float(ra)+min_rsi:
            divergence = "BULLISH_DIVERGENCE"

    if len(highs) >= 2:
        a, b = highs[-2], highs[-1]
        pa, pb = float(sub["High"].iloc[a]), float(sub["High"].iloc[b])
        ra, rb = sub["RSI"].iloc[a], sub["RSI"].iloc[b]
        if pd.notna(ra) and pd.notna(rb) and pb >= pa*(1+min_price/100.0) and float(rb) <= float(ra)-min_rsi:
            divergence = "BEARISH_DIVERGENCE"

    out.update({
        "value": rnum(cur, 2),
        "slope": rnum(slope, 2),
        "direction": direction,
        "divergence": divergence,
    })
    return out


def money_context(df, exact_current_amount=None):
    cur = df.iloc[-1]
    current = float(exact_current_amount) if exact_current_amount and exact_current_amount > 0 else float(cur["TV_EST"])
    avg20 = cur.get("AVG20_TV_EST")
    avg20 = float(avg20) if pd.notna(avg20) else None
    avg20_vol = cur.get("AVG20_VOL")
    avg20_vol = float(avg20_vol) if pd.notna(avg20_vol) else None
    return {
        "tradingValue": rnum(current, 0),
        "avg20TradingValueEstimated": rnum(avg20, 0),
        "tradingValueRatio20Estimated": rnum(current / avg20 if avg20 and avg20 > 0 else None),
        "volume": rnum(cur["Volume"], 0),
        "avg20Volume": rnum(avg20_vol, 0),
        "volumeRatio20": rnum(float(cur["Volume"]) / avg20_vol if avg20_vol and avg20_vol > 0 else None),
        "quality": "KRX_EXACT_CURRENT__HIST_ESTIMATED" if exact_current_amount else "ESTIMATED",
    }
