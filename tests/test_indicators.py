from __future__ import annotations

from src.signals import indicators


def test_sma_length_and_last_value(uptrend_df):
    ma = indicators.sma(uptrend_df["close"], 50)
    assert ma.isna().sum() == 49
    assert ma.iloc[-1] < uptrend_df["close"].iloc[-1]  # MA en retard sur un uptrend


def test_rsi_bounds(uptrend_df):
    r = indicators.rsi(uptrend_df["close"])
    assert (r >= 0).all() and (r <= 100).all()


def test_rsi_high_on_strong_uptrend(uptrend_df):
    r = indicators.rsi(uptrend_df["close"])
    assert r.iloc[-1] > 60


def test_rsi_low_on_strong_downtrend(downtrend_df):
    r = indicators.rsi(downtrend_df["close"])
    assert r.iloc[-1] < 40


def test_atr_positive(uptrend_df):
    a = indicators.atr(uptrend_df)
    assert a.dropna().gt(0).all()


def test_macd_shapes(uptrend_df):
    macd_line, signal_line, hist = indicators.macd(uptrend_df["close"])
    assert len(macd_line) == len(uptrend_df)
    assert len(signal_line) == len(uptrend_df)
    assert len(hist) == len(uptrend_df)


def test_donchian_breakout_flags_are_boolean(uptrend_df):
    up, down = indicators.donchian_breakout(uptrend_df)
    assert up.dtype == bool
    assert down.dtype == bool


def test_compute_indicators_uptrend(uptrend_df):
    ind = indicators.compute_indicators(uptrend_df, has_volume=True)
    assert ind["ma50"] is not None
    assert ind["atr"] is not None
    assert ind["rsi"] > 50


def test_compute_indicators_no_volume_market():
    from tests.conftest import _make_ohlcv

    df = _make_ohlcv(300, trend_per_bar=0.1)
    ind = indicators.compute_indicators(df, has_volume=False)
    assert ind["relative_volume"] is None
