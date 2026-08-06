"""Récupération forex/actions/indices via yfinance (Yahoo Finance non officiel, gratuit, sans clé).

Limite connue et assumée (voir plan) : peut être retardé, incomplet, ou casser sans
préavis si Yahoo modifie son site. validate_ohlcv() filtre les données trop périmées
ou incomplètes plutôt que de laisser passer un rapport erroné.
"""
from __future__ import annotations

import pandas as pd
import yfinance as yf

from src.data.base import DataSourceUnavailable, validate_ohlcv


def fetch_daily_ohlcv(ticker: str, period: str = "1y") -> pd.DataFrame:
    try:
        raw = yf.Ticker(ticker).history(period=period, interval="1d", auto_adjust=False)
    except Exception as exc:  # yfinance lève des erreurs variées selon la panne
        raise DataSourceUnavailable(f"yfinance: erreur ({exc})") from exc

    if raw is None or raw.empty:
        raise DataSourceUnavailable(f"yfinance: aucune donnée pour {ticker}")

    raw = raw.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"})
    if raw.index.tzinfo is None:
        raw.index = raw.index.tz_localize("UTC")

    return validate_ohlcv(raw[["open", "high", "low", "close", "volume"]], f"yfinance:{ticker}")
