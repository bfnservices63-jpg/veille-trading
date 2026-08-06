"""Point d'entrée unique pour récupérer l'historique OHLCV d'un instrument, quel que soit le marché."""
from __future__ import annotations

import logging

import pandas as pd

from src.data import binance_source, coingecko_source, yfinance_source
from src.data.base import Candidate, DataSourceUnavailable

logger = logging.getLogger(__name__)


def fetch_ohlcv(candidate: Candidate) -> pd.DataFrame:
    market = candidate.market
    raw = candidate.raw

    if market == "crypto":
        try:
            return binance_source.fetch_daily_ohlcv(raw["binance"])
        except DataSourceUnavailable as exc:
            logger.warning("Binance indisponible pour %s (%s), repli CoinGecko", candidate.symbol, exc)
            return coingecko_source.fetch_daily_ohlcv(raw["coingecko"])

    # forex, stocks, indices -> yfinance
    return yfinance_source.fetch_daily_ohlcv(raw["ticker"])
