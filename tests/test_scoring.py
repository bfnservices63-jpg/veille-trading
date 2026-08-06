from __future__ import annotations

from src.signals.scoring import compute_score, determine_direction

BULLISH_IND = {
    "close": 110.0, "ma50": 105.0, "ma200": 100.0,
    "rsi": 62.0, "macd": 1.2, "macd_signal": 0.8, "macd_hist": 0.4, "macd_hist_prev": 0.1,
    "atr": 2.0, "breakout_up": True, "breakout_down": False, "relative_volume": 1.6,
}

BEARISH_IND = {
    "close": 90.0, "ma50": 95.0, "ma200": 100.0,
    "rsi": 35.0, "macd": -1.2, "macd_signal": -0.8, "macd_hist": -0.4, "macd_hist_prev": -0.1,
    "atr": 2.0, "breakout_up": False, "breakout_down": True, "relative_volume": 1.4,
}

CONFLICTING_IND = {
    "close": 110.0, "ma50": 105.0, "ma200": 100.0,  # tendance haussière
    "rsi": 30.0, "macd": -1.0, "macd_signal": -0.5, "macd_hist": -0.6, "macd_hist_prev": -0.1,  # momentum baissier
    "atr": 2.0, "breakout_up": False, "breakout_down": False, "relative_volume": 1.0,
}


def test_determine_direction_bullish():
    assert determine_direction(BULLISH_IND) == "achat"


def test_determine_direction_bearish():
    assert determine_direction(BEARISH_IND) == "vente"


def test_determine_direction_conflicting_returns_none():
    assert determine_direction(CONFLICTING_IND) is None


def test_compute_score_bullish_in_range_and_has_rationale():
    score = compute_score(BULLISH_IND, "achat", risk_reward=1.5, news_info=None)
    assert 0 <= score.final_score <= 100
    assert score.final_score > 50  # setup propre => score au-dessus de la moyenne
    assert len(score.rationale) > 0


def test_compute_score_applies_news_veto():
    score = compute_score(BULLISH_IND, "achat", risk_reward=1.5, news_info={"score": 10, "veto": True, "note": "risque géopolitique"})
    assert score.news_veto is True


def test_compute_score_news_adjusts_final_score():
    base = compute_score(BULLISH_IND, "achat", risk_reward=1.5, news_info=None)
    adjusted = compute_score(BULLISH_IND, "achat", risk_reward=1.5, news_info={"score": 0, "veto": False, "note": "tensions"})
    assert adjusted.final_score < base.final_score
