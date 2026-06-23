from datetime import datetime
from sqlalchemy import create_engine, Column, String, Float, DateTime, JSON, Integer
from sqlalchemy.orm import DeclarativeBase, Session

engine = create_engine("sqlite:///./stock_signals.db", connect_args={"check_same_thread": False})


class Base(DeclarativeBase):
    pass


class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String, index=True)
    signal_type = Column(String)   # e.g. "RSI_OVERSOLD", "MACD_CROSS_BULL"
    direction = Column(String)     # "BUY" | "SELL" | "INFO"
    price = Column(Float)
    indicator_value = Column(Float, nullable=True)
    fired_at = Column(DateTime, default=datetime.utcnow)
    extra = Column(JSON, nullable=True)


class WatchlistEntry(Base):
    __tablename__ = "watchlist"
    ticker = Column(String, primary_key=True)
    signal_config = Column(JSON, nullable=True)  # per-ticker overrides
    added_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(engine)


def get_session() -> Session:
    return Session(engine)


def save_alert(ticker: str, signal_type: str, direction: str, price: float,
               indicator_value: float | None = None, extra: dict | None = None):
    with get_session() as s:
        s.add(Alert(ticker=ticker, signal_type=signal_type, direction=direction,
                    price=price, indicator_value=indicator_value, extra=extra))
        s.commit()


def get_recent_alerts(limit: int = 100) -> list[dict]:
    with get_session() as s:
        rows = s.query(Alert).order_by(Alert.fired_at.desc()).limit(limit).all()
        return [
            {
                "id": r.id, "ticker": r.ticker, "signal_type": r.signal_type,
                "direction": r.direction, "price": r.price,
                "indicator_value": r.indicator_value,
                "fired_at": r.fired_at.isoformat(),
            }
            for r in rows
        ]
