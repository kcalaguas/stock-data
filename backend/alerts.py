"""Email alert dispatcher. Falls back silently if SMTP is not configured."""
import asyncio
import logging
import aiosmtplib
from email.message import EmailMessage
from config import ALERT_EMAIL_ENABLED, SMTP_USER, SMTP_PASSWORD, ALERT_TO_EMAIL

log = logging.getLogger(__name__)

# Cooldown: don't re-fire the same signal for the same ticker within N seconds
_cooldown: dict[str, float] = {}
COOLDOWN_SECONDS = 300


def _key(ticker: str, signal_type: str) -> str:
    return f"{ticker}:{signal_type}"


def is_cooled_down(ticker: str, signal_type: str) -> bool:
    import time
    k = _key(ticker, signal_type)
    last = _cooldown.get(k, 0)
    if time.time() - last < COOLDOWN_SECONDS:
        return False
    _cooldown[k] = time.time()
    return True


async def send_email_alert(signal: dict):
    if not ALERT_EMAIL_ENABLED or not SMTP_USER:
        return
    try:
        msg = EmailMessage()
        msg["From"] = SMTP_USER
        msg["To"] = ALERT_TO_EMAIL
        ticker = signal["ticker"]
        sig = signal["signal_type"]
        direction = signal["direction"]
        price = signal["price"]
        msg["Subject"] = f"[{direction}] {ticker} — {sig} @ ${price}"
        msg.set_content(
            f"Signal fired: {sig}\n"
            f"Ticker: {ticker}\n"
            f"Direction: {direction}\n"
            f"Price: ${price}\n"
            f"Indicator value: {signal.get('indicator_value')}\n"
            f"Details: {signal.get('extra')}\n"
        )
        await aiosmtplib.send(
            msg,
            hostname="smtp.gmail.com",
            port=587,
            start_tls=True,
            username=SMTP_USER,
            password=SMTP_PASSWORD,
        )
        log.info("Email alert sent for %s %s", ticker, sig)
    except Exception as e:
        log.error("Email send failed: %s", e)
