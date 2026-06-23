"""
Compute technical indicators from a DataFrame of OHLCV bars.
All functions accept a pandas DataFrame with columns: open, high, low, close, volume
and return a dict of the most recent computed values.
"""
import pandas as pd
import pandas_ta as ta


def compute_all(df: pd.DataFrame, config: dict) -> dict:
    """Return latest indicator snapshot for a single ticker."""
    if len(df) < 30:
        return {}

    close = df["close"]
    volume = df["volume"]

    # ── RSI ──────────────────────────────────────────────────────────────────
    rsi_series = ta.rsi(close, length=14)
    rsi = round(float(rsi_series.iloc[-1]), 2) if rsi_series is not None else None

    # ── MACD ─────────────────────────────────────────────────────────────────
    macd_df = ta.macd(close, fast=12, slow=26, signal=9)
    if macd_df is not None and not macd_df.empty:
        hist = macd_df["MACDh_12_26_9"]
        macd_hist = round(float(hist.iloc[-1]), 4)
        macd_hist_prev = round(float(hist.iloc[-2]), 4)
        macd_line = round(float(macd_df["MACD_12_26_9"].iloc[-1]), 4)
        signal_line = round(float(macd_df["MACDs_12_26_9"].iloc[-1]), 4)
    else:
        macd_hist = macd_hist_prev = macd_line = signal_line = None

    # ── EMA crossover (9 / 21) ───────────────────────────────────────────────
    ema9 = ta.ema(close, length=9)
    ema21 = ta.ema(close, length=21)
    ema50 = ta.ema(close, length=50)
    ema200 = ta.ema(close, length=200)

    ema9_val = round(float(ema9.iloc[-1]), 2) if ema9 is not None else None
    ema21_val = round(float(ema21.iloc[-1]), 2) if ema21 is not None else None
    ema50_val = round(float(ema50.iloc[-1]), 2) if ema50 is not None and len(df) >= 50 else None
    ema200_val = round(float(ema200.iloc[-1]), 2) if ema200 is not None and len(df) >= 200 else None

    ema9_prev = round(float(ema9.iloc[-2]), 2) if ema9 is not None else None
    ema21_prev = round(float(ema21.iloc[-2]), 2) if ema21 is not None else None

    # ── Bollinger Bands ──────────────────────────────────────────────────────
    bb = ta.bbands(close, length=20, std=2)
    if bb is not None and not bb.empty:
        bb_upper = round(float(bb["BBU_20_2.0"].iloc[-1]), 2)
        bb_lower = round(float(bb["BBL_20_2.0"].iloc[-1]), 2)
        bb_mid = round(float(bb["BBM_20_2.0"].iloc[-1]), 2)
        bb_width = round((bb_upper - bb_lower) / bb_mid, 4)
    else:
        bb_upper = bb_lower = bb_mid = bb_width = None

    # ── Volume spike ─────────────────────────────────────────────────────────
    vol_avg = float(volume.rolling(20).mean().iloc[-1])
    vol_current = float(volume.iloc[-1])
    vol_ratio = round(vol_current / vol_avg, 2) if vol_avg > 0 else 0.0

    return {
        "price": round(float(close.iloc[-1]), 2),
        "rsi": rsi,
        "macd_hist": macd_hist,
        "macd_hist_prev": macd_hist_prev,
        "macd_line": macd_line,
        "macd_signal": signal_line,
        "ema9": ema9_val,
        "ema21": ema21_val,
        "ema50": ema50_val,
        "ema200": ema200_val,
        "ema9_prev": ema9_prev,
        "ema21_prev": ema21_prev,
        "bb_upper": bb_upper,
        "bb_lower": bb_lower,
        "bb_mid": bb_mid,
        "bb_width": bb_width,
        "volume": int(vol_current),
        "volume_avg_20": int(vol_avg),
        "volume_ratio": vol_ratio,
    }
