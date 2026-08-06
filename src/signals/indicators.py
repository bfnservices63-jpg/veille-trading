"""Calcul des indicateurs techniques utilisés par le moteur de scoring."""
from __future__ import annotations

import numpy as np
import pandas as pd


def sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window, min_periods=window).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    result = 100 - (100 / (1 + rs))
    return result.fillna(50)


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    tr = pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    ).max(axis=1)
    return tr.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()


def relative_volume(df: pd.DataFrame, window: int = 20) -> pd.Series:
    avg_vol = df["volume"].rolling(window=window, min_periods=window).mean()
    return df["volume"] / avg_vol.replace(0, np.nan)


def donchian_breakout(df: pd.DataFrame, window: int = 20) -> tuple[pd.Series, pd.Series]:
    prior_high = df["high"].shift(1).rolling(window=window, min_periods=window).max()
    prior_low = df["low"].shift(1).rolling(window=window, min_periods=window).min()
    upside = df["close"] > prior_high
    downside = df["close"] < prior_low
    return upside, downside


def compute_indicators(df: pd.DataFrame, has_volume: bool) -> dict:
    """Calcule tous les indicateurs et renvoie les valeurs de la dernière barre."""
    close = df["close"]
    ma50 = sma(close, 50)
    ma200 = sma(close, min(200, max(60, len(df) - 1)))
    rsi14 = rsi(close, 14)
    macd_line, signal_line, hist = macd(close)
    atr14 = atr(df, 14)
    up_break, down_break = donchian_breakout(df, 20)
    rel_vol = relative_volume(df, 20) if has_volume else pd.Series([np.nan] * len(df), index=df.index)

    last = -1
    return {
        "close": float(close.iloc[last]),
        "ma50": float(ma50.iloc[last]) if not np.isnan(ma50.iloc[last]) else None,
        "ma200": float(ma200.iloc[last]) if not np.isnan(ma200.iloc[last]) else None,
        "rsi": float(rsi14.iloc[last]),
        "macd": float(macd_line.iloc[last]),
        "macd_signal": float(signal_line.iloc[last]),
        "macd_hist": float(hist.iloc[last]),
        "macd_hist_prev": float(hist.iloc[last - 1]) if len(hist) > 1 else 0.0,
        "atr": float(atr14.iloc[last]) if not np.isnan(atr14.iloc[last]) else None,
        "breakout_up": bool(up_break.iloc[last]),
        "breakout_down": bool(down_break.iloc[last]),
        "relative_volume": float(rel_vol.iloc[last]) if has_volume and not np.isnan(rel_vol.iloc[last]) else None,
    }
