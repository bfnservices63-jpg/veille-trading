from __future__ import annotations

import pandas as pd
import pytest

from src.data import binance_source, yfinance_source
from src.data.base import DataSourceUnavailable, validate_ohlcv


def _valid_df(n=100):
    idx = pd.date_range("2024-01-01", periods=n, freq="D", tz="UTC")
    return pd.DataFrame(
        {"open": range(n), "high": range(n), "low": range(n), "close": range(n), "volume": [1] * n},
        index=idx,
    )


def test_validate_ohlcv_rejects_empty():
    with pytest.raises(DataSourceUnavailable):
        validate_ohlcv(pd.DataFrame(), "test")


def test_validate_ohlcv_rejects_too_short():
    with pytest.raises(DataSourceUnavailable):
        validate_ohlcv(_valid_df(10), "test")


def test_validate_ohlcv_rejects_stale_data():
    idx = pd.date_range("2020-01-01", periods=100, freq="D", tz="UTC")
    df = pd.DataFrame(
        {"open": range(100), "high": range(100), "low": range(100), "close": range(100), "volume": [1] * 100},
        index=idx,
    )
    with pytest.raises(DataSourceUnavailable):
        validate_ohlcv(df, "test")


def test_validate_ohlcv_accepts_fresh_data():
    n = 100
    idx = pd.date_range(end=pd.Timestamp.utcnow(), periods=n, freq="D", tz="UTC")
    df = pd.DataFrame(
        {"open": range(n), "high": range(n), "low": range(n), "close": range(n), "volume": [1] * n},
        index=idx,
    )
    result = validate_ohlcv(df, "test")
    assert len(result) == n


class _FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def test_binance_source_geo_blocked_raises(monkeypatch):
    def fake_get(*args, **kwargs):
        return _FakeResponse(451, {})

    monkeypatch.setattr(binance_source.requests, "get", fake_get)
    with pytest.raises(DataSourceUnavailable):
        binance_source.fetch_daily_ohlcv("BTCUSDT")


def test_binance_source_parses_klines(monkeypatch):
    import time

    n = 100
    now_ms = int(time.time() * 1000)
    base_ts = now_ms - n * 86400000
    klines = [
        [base_ts + i * 86400000, "100.0", "101.0", "99.0", "100.5", "1000", base_ts, "0", 0, "0", "0", "0"]
        for i in range(n)
    ]

    def fake_get(*args, **kwargs):
        return _FakeResponse(200, klines)

    monkeypatch.setattr(binance_source.requests, "get", fake_get)
    df = binance_source.fetch_daily_ohlcv("BTCUSDT")
    assert len(df) == n
    assert list(df.columns) == ["open", "high", "low", "close", "volume"]


def test_yfinance_source_empty_raises(monkeypatch):
    class FakeTicker:
        def __init__(self, ticker):
            pass

        def history(self, **kwargs):
            return pd.DataFrame()

    monkeypatch.setattr(yfinance_source.yf, "Ticker", FakeTicker)
    with pytest.raises(DataSourceUnavailable):
        yfinance_source.fetch_daily_ohlcv("AAPL")
