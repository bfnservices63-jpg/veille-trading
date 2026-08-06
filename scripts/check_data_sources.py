#!/usr/bin/env python3
"""Script manuel (non planifié) pour vérifier rapidement que les sources de données répondent.

Usage : python scripts/check_data_sources.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data import binance_source, yfinance_source  # noqa: E402
from src.data.base import DataSourceUnavailable  # noqa: E402


def check(name: str, fn) -> None:
    try:
        df = fn()
        print(f"[OK] {name}: {len(df)} barres, dernière = {df.index[-1]}")
    except DataSourceUnavailable as exc:
        print(f"[ECHEC] {name}: {exc}")
    except Exception as exc:
        print(f"[ERREUR] {name}: {exc}")


if __name__ == "__main__":
    check("Binance BTCUSDT", lambda: binance_source.fetch_daily_ohlcv("BTCUSDT"))
    check("Yahoo Finance AAPL", lambda: yfinance_source.fetch_daily_ohlcv("AAPL"))
    check("Yahoo Finance EURUSD=X", lambda: yfinance_source.fetch_daily_ohlcv("EURUSD=X"))
