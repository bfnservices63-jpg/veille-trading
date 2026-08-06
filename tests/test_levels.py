from __future__ import annotations

import pytest

from src.signals.levels import compute_levels


def test_achat_levels_ordering():
    lv = compute_levels("achat", last_close=100.0, atr=2.0, capital_eur=3000.0)
    assert lv.stop < lv.entry < lv.tp1 < lv.tp2


def test_vente_levels_ordering():
    lv = compute_levels("vente", last_close=100.0, atr=2.0, capital_eur=3000.0)
    assert lv.tp2 < lv.tp1 < lv.entry < lv.stop


def test_risk_reward_matches_atr_multiples():
    lv = compute_levels("achat", last_close=100.0, atr=2.0, capital_eur=3000.0)
    # stop = 1.5*ATR, tp1 = 2.0*ATR => R:R théorique ~= 2.0/1.5
    assert lv.risk_reward == pytest.approx(2.0 / 1.5, rel=0.01)


def test_position_size_respects_risk_budget():
    capital = 3000.0
    lv = compute_levels("achat", last_close=100.0, atr=2.0, capital_eur=capital)
    risk_per_unit = abs(lv.entry - lv.stop)
    assert lv.position_size * risk_per_unit == pytest.approx(capital * 0.01, rel=0.01)
    assert lv.risk_amount_eur == pytest.approx(capital * 0.01, rel=0.01)
