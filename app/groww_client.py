from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

import httpx
import pandas as pd


class GrowwAPIError(Exception):
    pass


class GrowwClient:
    def __init__(self, base_url: str, candle_path: str, timeout: int = 10, mock_mode: bool = True):
        self.base_url = base_url.rstrip("/")
        self.candle_path = candle_path
        self.timeout = timeout
        self.mock_mode = mock_mode

    async def fetch_intraday(self, symbol: str, timeframe: str, api_key: str) -> pd.DataFrame:
        if self.mock_mode:
            return self._mock_data(symbol, timeframe)

        params = {
            "symbol": symbol.upper(),
            "interval": timeframe,
            "session": "today",
        }
        headers = {"Authorization": f"Bearer {api_key}"}
        url = f"{self.base_url}{self.candle_path}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, params=params, headers=headers)

        if response.status_code >= 400:
            raise GrowwAPIError(f"Groww API returned {response.status_code}: {response.text}")

        payload = response.json()
        candles = payload.get("candles") or payload.get("data") or []
        if not candles:
            raise GrowwAPIError("No candle data returned for symbol")

        frame = pd.DataFrame(candles)
        rename_map = {
            "t": "timestamp",
            "o": "open",
            "h": "high",
            "l": "low",
            "c": "close",
            "v": "volume",
        }
        frame = frame.rename(columns=rename_map)
        required = ["timestamp", "open", "high", "low", "close", "volume"]
        if not set(required).issubset(frame.columns):
            raise GrowwAPIError("Groww response missing required candle fields")

        frame = frame[required]
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
        for col in ["open", "high", "low", "close", "volume"]:
            frame[col] = pd.to_numeric(frame[col], errors="coerce")
        frame = frame.dropna().sort_values("timestamp")

        if frame.empty:
            raise GrowwAPIError("Candle data became empty after cleaning")
        return frame

    def _mock_data(self, symbol: str, timeframe: str) -> pd.DataFrame:
        mins = {"1m": 1, "5m": 5, "15m": 15}[timeframe]
        count = int(390 / mins)
        start = datetime.now(timezone.utc).replace(hour=3, minute=45, second=0, microsecond=0)
        rows = []
        base = 2450 + (sum(ord(ch) for ch in symbol.upper()) % 80)
        for i in range(count):
            ts = start + timedelta(minutes=i * mins)
            drift = 0.12 * i
            wave = 6 * math.sin(i / 7)
            close = base + drift + wave
            open_ = close - math.sin(i / 4)
            high = max(open_, close) + 2.1
            low = min(open_, close) - 2.1
            volume = 9000 + int(abs(math.sin(i / 3)) * 6000) + (22000 if i % 40 == 0 else 0)
            rows.append(
                {
                    "timestamp": ts,
                    "open": round(open_, 2),
                    "high": round(high, 2),
                    "low": round(low, 2),
                    "close": round(close, 2),
                    "volume": volume,
                }
            )
        return pd.DataFrame(rows)
