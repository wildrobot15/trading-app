from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.analysis import analyze
from app.database import HistoryRepository
from app.groww_client import GrowwAPIError, GrowwClient
from app.models import AnalysisResponse, AnalyzeRequest, ApiKeyRequest, Candle, HistoryRecord

load_dotenv()

app = FastAPI(title="Intraday Signal Engine", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

client = GrowwClient(
    base_url=os.getenv("GROWW_BASE_URL", "https://api.groww.in"),
    candle_path=os.getenv("GROWW_CANDLE_PATH", "/v1/market/candles/intraday"),
    timeout=int(os.getenv("GROWW_REQUEST_TIMEOUT", "10")),
    mock_mode=os.getenv("GROWW_MOCK_MODE", "true").lower() == "true",
)
repo = HistoryRepository(os.getenv("DATABASE_URL", "sqlite:///./analysis_history.db"))
session_keys: dict[str, str] = {}


@app.get("/")
async def root() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/configure-key")
async def configure_key(payload: ApiKeyRequest):
    session_keys[payload.client_id] = payload.api_key.strip()
    return {"message": "API key stored in backend session."}


@app.post("/api/analyze", response_model=AnalysisResponse)
async def run_analysis(payload: AnalyzeRequest):
    key = session_keys.get(payload.client_id)
    if not key:
        raise HTTPException(status_code=400, detail="API key not configured for this client_id")

    try:
        candles_df = await client.fetch_intraday(payload.symbol, payload.timeframe, key)
    except GrowwAPIError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unexpected failure: {exc}") from exc

    result = analyze(candles_df, payload.mode)
    repo.insert(payload.symbol.upper(), payload.timeframe, payload.mode, result.signal, result.trend, result.confidence)

    candles = [
        Candle(
            timestamp=row.timestamp.to_pydatetime(),
            open=float(row.open),
            high=float(row.high),
            low=float(row.low),
            close=float(row.close),
            volume=float(row.volume),
        )
        for row in candles_df.tail(200).itertuples()
    ]

    return AnalysisResponse(
        stock=payload.symbol.upper(),
        timeframe=payload.timeframe,
        mode=payload.mode,
        trend=result.trend,
        confidence=result.confidence,
        signal=result.signal,
        levels=result.levels,
        reason=result.reasons,
        indicators=result.indicators,
        candles=candles,
    )


@app.get("/api/history", response_model=list[HistoryRecord])
async def history(limit: int = 20):
    rows = repo.latest(limit=limit)
    return rows
