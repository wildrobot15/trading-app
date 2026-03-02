from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from app.indicators import compute_indicators, latest_support_resistance


@dataclass
class StrategyResult:
    trend: str
    signal: str
    confidence: float
    reasons: list[str]
    levels: dict
    indicators: dict


def analyze(frame: pd.DataFrame, mode: str) -> StrategyResult:
    df = compute_indicators(frame)
    last = df.iloc[-1]
    prev = df.iloc[-2]
    support, resistance = latest_support_resistance(df)

    above_vwap = last.close > last.vwap
    ema_bull = last.ema20 > last.ema50
    ema_bear = last.ema20 < last.ema50
    macd_bull_cross = prev.macd <= prev.macd_signal and last.macd > last.macd_signal
    macd_bear_cross = prev.macd >= prev.macd_signal and last.macd < last.macd_signal
    breakout = last.close > resistance * 1.001
    breakdown = last.close < support * 0.999

    bullish_checks = {
        "Price above VWAP": above_vwap,
        "20 EMA > 50 EMA": ema_bull,
        "RSI in bullish zone": 50 <= last.rsi <= 70,
        "Volume spike on breakout": bool(last.volume_spike and breakout),
        "Bullish engulfing": bool(last.bullish_engulfing),
        "MACD bullish crossover": bool(macd_bull_cross),
    }

    bearish_checks = {
        "Price below VWAP": not above_vwap,
        "20 EMA < 50 EMA": ema_bear,
        "RSI in bearish zone": 30 <= last.rsi <= 50,
        "Breakdown below support": bool(breakdown),
        "Bearish engulfing": bool(last.bearish_engulfing),
        "MACD bearish crossover": bool(macd_bear_cross),
    }

    bull_score = sum(bullish_checks.values())
    bear_score = sum(bearish_checks.values())

    if bull_score >= 4 and bull_score > bear_score:
        signal = "BUY"
        trend = "Bullish"
        reasons = [name for name, ok in bullish_checks.items() if ok]
    elif bear_score >= 4 and bear_score > bull_score:
        signal = "SELL"
        trend = "Bearish"
        reasons = [name for name, ok in bearish_checks.items() if ok]
    else:
        signal = "WAIT"
        trend = "Sideways"
        reasons = ["Mixed signals; waiting for cleaner setup"]

    mode_multiplier = 1.2 if mode == "aggressive" else 1.0
    risk_buffer = (last.close * (0.004 if mode == "aggressive" else 0.007))

    if signal == "BUY":
        entry = float(last.close)
        stop = float(max(support, entry - risk_buffer))
        risk = max(entry - stop, 0.1)
        t1 = entry + (risk * 1.5 * mode_multiplier)
        t2 = entry + (risk * 2.5 * mode_multiplier)
        rr = (t2 - entry) / risk
        levels = {
            "best_buy_entry": round(entry, 2),
            "best_sell_entry": None,
            "stop_loss": round(stop, 2),
            "target_1": round(t1, 2),
            "target_2": round(t2, 2),
            "risk_reward_ratio": f"1:{rr:.2f}",
        }
    elif signal == "SELL":
        entry = float(last.close)
        stop = float(min(resistance, entry + risk_buffer))
        risk = max(stop - entry, 0.1)
        t1 = entry - (risk * 1.5 * mode_multiplier)
        t2 = entry - (risk * 2.5 * mode_multiplier)
        rr = (entry - t2) / risk
        levels = {
            "best_buy_entry": None,
            "best_sell_entry": round(entry, 2),
            "stop_loss": round(stop, 2),
            "target_1": round(t1, 2),
            "target_2": round(t2, 2),
            "risk_reward_ratio": f"1:{rr:.2f}",
        }
    else:
        levels = {
            "best_buy_entry": round(float(last.close), 2),
            "best_sell_entry": round(float(last.close), 2),
            "stop_loss": round(float(support), 2),
            "target_1": round(float(resistance), 2),
            "target_2": round(float(resistance * 1.01), 2),
            "risk_reward_ratio": "1:1.00",
        }

    raw_confidence = max(bull_score, bear_score) / 6 * 100
    confidence = min(95.0, raw_confidence + (5 if signal != "WAIT" else 0))

    indicators = {
        "close": round(float(last.close), 2),
        "vwap": round(float(last.vwap), 2),
        "ema20": round(float(last.ema20), 2),
        "ema50": round(float(last.ema50), 2),
        "rsi14": round(float(last.rsi), 2),
        "macd": round(float(last.macd), 4),
        "macd_signal": round(float(last.macd_signal), 4),
        "support": round(float(support), 2),
        "resistance": round(float(resistance), 2),
        "volume_spike": bool(last.volume_spike),
        "breakout": bool(breakout),
        "breakdown": bool(breakdown),
    }

    return StrategyResult(
        trend=trend,
        signal=signal,
        confidence=round(confidence, 1),
        reasons=reasons,
        levels=levels,
        indicators=indicators,
    )
