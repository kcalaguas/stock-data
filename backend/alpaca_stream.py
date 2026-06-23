"""
Manages Alpaca WebSocket data stream + historical bar seeding.
Uses alpaca-py SDK. Falls back gracefully if keys are missing (demo mode).
"""
from __future__ import annotations
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from collections import defaultdict

import pandas as pd

log = logging.getLogger(__name__)


class MarketDataManager:
    """
    Maintains an in-memory rolling OHLCV DataFrame per ticker.
    Seeded with 60 days of daily bars on startup; updated tick-by-tick
    via Alpaca WebSocket (or polling fallback).
    """

    def __init__(self, tickers: list[str], api_key: str, secret_key: str, live: bool = False):
        self.tickers = tickers
        self.api_key = api_key
        self.secret_key = secret_key
        self.live = live
        # ticker → pd.DataFrame(open,high,low,close,volume)
        self._bars: dict[str, pd.DataFrame] = defaultdict(pd.DataFrame)
        self._latest_price: dict[str, float] = {}
        self._on_bar_callbacks: list = []
        self._demo_mode = not (api_key and secret_key)
        if self._demo_mode:
            log.warning("No Alpaca keys — running in DEMO mode with synthetic data")

    def on_bar(self, cb):
        """Register a callback(ticker, df) called whenever a new bar is appended."""
        self._on_bar_callbacks.append(cb)

    async def start(self):
        if self._demo_mode:
            await self._run_demo()
            return

        await self._seed_history()
        asyncio.create_task(self._run_stream())

    # ── Historical seed ───────────────────────────────────────────────────────

    async def _seed_history(self):
        try:
            from alpaca.data.historical import StockHistoricalDataClient
            from alpaca.data.requests import StockBarsRequest
            from alpaca.data.timeframe import TimeFrame

            client = StockHistoricalDataClient(self.api_key, self.secret_key)
            end = datetime.now(timezone.utc)
            start = end - timedelta(days=300)  # 300 days covers 200-bar EMA warmup

            req = StockBarsRequest(
                symbol_or_symbols=self.tickers,
                timeframe=TimeFrame.Day,
                start=start,
                end=end,
            )
            bars = client.get_stock_bars(req).df

            for ticker in self.tickers:
                try:
                    df = bars.xs(ticker, level="symbol").copy()
                    df = df[["open", "high", "low", "close", "volume"]].sort_index()
                    df.index = pd.to_datetime(df.index)
                    self._bars[ticker] = df
                    self._latest_price[ticker] = float(df["close"].iloc[-1])
                    log.info("Seeded %s with %d bars", ticker, len(df))
                except KeyError:
                    log.warning("No historical data for %s", ticker)

        except Exception as e:
            log.error("History seed failed: %s", e)

    # ── Live WebSocket stream ─────────────────────────────────────────────────

    async def _run_stream(self):
        from alpaca.data.live import StockDataStream

        while True:
            try:
                stream = StockDataStream(self.api_key, self.secret_key)

                async def handle_bar(bar):
                    ticker = bar.symbol
                    new_row = pd.DataFrame([{
                        "open": float(bar.open),
                        "high": float(bar.high),
                        "low": float(bar.low),
                        "close": float(bar.close),
                        "volume": float(bar.volume),
                    }], index=[pd.Timestamp(bar.timestamp)])

                    df = self._bars.get(ticker, pd.DataFrame())
                    self._bars[ticker] = pd.concat([df, new_row]).tail(300)
                    self._latest_price[ticker] = float(bar.close)

                    for cb in self._on_bar_callbacks:
                        await cb(ticker, self._bars[ticker])

                stream.subscribe_bars(handle_bar, *self.tickers)
                log.info("Alpaca stream connected for %s", self.tickers)
                await stream._run_forever()

            except Exception as e:
                log.error("Stream error: %s — reconnecting in 5s", e)
                await asyncio.sleep(5)

    # ── Demo mode (synthetic prices for UI testing) ───────────────────────────

    async def _run_demo(self):
        import random
        prices = {t: 150.0 + random.uniform(-50, 200) for t in self.tickers}
        volumes = {t: random.randint(1_000_000, 10_000_000) for t in self.tickers}

        # Seed 60 synthetic daily bars
        for ticker in self.tickers:
            rows = []
            p = prices[ticker]
            for i in range(60):
                p *= 1 + random.gauss(0, 0.012)
                rows.append({
                    "open": round(p * 0.999, 2),
                    "high": round(p * 1.008, 2),
                    "low": round(p * 0.992, 2),
                    "close": round(p, 2),
                    "volume": random.randint(500_000, 15_000_000),
                })
            idx = pd.date_range(end=pd.Timestamp.now(), periods=60, freq="D")
            self._bars[ticker] = pd.DataFrame(rows, index=idx)
            self._latest_price[ticker] = round(p, 2)

        # Emit a new bar every 5 seconds to simulate live updates
        while True:
            for ticker in self.tickers:
                df = self._bars[ticker]
                last = float(df["close"].iloc[-1])
                p = last * (1 + random.gauss(0, 0.005))
                new_row = pd.DataFrame([{
                    "open": round(last, 2),
                    "high": round(max(last, p) * 1.002, 2),
                    "low": round(min(last, p) * 0.998, 2),
                    "close": round(p, 2),
                    "volume": random.randint(100_000, 2_000_000),
                }], index=[pd.Timestamp.now()])
                self._bars[ticker] = pd.concat([df, new_row]).tail(300)
                self._latest_price[ticker] = round(p, 2)

                for cb in self._on_bar_callbacks:
                    await cb(ticker, self._bars[ticker])

            await asyncio.sleep(5)

    def get_bars(self, ticker: str) -> pd.DataFrame:
        return self._bars.get(ticker, pd.DataFrame())

    def get_snapshot(self) -> dict[str, float]:
        return dict(self._latest_price)
