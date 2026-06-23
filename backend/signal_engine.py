"""
Evaluate indicator snapshots against thresholds and fire signals.
Each check returns a list of signal dicts (may be empty).
"""
from __future__ import annotations
from config import DEFAULT_SIGNAL_CONFIG


def evaluate(ticker: str, indicators: dict, config: dict | None = None) -> list[dict]:
    cfg = {**DEFAULT_SIGNAL_CONFIG, **(config or {})}
    signals: list[dict] = []

    price = indicators.get("price")
    if not price:
        return signals

    # ── RSI ──────────────────────────────────────────────────────────────────
    rsi = indicators.get("rsi")
    if rsi is not None:
        if rsi <= cfg["rsi_oversold"]:
            signals.append(_sig(ticker, "RSI_OVERSOLD", "BUY", price, rsi,
                                {"threshold": cfg["rsi_oversold"]}))
        elif rsi >= cfg["rsi_overbought"]:
            signals.append(_sig(ticker, "RSI_OVERBOUGHT", "SELL", price, rsi,
                                {"threshold": cfg["rsi_overbought"]}))

    # ── MACD histogram cross ──────────────────────────────────────────────────
    if cfg.get("macd_cross"):
        hist = indicators.get("macd_hist")
        hist_prev = indicators.get("macd_hist_prev")
        if hist is not None and hist_prev is not None:
            if hist_prev < 0 < hist:
                signals.append(_sig(ticker, "MACD_CROSS_BULL", "BUY", price, hist))
            elif hist_prev > 0 > hist:
                signals.append(_sig(ticker, "MACD_CROSS_BEAR", "SELL", price, hist))

    # ── EMA 9/21 crossover ───────────────────────────────────────────────────
    if cfg.get("ema_cross"):
        e9, e9p = indicators.get("ema9"), indicators.get("ema9_prev")
        e21, e21p = indicators.get("ema21"), indicators.get("ema21_prev")
        if all(v is not None for v in [e9, e9p, e21, e21p]):
            if e9p <= e21p and e9 > e21:
                signals.append(_sig(ticker, "EMA9_CROSS_ABOVE_21", "BUY", price,
                                    round(e9 - e21, 2)))
            elif e9p >= e21p and e9 < e21:
                signals.append(_sig(ticker, "EMA9_CROSS_BELOW_21", "SELL", price,
                                    round(e9 - e21, 2)))

    # ── Volume spike ─────────────────────────────────────────────────────────
    vol_ratio = indicators.get("volume_ratio", 0)
    if vol_ratio >= cfg["volume_spike_mult"]:
        signals.append(_sig(ticker, "VOLUME_SPIKE", "INFO", price, vol_ratio,
                            {"multiplier": vol_ratio, "threshold": cfg["volume_spike_mult"]}))

    # ── Bollinger Band squeeze ────────────────────────────────────────────────
    bb_width = indicators.get("bb_width")
    if bb_width is not None and bb_width < cfg["bb_squeeze_pct"]:
        signals.append(_sig(ticker, "BB_SQUEEZE", "INFO", price, bb_width,
                            {"bb_width": bb_width, "threshold": cfg["bb_squeeze_pct"]}))

    # ── Price at Bollinger extremes ───────────────────────────────────────────
    bb_upper = indicators.get("bb_upper")
    bb_lower = indicators.get("bb_lower")
    if bb_upper and price >= bb_upper:
        signals.append(_sig(ticker, "BB_UPPER_TOUCH", "SELL", price, bb_upper))
    if bb_lower and price <= bb_lower:
        signals.append(_sig(ticker, "BB_LOWER_TOUCH", "BUY", price, bb_lower))

    return signals


def _sig(ticker, signal_type, direction, price, indicator_value=None, extra=None):
    return {
        "ticker": ticker,
        "signal_type": signal_type,
        "direction": direction,
        "price": price,
        "indicator_value": indicator_value,
        "extra": extra,
    }
