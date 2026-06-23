"""
Compute technical indicators from a DataFrame of OHLCV bars using pure pandas/numpy.
"""
import pandas as pd
import numpy as np


def _ema(series: pd.Series, length: int) -> pd.Series:
    return series.ewm(span=length, adjust=False).mean()


def _rsi(close: pd.Series, length: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(com=length - 1, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(com=length - 1, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def compute_all(df: pd.DataFrame, config: dict) -> dict:
    if len(df) < 30:
        return {}

    close = df["close"]
    volume = df["volume"]

    # ── RSI ──────────────────────────────────────────────────────────────────
    rsi_series = _rsi(close, 14)
    rsi = round(float(rsi_series.iloc[-1]), 2)

    # ── MACD ─────────────────────────────────────────────────────────────────
    ema12 = _ema(close, 12)
    ema26 = _ema(close, 26)
    macd_line = ema12 - ema26
    signal_line = _ema(macd_line, 9)
    hist = macd_line - signal_line
    macd_hist = round(float(hist.iloc[-1]), 4)
    macd_hist_prev = round(float(hist.iloc[-2]), 4)

    # ── EMA crossovers ───────────────────────────────────────────────────────
    ema9  = _ema(close, 9)
    ema21 = _ema(close, 21)
    ema50 = _ema(close, 50) if len(df) >= 50 else None
    ema200 = _ema(close, 200) if len(df) >= 200 else None

    # ── Bollinger Bands ──────────────────────────────────────────────────────
    sma20 = close.rolling(20).mean()
    std20 = close.rolling(20).std()
    bb_upper = sma20 + 2 * std20
    bb_lower = sma20 - 2 * std20
    bb_mid = sma20
    _bb_upper = round(float(bb_upper.iloc[-1]), 2)
    _bb_lower = round(float(bb_lower.iloc[-1]), 2)
    _bb_mid   = round(float(bb_mid.iloc[-1]), 2)
    bb_width  = round((_bb_upper - _bb_lower) / _bb_mid, 4) if _bb_mid else None

    # ── Volume spike ─────────────────────────────────────────────────────────
    vol_avg = float(volume.rolling(20).mean().iloc[-1])
    vol_current = float(volume.iloc[-1])
    vol_ratio = round(vol_current / vol_avg, 2) if vol_avg > 0 else 0.0

    return {
        "price": round(float(close.iloc[-1]), 2),
        "rsi": rsi,
        "macd_hist": macd_hist,
        "macd_hist_prev": macd_hist_prev,
        "macd_line": round(float(macd_line.iloc[-1]), 4),
        "macd_signal": round(float(signal_line.iloc[-1]), 4),
        "ema9":  round(float(ema9.iloc[-1]), 2),
        "ema21": round(float(ema21.iloc[-1]), 2),
        "ema50":  round(float(ema50.iloc[-1]), 2) if ema50 is not None else None,
        "ema200": round(float(ema200.iloc[-1]), 2) if ema200 is not None else None,
        "ema9_prev":  round(float(ema9.iloc[-2]), 2),
        "ema21_prev": round(float(ema21.iloc[-2]), 2),
        "bb_upper": _bb_upper,
        "bb_lower": _bb_lower,
        "bb_mid":   _bb_mid,
        "bb_width": bb_width,
        "volume": int(vol_current),
        "volume_avg_20": int(vol_avg),
        "volume_ratio": vol_ratio,
    }
