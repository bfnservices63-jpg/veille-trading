"""Récupération de données crypto via l'API publique Binance (gratuite, sans clé).

Peut être bloquée géographiquement (ex: IP US des runners GitHub Actions -> HTTP 451).
Dans ce cas, l'appelant doit basculer sur coingecko_source.py.
"""
from __future__ import annotations

import pandas as pd
import requests

from src.data.base import DataSourceUnavailable, validate_ohlcv

BASE_URL = "https://api.binance.com/api/v3/klines"
TIMEOUT_S = 15


def fetch_daily_ohlcv(binance_symbol: str, limit: int = 300) -> pd.DataFrame:
    params = {"symbol": binance_symbol, "interval": "1d", "limit": limit}
    try:
        resp = requests.get(BASE_URL, params=params, timeout=TIMEOUT_S)
    except requests.RequestException as exc:
        raise DataSourceUnavailable(f"binance: erreur réseau ({exc})") from exc

    if resp.status_code == 451:
        raise DataSourceUnavailable("binance: bloqué géographiquement (HTTP 451)")
    if resp.status_code != 200:
        raise DataSourceUnavailable(f"binance: HTTP {resp.status_code}")

    raw = resp.json()
    if not isinstance(raw, list) or not raw:
        raise DataSourceUnavailable("binance: réponse vide/inattendue")

    df = pd.DataFrame(
        raw,
        columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "n_trades",
            "taker_buy_base", "taker_buy_quote", "ignore",
        ],
    )
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    df = df.set_index("open_time")
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)

    return validate_ohlcv(df[["open", "high", "low", "close", "volume"]], "binance")
