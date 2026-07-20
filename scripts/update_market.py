#!/usr/bin/env python3
"""Generate data/market.json using public Yahoo Finance price history via yfinance."""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "market.json"
WATCHLIST = [
    "SCHG", "MSFT", "AAPL", "AMZN", "GOOGL", "META", "NVDA", "AVGO", "TSM",
    "ASML", "V", "MA", "BRK-B", "LLY", "CEG", "VRT", "CRWD", "PANW", "COST",
    "PLTR", "AMD", "MRVL", "ANET", "ETN", "NOW", "TSLA", "RKLB", "TEM", "RXRX",
    "IONQ", "SNPS", "CDNS", "QUBT", "AMAT", "NFLX", "ORCL", "ISRG", "MU", "QCOM", "RBLX", "SNOW"
]
BENCHMARKS = ["SPY", "QQQ", "^VIX"]

@dataclass
class StockScore:
    symbol: str
    price: float
    change_percent: float
    score: float
    signal: str
    reason: str


def clamp(value: float, low: float = 0, high: float = 100) -> float:
    return max(low, min(high, value))


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        result = float(value)
        return default if math.isnan(result) or math.isinf(result) else result
    except (TypeError, ValueError):
        return default


def rsi(close: pd.Series, period: int = 14) -> float:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / loss.replace(0, float("nan"))
    value = 100 - (100 / (1 + rs))
    return safe_float(value.iloc[-1], 50)


def score_symbol(symbol: str, frame: pd.DataFrame) -> StockScore | None:
    frame = frame.dropna().copy()
    if len(frame) < 55:
        return None
    close = frame["Close"]
    price = safe_float(close.iloc[-1])
    previous = safe_float(close.iloc[-2], price)
    change = ((price / previous) - 1) * 100 if previous else 0
    ma20 = safe_float(close.rolling(20).mean().iloc[-1], price)
    ma50 = safe_float(close.rolling(50).mean().iloc[-1], price)
    momentum_20 = ((price / safe_float(close.iloc[-21], price)) - 1) * 100
    vol_20 = safe_float(close.pct_change().rolling(20).std().iloc[-1]) * math.sqrt(252) * 100
    rsi_value = rsi(close)

    trend_score = 50 + (20 if price > ma20 else -20) + (15 if ma20 > ma50 else -15)
    momentum_score = 50 + max(-25, min(25, momentum_20 * 2))
    rsi_score = 75 if 50 <= rsi_value <= 68 else 60 if 40 <= rsi_value < 50 else 45 if 68 < rsi_value <= 75 else 25
    volatility_score = 75 if vol_20 < 30 else 60 if vol_20 < 45 else 40 if vol_20 < 65 else 20
    total = clamp(.42 * trend_score + .28 * momentum_score + .18 * rsi_score + .12 * volatility_score)

    signal = "BUY" if total >= 68 else "HOLD" if total >= 45 else "SELL"
    reasons = []
    reasons.append("above 20- and 50-day averages" if price > ma20 > ma50 else "mixed moving-average trend")
    reasons.append(f"20-day momentum {momentum_20:+.1f}%")
    reasons.append(f"RSI {rsi_value:.0f}")
    return StockScore(symbol.replace("BRK-B", "BRK.B"), price, change, round(total, 1), signal, ", ".join(reasons))


def download_history(symbols: list[str]) -> dict[str, pd.DataFrame]:
    raw = yf.download(symbols, period="1y", interval="1d", group_by="ticker", auto_adjust=True, progress=False, threads=True)
    result: dict[str, pd.DataFrame] = {}
    if len(symbols) == 1:
        result[symbols[0]] = raw
    else:
        for symbol in symbols:
            try:
                result[symbol] = raw[symbol]
            except KeyError:
                continue
    return result


def benchmark_payload(symbol: str, frame: pd.DataFrame) -> dict[str, float]:
    close = frame["Close"].dropna()
    price = safe_float(close.iloc[-1])
    prev = safe_float(close.iloc[-2], price)
    return {"price": round(price, 2), "change_percent": round(((price / prev) - 1) * 100 if prev else 0, 2)}


def main() -> None:
    all_symbols = WATCHLIST + BENCHMARKS
    history = download_history(all_symbols)
    scored = [score_symbol(symbol, history[symbol]) for symbol in WATCHLIST if symbol in history]
    scored = [item for item in scored if item is not None]
    if not scored:
        raise RuntimeError("No watchlist data returned")

    counts = {"BUY": 0, "HOLD": 0, "SELL": 0}
    for item in scored:
        counts[item.signal] += 1
    total = len(scored)
    temperature = {key.lower(): round(value / total * 100) for key, value in counts.items()}
    drift = 100 - sum(temperature.values())
    temperature["hold"] += drift

    spy = benchmark_payload("SPY", history["SPY"])
    qqq = benchmark_payload("QQQ", history["QQQ"])
    vix = benchmark_payload("^VIX", history["^VIX"])
    score = round(sum(item.score for item in scored) / total)
    label = "Strong Bullish" if score >= 72 else "Bullish" if score >= 60 else "Neutral" if score >= 45 else "Defensive" if score >= 32 else "Strong Defensive"
    trend = "Bullish" if spy["price"] > safe_float(history["SPY"]["Close"].rolling(50).mean().iloc[-1]) else "Bearish"
    vix_status = "Calm" if vix["price"] < 17 else "Elevated" if vix["price"] < 25 else "High fear"

    candidates = sorted(scored, key=lambda item: item.score, reverse=True)[:12]
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "temperature": temperature,
        "market": {
            "score": score,
            "label": label,
            "summary": f"The watchlist is {temperature['buy']}% Buy, {temperature['hold']}% Hold and {temperature['sell']}% Sell based on trend, momentum and volatility.",
            "spy": spy,
            "qqq": qqq,
            "vix": {"price": vix["price"], "change_percent": vix["change_percent"], "status": vix_status},
            "trend": trend,
        },
        "candidates": [item.__dict__ for item in candidates],
        "starter_plan": [
            {"label": "Broad ETF", "percent": 60},
            {"label": "Growth ETF", "percent": 25},
            {"label": "Cash", "percent": 15},
        ],
        "disclaimer": "Educational information only. No guaranteed return or personalized investment advice."
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Updated {OUTPUT} with {len(scored)} scored symbols")


if __name__ == "__main__":
    main()
