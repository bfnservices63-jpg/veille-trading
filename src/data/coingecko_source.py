"""Repli gratuit pour la crypto si Binance est bloqué géographiquement.

Limite connue : l'endpoint /market_chart de CoinGecko ne fournit qu'un prix de clôture
par jour (pas de vrai open/high/low). On approxime open=high=low=close, ce qui dégrade
légèrement la précision de l'ATR/breakout pour les instruments concernés — acceptable
car c'est un repli de secours, pas la source principale.
"""
from __future__ import annotations

import pandas as pd
import requests

from src.data.base import DataSourceUnavailable, validate_ohlcv

BASE_URL = "https://api.coingecko.com/api/v3/coins/{id}/market_chart"
TIMEOUT_S = 15


def fetch_daily_ohlcv(coingecko_id: str, days: int = 300) -> pd.DataFrame:
    url = BASE_URL.format(id=coingecko_id)
    params = {"vs_currency": "usd", "days": days, "interval": "daily"}
    try:
        resp = requests.get(url, params=params, timeout=TIMEOUT_S)
    except requests.RequestException as exc:
        raise DataSourceUnavailable(f"coingecko: erreur réseau ({exc})") from exc

    if resp.status_code != 200:
        raise DataSourceUnavailable(f"coingecko: HTTP {resp.status_code}")

    raw = resp.json()
    prices = raw.get("prices", [])
    volumes = raw.get("total_volumes", [])
    if not prices:
        raise DataSourceUnavailable("coingecko: réponse vide")

    price_df = pd.DataFrame(prices, columns=["ts", "close"])
    vol_df = pd.DataFrame(volumes, columns=["ts", "volume"])
    df = price_df.merge(vol_df, on="ts", how="left")
    df["ts"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    df = df.set_index("ts")
    df["open"] = df["close"]
    df["high"] = df["close"]
    df["low"] = df["close"]

    return validate_ohlcv(df[["open", "high", "low", "close", "volume"]], "coingecko")
