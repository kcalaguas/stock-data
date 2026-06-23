"""
FastAPI backend for the stock signal dashboard.

Endpoints:
  GET  /api/snapshot          → latest price + indicators for all tickers
  GET  /api/alerts            → recent alert history
  POST /api/watchlist         → add ticker
  DELETE /api/watchlist/{t}   → remove ticker
  GET  /api/config            → current signal thresholds
  POST /api/config            → update signal thresholds
  WS   /ws                    → real-time push of {type, ticker, data}
"""
import asyncio
import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

import config as cfg
from alpaca_stream import MarketDataManager
from indicators import compute_all
from signal_engine import evaluate
from database import save_alert, get_recent_alerts
from alerts import send_email_alert, is_cooled_down

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ── State ────────────────────────────────────────────────────────────────────

market = MarketDataManager(
    tickers=list(cfg.WATCHLIST),
    api_key=cfg.ALPACA_API_KEY,
    secret_key=cfg.ALPACA_SECRET_KEY,
    live=cfg.ALPACA_LIVE,
)

# In-memory cache of latest indicator snapshots
indicator_cache: dict[str, dict] = {}
# Per-ticker signal config overrides
signal_configs: dict[str, dict] = {}
# Connected WebSocket clients
ws_clients: list[WebSocket] = []


# ── Bar callback ─────────────────────────────────────────────────────────────

async def on_new_bar(ticker: str, df):
    sig_cfg = signal_configs.get(ticker)
    indicators = compute_all(df, sig_cfg or cfg.DEFAULT_SIGNAL_CONFIG)
    if not indicators:
        return

    indicator_cache[ticker] = indicators
    signals = evaluate(ticker, indicators, sig_cfg)

    for signal in signals:
        if is_cooled_down(ticker, signal["signal_type"]):
            save_alert(
                ticker=ticker,
                signal_type=signal["signal_type"],
                direction=signal["direction"],
                price=signal["price"],
                indicator_value=signal.get("indicator_value"),
                extra=signal.get("extra"),
            )
            asyncio.create_task(send_email_alert(signal))
            await broadcast({"type": "SIGNAL", "data": signal})
            log.info("SIGNAL %s %s @ $%s", ticker, signal["signal_type"], signal["price"])

    await broadcast({"type": "TICK", "ticker": ticker, "data": indicators})


async def broadcast(msg: dict):
    dead = []
    for ws in ws_clients:
        try:
            await ws.send_text(json.dumps(msg))
        except Exception:
            dead.append(ws)
    for ws in dead:
        ws_clients.remove(ws)


# ── App lifecycle ─────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    market.on_bar(on_new_bar)
    await market.start()
    yield


app = FastAPI(title="Stock Signal Dashboard", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── REST API ──────────────────────────────────────────────────────────────────

@app.get("/api/snapshot")
async def snapshot():
    return {
        "tickers": market.tickers,
        "indicators": indicator_cache,
    }


@app.get("/api/alerts")
async def alerts(limit: int = 100):
    return get_recent_alerts(limit)


@app.get("/api/config")
async def get_config():
    return {"default": cfg.DEFAULT_SIGNAL_CONFIG, "per_ticker": signal_configs}


@app.post("/api/config")
async def update_config(body: dict):
    ticker = body.pop("ticker", None)
    if ticker:
        signal_configs[ticker] = {**cfg.DEFAULT_SIGNAL_CONFIG, **body}
    else:
        cfg.DEFAULT_SIGNAL_CONFIG.update(body)
    return {"ok": True}


@app.post("/api/watchlist")
async def add_ticker(body: dict):
    ticker = body.get("ticker", "").upper()
    if not ticker:
        raise HTTPException(400, "ticker required")
    if ticker not in market.tickers:
        market.tickers.append(ticker)
    return {"tickers": market.tickers}


@app.delete("/api/watchlist/{ticker}")
async def remove_ticker(ticker: str):
    ticker = ticker.upper()
    if ticker in market.tickers:
        market.tickers.remove(ticker)
    return {"tickers": market.tickers}


# ── WebSocket ─────────────────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    ws_clients.append(ws)
    # Send current snapshot immediately on connect
    await ws.send_text(json.dumps({"type": "SNAPSHOT", "data": {
        "tickers": market.tickers,
        "indicators": indicator_cache,
    }}))
    try:
        while True:
            await ws.receive_text()  # keep alive; client can send pings
    except WebSocketDisconnect:
        if ws in ws_clients:
            ws_clients.remove(ws)


# ── Static frontend ───────────────────────────────────────────────────────────

frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

    @app.get("/")
    async def serve_frontend():
        return FileResponse(os.path.join(frontend_path, "index.html"))
