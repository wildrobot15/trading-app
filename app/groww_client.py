from __future__ import annotations

from datetime import datetime

import httpx
import pandas as pd


class GrowwAPIError(Exception):
    pass


class GrowwClient:
    """
    Thin integration wrapper around Groww candle endpoint.
    Adjust GROWW_CANDLE_ENDPOINT env var if your account uses a different route.
    """

    def __init__(self, base_url: str, timeout: int = 15) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def fetch_candles(
        self,
        *,
        symbol: str,
        interval: str,
        start_ts: datetime,
        end_ts: datetime,
        api_key: str,
    ) -> pd.DataFrame:
        endpoint = f"{self.base_url}/v1/market/candles"
        params = {
            "symbol": symbol.upper(),
            "interval": interval,
            "from": int(start_ts.timestamp()),
            "to": int(end_ts.timestamp()),
        }
        headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(endpoint, params=params, headers=headers)

        if response.status_code == 401:
            raise GrowwAPIError("Authentication failed. Your Groww API key may be expired.")
        if response.status_code == 404:
            raise GrowwAPIError(f"Symbol {symbol} not found on Groww.")
        if response.status_code >= 400:
            raise GrowwAPIError(f"Groww API error ({response.status_code}): {response.text[:150]}")

        payload = response.json()
        candles = payload.get("candles") or payload.get("data", {}).get("candles")
        if not candles:
            raise GrowwAPIError("No candle data returned from Groww for this symbol/timeframe.")

        frame = pd.DataFrame(candles)
        expected = ["timestamp", "open", "high", "low", "close", "volume"]

        if list(frame.columns[:6]) != expected:
            if all(k in frame.columns for k in expected):
                frame = frame[expected]
            else:
                raise GrowwAPIError(
                    "Unexpected candle schema from Groww. Expected keys: timestamp, open, high, low, close, volume"
                )

        frame["timestamp"] = pd.to_datetime(frame["timestamp"], unit="s", utc=True)
        for col in ["open", "high", "low", "close", "volume"]:
            frame[col] = pd.to_numeric(frame[col], errors="coerce")

        frame = frame.dropna().sort_values("timestamp").reset_index(drop=True)
        if frame.empty:
            raise GrowwAPIError("Candle dataset is empty after validation.")
        return frame
