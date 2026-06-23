# Stock Signal Dashboard

A real-time stock technical analysis dashboard with WebSocket-pushed signals.

## Features

- **Live data** via Alpaca Markets WebSocket (free tier = 15-min delayed; real-time with a free brokerage account)
- **Demo mode** — runs with synthetic data if no API keys are set
- **Indicators**: RSI(14), MACD(12/26/9), EMA 9/21/50/200, Bollinger Bands(20,2), Volume spikes
- **Signals**: RSI oversold/overbought, MACD histogram cross, EMA 9/21 crossover, BB touches, BB squeeze, volume spike
- **Alert history** persisted in SQLite
- **Optional email alerts** via Gmail SMTP
- Per-ticker signal threshold overrides via REST API

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — at minimum set your WATCHLIST
# Add Alpaca keys for live/delayed data; leave blank for demo mode
```

### 3. Run

```bash
cd backend
python run.py
```

Open **http://localhost:8000**

## Getting Alpaca Keys (Free)

1. Sign up at https://alpaca.markets (no credit card)
2. Go to **Paper Trading → API Keys → Generate**
3. Paste into `.env` as `ALPACA_API_KEY` and `ALPACA_SECRET_KEY`
4. For real-time data (not 15-min delayed), open a free live brokerage account and set `ALPACA_LIVE=true`

## Signal Reference

| Signal | Direction | Trigger |
|---|---|---|
| `RSI_OVERSOLD` | BUY | RSI < 30 |
| `RSI_OVERBOUGHT` | SELL | RSI > 70 |
| `MACD_CROSS_BULL` | BUY | MACD histogram crosses above 0 |
| `MACD_CROSS_BEAR` | SELL | MACD histogram crosses below 0 |
| `EMA9_CROSS_ABOVE_21` | BUY | EMA(9) crosses above EMA(21) |
| `EMA9_CROSS_BELOW_21` | SELL | EMA(9) crosses below EMA(21) |
| `BB_LOWER_TOUCH` | BUY | Price <= lower Bollinger Band |
| `BB_UPPER_TOUCH` | SELL | Price >= upper Bollinger Band |
| `BB_SQUEEZE` | INFO | BB width < 2% of price (volatility compression) |
| `VOLUME_SPIKE` | INFO | Volume > 2x 20-bar average |

## Adjust Thresholds

```bash
# Change RSI thresholds globally
curl -X POST http://localhost:8000/api/config \
  -H "Content-Type: application/json" \
  -d '{"rsi_oversold": 25, "rsi_overbought": 75}'

# Override for a specific ticker
curl -X POST http://localhost:8000/api/config \
  -H "Content-Type: application/json" \
  -d '{"ticker": "NVDA", "rsi_oversold": 35, "volume_spike_mult": 3.0}'
```

## API Reference

| Method | Path | Description |
|---|---|---|
| GET | `/api/snapshot` | Latest indicators for all tickers |
| GET | `/api/alerts?limit=100` | Recent signal history |
| POST | `/api/watchlist` | Add ticker {"ticker":"TSLA"} |
| DELETE | `/api/watchlist/{ticker}` | Remove ticker |
| GET | `/api/config` | Current thresholds |
| POST | `/api/config` | Update thresholds |
| WS | `/ws` | Real-time push stream |

## WebSocket Message Types

```json
{"type": "SNAPSHOT", "data": {"tickers": [...], "indicators": {...}}}
{"type": "TICK",     "ticker": "AAPL", "data": {<indicators>}}
{"type": "SIGNAL",   "data": {"ticker":"AAPL","signal_type":"RSI_OVERSOLD","direction":"BUY","price":182.5}}
```

## Quant Notes

**Swing trading (2-10 days)**: RSI(14) + MACD histogram cross + volume confirmation is the most reliable combo. Avoid acting on BB alone in trending markets.

**Long-term holds**: Watch the EMA 50/200 crossover ("golden cross" / "death cross"). Fires rarely but has strong historical significance.

**False signal reduction**: Signals have a 5-min cooldown per ticker per signal type. For fewer false positives, require confluence: e.g., only act on MACD_CROSS_BULL when RSI is also below 50.
