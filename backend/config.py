import os
from dotenv import load_dotenv

load_dotenv()

ALPACA_API_KEY = os.getenv("ALPACA_API_KEY", "")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY", "")
ALPACA_LIVE = os.getenv("ALPACA_LIVE", "false").lower() == "true"

WATCHLIST: list[str] = [
    t.strip().upper()
    for t in os.getenv("WATCHLIST", "AAPL,MSFT,NVDA,SPY,QQQ").split(",")
    if t.strip()
]

# Alert thresholds — can be overridden per-ticker via the API
DEFAULT_SIGNAL_CONFIG = {
    "rsi_oversold": 30,       # RSI below this → buy signal
    "rsi_overbought": 70,     # RSI above this → sell signal
    "macd_cross": True,       # fire on MACD histogram sign change
    "ema_cross": True,        # fire on 9/21 EMA crossover
    "volume_spike_mult": 2.0, # volume > N × 20-bar avg → spike alert
    "bb_squeeze_pct": 0.02,   # Bollinger Band width < 2% of price → squeeze
}

ALERT_EMAIL_ENABLED = os.getenv("ALERT_EMAIL_ENABLED", "false").lower() == "true"
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
ALERT_TO_EMAIL = os.getenv("ALERT_TO_EMAIL", SMTP_USER)

PORT = int(os.getenv("PORT", "8000"))
