"""Orchestre : récupération des données -> indicateurs -> scoring -> classement -> sélection finale."""
from __future__ import annotations

import logging
import math

from src import config
from src.data.base import Candidate, DataSourceUnavailable
from src.data.fetch import fetch_ohlcv
from src.signals import indicators as ind_mod
from src.signals import scoring
from src.signals.levels import compute_levels
from src.signals.models import Signal

logger = logging.getLogger(__name__)


class ScreeningResult:
    def __init__(self, signals: list[Signal], failures: list[tuple[str, str]], underfilled: bool):
        self.signals = signals
        self.failures = failures
        self.underfilled = underfilled


def _has_volume(market: str) -> bool:
    return market != "forex"


def screen_candidates(candidates: list[Candidate], news_context: dict | None = None) -> ScreeningResult:
    news_context = news_context or {}
    scored: list[Signal] = []
    failures: list[tuple[str, str]] = []

    for c in candidates:
        try:
            df = fetch_ohlcv(c)
        except DataSourceUnavailable as exc:
            failures.append((c.symbol, str(exc)))
            continue

        try:
            has_vol = _has_volume(c.market)
            ind = ind_mod.compute_indicators(df, has_vol)
            if ind["ma50"] is None or ind["atr"] is None:
                failures.append((c.symbol, "historique insuffisant pour les indicateurs"))
                continue

            direction = scoring.determine_direction(ind)
            if direction is None:
                continue  # signaux contradictoires : on écarte, ce n'est pas une erreur

            levels = compute_levels(direction, ind["close"], ind["atr"], config.CAPITAL_TOTAL_EUR)
            if levels.risk_reward < config.MIN_RISK_REWARD:
                continue

            news_info = news_context.get(c.symbol)
            score = scoring.compute_score(ind, direction, levels.risk_reward, news_info)
            if score.news_veto:
                continue

            scored.append(
                Signal(
                    symbol=c.symbol,
                    market=c.market,
                    session=c.session,
                    direction=direction,
                    last_close=ind["close"],
                    atr=ind["atr"],
                    levels=levels,
                    score=score,
                    raw=c.raw,
                )
            )
        except Exception as exc:  # ne jamais laisser un instrument planter tout le pipeline
            logger.exception("Erreur de scoring pour %s", c.symbol)
            failures.append((c.symbol, f"erreur de scoring: {exc}"))

    scored.sort(key=lambda s: s.score.final_score, reverse=True)
    selected = _select_with_diversity_cap(scored)
    underfilled = len(selected) < config.MIN_SIGNALS

    return ScreeningResult(signals=selected, failures=failures, underfilled=underfilled)


def _select_with_diversity_cap(scored: list[Signal]) -> list[Signal]:
    target_n = min(config.MAX_SIGNALS, len(scored))
    cap = max(1, math.ceil(config.MAX_SHARE_PER_MARKET * target_n)) if target_n else 0

    selected: list[Signal] = []
    per_market_count: dict[str, int] = {}
    leftover: list[Signal] = []

    for s in scored:
        if len(selected) >= config.MAX_SIGNALS:
            break
        count = per_market_count.get(s.market, 0)
        if count < cap:
            selected.append(s)
            per_market_count[s.market] = count + 1
        else:
            leftover.append(s)

    # Deuxième passe : si le cap de diversité empêche d'atteindre le minimum, on relâche la contrainte.
    for s in leftover:
        if len(selected) >= config.MAX_SIGNALS:
            break
        if len(selected) < config.MIN_SIGNALS:
            selected.append(s)

    return selected
