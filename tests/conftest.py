from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


def _make_ohlcv(n: int, trend_per_bar: float, start: float = 100.0, vol_base: float = 1000.0) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    closes = start + np.cumsum(np.full(n, trend_per_bar)) + rng.normal(0, 0.3, n)
    highs = closes + np.abs(rng.normal(0.5, 0.2, n))
    lows = closes - np.abs(rng.normal(0.5, 0.2, n))
    opens = closes - trend_per_bar / 2
    volumes = vol_base + rng.normal(0, 50, n)
    idx = pd.date_range("2024-01-01", periods=n, freq="D", tz="UTC")
    return pd.DataFrame(
        {"open": opens, "high": highs, "low": lows, "close": closes, "volume": np.abs(volumes)}, index=idx
    )


@pytest.fixture
def uptrend_df() -> pd.DataFrame:
    return _make_ohlcv(300, trend_per_bar=0.3)


@pytest.fixture
def downtrend_df() -> pd.DataFrame:
    return _make_ohlcv(300, trend_per_bar=-0.3)


@pytest.fixture
def flat_df() -> pd.DataFrame:
    return _make_ohlcv(300, trend_per_bar=0.0)
