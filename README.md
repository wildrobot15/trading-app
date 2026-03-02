# Groww Intraday Trading Analyzer (FastAPI + JS)

Python-based web app that connects to Groww candle API and suggests intraday BUY/SELL entries.

## Features

- FastAPI backend + lightweight HTML/JS frontend
- Uses Groww candle data for **1m**, **5m**, and **15m** intervals
- Indicator engine:
  - Support & Resistance (recent swing highs/lows)
  - VWAP
  - EMA 20 / EMA 50
  - RSI (14)
  - MACD crossover components
  - Volume spike detection
  - Bullish/Bearish engulfing
  - Breakout/breakdown detection
- Trade plan output:
  - Best Buy / Best Sell
  - Stop Loss
  - Target 1 and Target 2
  - Risk:Reward ratio
  - Trend and confidence score
- Refreshes analysis every 60 seconds
- Aggressive / Conservative modes
- SQLite history logging (`analysis_history.db`)

## Project Structure

- `app/main.py`: API + static hosting
- `app/groww_client.py`: Groww HTTP integration
- `app/analysis.py`: indicator + decision logic
- `app/db.py`: history persistence
- `static/index.html`: UI + chart + result cards

## Setup

1. Create venv and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Configure environment:

```bash
cp .env.example .env
# Edit GROWW_BASE_URL if your account uses a different domain/route
```

3. Run app:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4. Open:

- `http://localhost:8000`

## API Endpoints

- `POST /api/analyze`
- `GET /api/history?limit=20`

### Example Request

```json
{
  "api_key": "YOUR_DAILY_GROWW_KEY",
  "stock": "RELIANCE",
  "timeframe": "5m",
  "mode": "conservative"
}
```

## Decision Logic Summary

### BUY signal checklist

- Price > VWAP
- EMA20 > EMA50
- RSI in 50-70
- Volume spike + breakout above resistance
- Bullish engulfing confirmation

### SELL signal checklist

- Price < VWAP
- EMA20 < EMA50
- RSI in 30-50
- Breakdown below support
- Bearish engulfing confirmation

`conservative` requires stronger confirmation than `aggressive`.

## Notes on Groww API integration

- API key is entered from UI daily and sent only to backend API endpoint.
- Backend forwards key as Bearer token to Groww candle endpoint.
- If your Groww endpoint path differs, adjust `GrowwClient.fetch_candles` endpoint.
- Invalid stock or expired key errors are surfaced with clear messages.

## Security

- `.env` is ignored from git
- API key is not stored in database logs (only derived analysis result is stored)

