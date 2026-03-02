from __future__ import annotations

import pandas as pd


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    frame = df.copy()

    typical_price = (frame["high"] + frame["low"] + frame["close"]) / 3
    frame["vwap"] = (typical_price * frame["volume"]).cumsum() / frame["volume"].cumsum().clip(lower=1)

    frame["ema20"] = frame["close"].ewm(span=20, adjust=False).mean()
    frame["ema50"] = frame["close"].ewm(span=50, adjust=False).mean()

    delta = frame["close"].diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)
    avg_gain = gains.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
    avg_loss = losses.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    frame["rsi"] = 100 - (100 / (1 + rs))
    frame["rsi"] = frame["rsi"].fillna(50)

    ema12 = frame["close"].ewm(span=12, adjust=False).mean()
    ema26 = frame["close"].ewm(span=26, adjust=False).mean()
    frame["macd"] = ema12 - ema26
    frame["macd_signal"] = frame["macd"].ewm(span=9, adjust=False).mean()

    frame["avg_volume20"] = frame["volume"].rolling(20).mean().fillna(method="bfill")
    frame["volume_spike"] = frame["volume"] > (1.5 * frame["avg_volume20"])

    frame["swing_high"] = frame["high"][
        (frame["high"] > frame["high"].shift(1)) & (frame["high"] > frame["high"].shift(-1))
    ]
    frame["swing_low"] = frame["low"][
        (frame["low"] < frame["low"].shift(1)) & (frame["low"] < frame["low"].shift(-1))
    ]

    frame["bullish_engulfing"] = (
        (frame["close"].shift(1) < frame["open"].shift(1))
        & (frame["close"] > frame["open"])
        & (frame["open"] <= frame["close"].shift(1))
        & (frame["close"] >= frame["open"].shift(1))
    )
    frame["bearish_engulfing"] = (
        (frame["close"].shift(1) > frame["open"].shift(1))
        & (frame["close"] < frame["open"])
        & (frame["open"] >= frame["close"].shift(1))
        & (frame["close"] <= frame["open"].shift(1))
    )

    return frame


def latest_support_resistance(df: pd.DataFrame) -> tuple[float, float]:
    recent = df.tail(80)
    support = recent["swing_low"].dropna().tail(5)
    resistance = recent["swing_high"].dropna().tail(5)

    support_value = float(support.mean()) if not support.empty else float(recent["low"].min())
    resistance_value = float(resistance.mean()) if not resistance.empty else float(recent["high"].max())

    return support_value, resistance_value
