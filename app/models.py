from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class Candle(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class AnalyzeRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20)
    timeframe: Literal["1m", "5m", "15m"] = "1m"
    mode: Literal["aggressive", "conservative"] = "conservative"
    client_id: str = Field(..., min_length=3, max_length=128)


class ApiKeyRequest(BaseModel):
    client_id: str = Field(..., min_length=3, max_length=128)
    api_key: str = Field(..., min_length=8, max_length=256)


class SignalLevels(BaseModel):
    best_buy_entry: Optional[float] = None
    best_sell_entry: Optional[float] = None
    stop_loss: float
    target_1: float
    target_2: float
    risk_reward_ratio: str


class AnalysisResponse(BaseModel):
    stock: str
    timeframe: str
    mode: str
    trend: Literal["Bullish", "Bearish", "Sideways"]
    confidence: float
    signal: Literal["BUY", "SELL", "WAIT"]
    levels: SignalLevels
    reason: list[str]
    indicators: dict
    candles: list[Candle]


class HistoryRecord(BaseModel):
    id: int
    symbol: str
    timeframe: str
    mode: str
    signal: str
    trend: str
    confidence: float
    created_at: datetime
