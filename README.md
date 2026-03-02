# Groww Intraday Signal Web App (FastAPI)

Python web app for intraday BUY/SELL suggestions using Groww candle data with chart visualization.

## Features
- FastAPI backend with analysis endpoint.
- Frontend (HTML + JS) using Lightweight Charts.
- Inputs for daily Groww API key, stock symbol, timeframe (1m/5m/15m), and mode (aggressive/conservative).
- Indicator engine:
  - VWAP
  - EMA 20 / EMA 50
  - RSI 14
  - MACD crossover
  - Volume spike detection
  - Bullish/Bearish engulfing
  - Support/Resistance from swing highs/lows
  - Breakout/Breakdown detection
- Trading output:
  - Best Buy / Best Sell
  - Stop loss
  - Target 1 / Target 2
  - Risk:Reward
  - Trend and confidence score
- Analysis history logging in SQLite.
- Auto-refresh every 60 seconds.

## Project structure

- `app/main.py` - FastAPI routes and app wiring.
- `app/groww_client.py` - Groww API integration + optional mock mode.
- `app/indicators.py` - indicator calculations.
- `app/analysis.py` - decision logic and price level calculations.
- `app/database.py` - SQLite analysis log repository.
- `static/` - frontend assets.

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy env file:

```bash
cp .env.example .env
```

4. Configure `.env`:

- `GROWW_MOCK_MODE=true` for local demo without live API.
- Set `GROWW_MOCK_MODE=false` and configure `GROWW_BASE_URL` + `GROWW_CANDLE_PATH` to your Groww endpoint for real data.

5. Run app:

```bash
uvicorn app.main:app --reload --port 8000
```

6. Open `http://localhost:8000`.

## How API key handling works

- User enters API key in UI daily.
- Key is sent once to `/api/configure-key`.
- Key is stored only in backend in-memory session map by `client_id`.
- `/api/analyze` uses stored key; key is not returned to frontend.

> In production, replace in-memory storage with secure server-side session storage (Redis/encrypted DB).

## Endpoints

- `POST /api/configure-key`
- `POST /api/analyze`
- `GET /api/history?limit=20`

## Notes for Groww integration

Groww response formats may vary by account/app entitlement. `app/groww_client.py` accepts either:
- `{"candles": [...]}` or
- `{"data": [...]}`

Each candle must provide fields that map to:
`timestamp/open/high/low/close/volume` (or compact keys `t/o/h/l/c/v`).

## Production suggestions
- Add authentication around API key configuration and analysis routes.
- Encrypt session keys at rest.
- Add retry + circuit breaker around Groww API calls.
- Add unit tests for indicator and strategy logic.
