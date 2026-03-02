from __future__ import annotations

import json
import os
from datetime import UTC, datetime, time

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.analysis import AnalysisConfig, analyze_intraday
from app.db import fetch_history, init_db, insert_history
from app.groww_client import GrowwAPIError, GrowwClient
from app.models import AnalyzeRequest, AnalyzeResponse, HistoryRecord

app = FastAPI(title="Groww Intraday Analyzer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

GROWW_BASE_URL = os.getenv("GROWW_BASE_URL", "https://api.groww.in")
client = GrowwClient(GROWW_BASE_URL)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/")
def index() -> FileResponse:
    return FileResponse("static/index.html")


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(payload: AnalyzeRequest) -> dict:
    now = datetime.now(UTC)
    start_of_day = datetime.combine(now.date(), time.min, tzinfo=UTC)

    try:
        df_selected = await client.fetch_candles(
            symbol=payload.stock,
            interval=payload.timeframe,
            start_ts=start_of_day,
            end_ts=now,
            api_key=payload.api_key,
        )
        # always pull 1m for sharper breakout/volume context
        df_one = await client.fetch_candles(
            symbol=payload.stock,
            interval="1m",
            start_ts=start_of_day,
            end_ts=now,
            api_key=payload.api_key,
        )
    except GrowwAPIError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    analysis = analyze_intraday(df_selected, AnalysisConfig(mode=payload.mode))
    analysis_one = analyze_intraday(df_one, AnalysisConfig(mode=payload.mode))

    analysis["plan"]["confidence"] = int((analysis["plan"]["confidence"] * 0.7) + (analysis_one["plan"]["confidence"] * 0.3))

    response = {
        "stock": payload.stock.upper(),
        "timeframe": payload.timeframe,
        "mode": payload.mode,
        "generated_at": now,
        "latest_price": analysis["latest_price"],
        "indicators": analysis["indicators"],
        "plan": analysis["plan"],
    }

    chart_candles = [
        {
            "time": int(ts.timestamp()),
            "open": float(o),
            "high": float(h),
            "low": float(l),
            "close": float(c),
        }
        for ts, o, h, l, c in zip(
            df_selected["timestamp"],
            df_selected["open"],
            df_selected["high"],
            df_selected["low"],
            df_selected["close"],
        )
    ]

    insert_history(
        {
            "stock": response["stock"],
            "timeframe": response["timeframe"],
            "mode": response["mode"],
            "signal": response["plan"]["signal"],
            "confidence": response["plan"]["confidence"],
            "trend": response["plan"]["trend"],
            "latest_price": response["latest_price"],
            "payload_json": json.dumps({"response": response, "candles": chart_candles}),
        }
    )

    return {**response, "indicators": {**response["indicators"], "candles": chart_candles}}


@app.get("/api/history", response_model=list[HistoryRecord])
def history(limit: int = 20) -> list[dict]:
    return fetch_history(limit)
