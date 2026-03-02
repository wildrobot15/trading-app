from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class AnalysisConfig:
    mode: str = "conservative"


def _ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _macd(close: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
    macd_line = _ema(close, 12) - _ema(close, 26)
    signal = _ema(macd_line, 9)
    hist = macd_line - signal
    return macd_line, signal, hist


def _vwap(df: pd.DataFrame) -> pd.Series:
    pv = (df["close"] * df["volume"]).cumsum()
    return pv / df["volume"].cumsum().replace(0, np.nan)


def _engulfing(df: pd.DataFrame) -> tuple[bool, bool]:
    if len(df) < 2:
        return False, False
    prev = df.iloc[-2]
    curr = df.iloc[-1]

    prev_bear = prev["close"] < prev["open"]
    prev_bull = prev["close"] > prev["open"]
    curr_bull = curr["close"] > curr["open"]
    curr_bear = curr["close"] < curr["open"]

    bullish = prev_bear and curr_bull and curr["close"] > prev["open"] and curr["open"] < prev["close"]
    bearish = prev_bull and curr_bear and curr["open"] > prev["close"] and curr["close"] < prev["open"]
    return bullish, bearish


def _swing_levels(df: pd.DataFrame, lookback: int = 20) -> tuple[float, float]:
    window = df.tail(lookback)
    return float(window["low"].min()), float(window["high"].max())


def analyze_intraday(df: pd.DataFrame, config: AnalysisConfig) -> dict:
    data = df.copy()
    data["ema20"] = _ema(data["close"], 20)
    data["ema50"] = _ema(data["close"], 50)
    data["rsi14"] = _rsi(data["close"], 14)
    macd_line, macd_signal, macd_hist = _macd(data["close"])
    data["macd"] = macd_line
    data["macd_signal"] = macd_signal
    data["macd_hist"] = macd_hist
    data["vwap"] = _vwap(data)
    data["vol_avg20"] = data["volume"].rolling(20).mean()

    latest = data.iloc[-1]
    support, resistance = _swing_levels(data)
    bullish_engulfing, bearish_engulfing = _engulfing(data)

    volume_spike = bool(latest["volume"] > (latest["vol_avg20"] * 1.5 if not pd.isna(latest["vol_avg20"]) else np.inf))
    breakout_up = bool(latest["close"] > resistance * 1.001)
    breakdown = bool(latest["close"] < support * 0.999)

    buy_rules = {
        "price_above_vwap": latest["close"] > latest["vwap"],
        "ema_bullish": latest["ema20"] > latest["ema50"],
        "rsi_in_buy_zone": 50 <= latest["rsi14"] <= 70,
        "volume_breakout": volume_spike and breakout_up,
        "bullish_pattern": bullish_engulfing,
    }

    sell_rules = {
        "price_below_vwap": latest["close"] < latest["vwap"],
        "ema_bearish": latest["ema20"] < latest["ema50"],
        "rsi_in_sell_zone": 30 <= latest["rsi14"] <= 50,
        "breakdown_support": breakdown,
        "bearish_pattern": bearish_engulfing,
    }

    threshold = 3 if config.mode == "aggressive" else 4
    buy_score = sum(buy_rules.values())
    sell_score = sum(sell_rules.values())

    if buy_score >= threshold and buy_score > sell_score:
        signal = "BUY"
        trend = "Bullish"
        entry = float(latest["close"])
        stop_loss = min(support, entry * 0.994)
        risk = entry - stop_loss
        t1 = entry + risk * 1.5
        t2 = entry + risk * 2.5
        best_buy, best_sell = entry, None
        chosen_rules = buy_rules
    elif sell_score >= threshold and sell_score > buy_score:
        signal = "SELL"
        trend = "Bearish"
        entry = float(latest["close"])
        stop_loss = max(resistance, entry * 1.006)
        risk = stop_loss - entry
        t1 = entry - risk * 1.5
        t2 = entry - risk * 2.5
        best_buy, best_sell = None, entry
        chosen_rules = sell_rules
    else:
        signal = "HOLD"
        trend = "Sideways"
        best_buy = best_sell = stop_loss = t1 = t2 = None
        chosen_rules = {}

    confidence = int(min(100, max(buy_score, sell_score) / 5 * 100))

    rationale = [f"{k.replace('_', ' ').title()}: {'✅' if v else '❌'}" for k, v in (chosen_rules or buy_rules).items()]
    if signal == "HOLD":
        rationale.append("Signal mixed; waiting for stronger confirmation.")

    rr = None
    if signal in {"BUY", "SELL"} and stop_loss is not None and t2 is not None:
        reward = abs(t2 - (best_buy if signal == "BUY" else best_sell))
        risk = abs((best_buy if signal == "BUY" else best_sell) - stop_loss)
        rr = f"1:{reward / risk:.2f}" if risk else None

    return {
        "latest_price": round(float(latest["close"]), 2),
        "indicators": {
            "vwap": round(float(latest["vwap"]), 2),
            "ema20": round(float(latest["ema20"]), 2),
            "ema50": round(float(latest["ema50"]), 2),
            "rsi14": round(float(latest["rsi14"]), 2),
            "macd": round(float(latest["macd"]), 4),
            "macd_signal": round(float(latest["macd_signal"]), 4),
            "macd_hist": round(float(latest["macd_hist"]), 4),
            "support": round(support, 2),
            "resistance": round(resistance, 2),
            "volume_spike": volume_spike,
            "bullish_engulfing": bullish_engulfing,
            "bearish_engulfing": bearish_engulfing,
            "breakout_up": breakout_up,
            "breakdown": breakdown,
        },
        "plan": {
            "signal": signal,
            "trend": trend,
            "confidence": confidence,
            "best_buy": round(best_buy, 2) if best_buy else None,
            "best_sell": round(best_sell, 2) if best_sell else None,
            "stop_loss": round(stop_loss, 2) if stop_loss else None,
            "target_1": round(t1, 2) if t1 else None,
            "target_2": round(t2, 2) if t2 else None,
            "risk_reward": rr,
            "rationale": rationale,
        },
    }
