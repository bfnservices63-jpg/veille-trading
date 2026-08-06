"""Interface commune pour les sources de données de marché."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import pandas as pd

OHLCV_COLUMNS = ["open", "high", "low", "close", "volume"]


class DataSourceUnavailable(Exception):
    """Levée quand une source de données ne répond pas, est bloquée, ou renvoie des données invalides."""


@dataclass
class Candidate:
    """Un instrument à évaluer, tel que défini dans une watchlist."""

    symbol: str
    market: str  # forex | crypto | stocks | indices
    session: str  # 24h | EU | US
    raw: dict


def validate_ohlcv(df: pd.DataFrame, source_name: str, max_staleness_days: int = 5) -> pd.DataFrame:
    """Vérifie que les données récupérées sont exploitables. Lève DataSourceUnavailable sinon."""
    if df is None or df.empty:
        raise DataSourceUnavailable(f"{source_name}: données vides")
    missing = [c for c in OHLCV_COLUMNS if c not in df.columns]
    if missing:
        raise DataSourceUnavailable(f"{source_name}: colonnes manquantes {missing}")
    if len(df) < 60:
        raise DataSourceUnavailable(f"{source_name}: historique trop court ({len(df)} barres)")
    if df[OHLCV_COLUMNS[:4]].isna().any().any():
        raise DataSourceUnavailable(f"{source_name}: valeurs manquantes dans les prix")

    last_ts = df.index[-1]
    if last_ts.tzinfo is None:
        last_ts = last_ts.tz_localize("UTC")
    now = datetime.now(timezone.utc)
    if now - last_ts.to_pydatetime() > timedelta(days=max_staleness_days):
        raise DataSourceUnavailable(f"{source_name}: données périmées (dernière barre {last_ts})")
    return df
