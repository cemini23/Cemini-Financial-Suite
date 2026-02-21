from sqlalchemy import Column, Integer, Float, String, DateTime
from datetime import datetime
from app.core.database import Base

class BTCHarvest(Base):
    __tablename__ = "btc_harvest"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    price = Column(Float)
    volume = Column(Float)
    rsi = Column(Float)
    vwap = Column(Float)
    adx = Column(Float)

class SignalLog(Base):
    __tablename__ = "signal_log"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    module = Column(String) # Weather, Musk, or BTC
    signal = Column(String)
    confidence = Column(Float)
    logic = Column(String)
