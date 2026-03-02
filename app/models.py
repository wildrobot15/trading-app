from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


Timeframe = Literal["1m", "5m", "15m"]
Mode = Literal["aggressive", "conservative"]
Trend = Literal["Bullish", "Bearish", "Sideways"]
Signal = Literal["BUY", "SELL", "HOLD"]


class AnalyzeRequest(BaseModel):
    stock: str = Field(..., min_length=1, max_length=30, description="Ticker/symbol like RELIANCE")
    timeframe: Timeframe = "5m"
    mode: Mode = "conservative"
    api_key: str = Field(..., min_length=10, description="Groww API key (daily rotating)")


class TradePlan(BaseModel):
    signal: Signal
    trend: Trend
    confidence: int = Field(..., ge=0, le=100)
    best_buy: Optional[float] = None
    best_sell: Optional[float] = None
    stop_loss: Optional[float] = None
    target_1: Optional[float] = None
    target_2: Optional[float] = None
    risk_reward: Optional[str] = None
    rationale: list[str]


class AnalyzeResponse(BaseModel):
    stock: str
    timeframe: Timeframe
    mode: Mode
    generated_at: datetime
    latest_price: float
    indicators: dict
    plan: TradePlan


class HistoryRecord(BaseModel):
    id: int
    stock: str
    timeframe: Timeframe
    mode: Mode
    signal: Signal
    confidence: int
    trend: Trend
    latest_price: float
    created_at: datetime
