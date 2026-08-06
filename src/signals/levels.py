"""Calcul des niveaux d'entrée/stop/objectifs (multiples d'ATR) et du dimensionnement de position."""
from __future__ import annotations

from dataclasses import dataclass

from src import config


@dataclass
class Levels:
    entry: float
    stop: float
    tp1: float
    tp2: float
    risk_reward: float
    position_size: float
    risk_amount_eur: float


def compute_levels(direction: str, last_close: float, atr: float, capital_eur: float) -> Levels:
    """direction: 'achat' ou 'vente'."""
    sign = 1 if direction == "achat" else -1

    entry = last_close - sign * config.ENTRY_PULLBACK_ATR_MULT * atr
    stop = entry - sign * config.STOP_ATR_MULT * atr
    tp1 = entry + sign * config.TP1_ATR_MULT * atr
    tp2 = entry + sign * config.TP2_ATR_MULT * atr

    risk_per_unit = abs(entry - stop)
    reward_per_unit = abs(tp1 - entry)
    risk_reward = reward_per_unit / risk_per_unit if risk_per_unit > 0 else 0.0

    risk_amount_eur = capital_eur * config.RISK_PER_TRADE_PCT
    position_size = risk_amount_eur / risk_per_unit if risk_per_unit > 0 else 0.0

    return Levels(
        entry=entry,
        stop=stop,
        tp1=tp1,
        tp2=tp2,
        risk_reward=risk_reward,
        position_size=position_size,
        risk_amount_eur=risk_amount_eur,
    )
