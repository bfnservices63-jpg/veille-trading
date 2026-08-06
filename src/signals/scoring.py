"""Détermination de la direction, du score composite et de la justification textuelle."""
from __future__ import annotations

from dataclasses import dataclass, field

from src import config


def _clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))


def determine_direction(ind: dict) -> str | None:
    """Renvoie 'achat', 'vente' ou None si les signaux se contredisent (l'instrument est alors écarté)."""
    close, ma50, ma200 = ind["close"], ind["ma50"], ind["ma200"]

    trend_bias = 0
    if ma50 is not None:
        ref200 = ma200 if ma200 is not None else ma50
        if close > ma50 and ma50 >= ref200:
            trend_bias = 1
        elif close < ma50 and ma50 <= ref200:
            trend_bias = -1

    momentum_bias = 0
    rising_hist = ind["macd_hist"] > ind["macd_hist_prev"]
    if ind["rsi"] > 55 and rising_hist:
        momentum_bias = 1
    elif ind["rsi"] < 45 and not rising_hist:
        momentum_bias = -1

    breakout_bias = 1 if ind["breakout_up"] else (-1 if ind["breakout_down"] else 0)

    votes = trend_bias + momentum_bias + breakout_bias
    if trend_bias * momentum_bias < 0:  # tendance et momentum contradictoires -> on écarte
        return None
    if votes > 0:
        return "achat"
    if votes < 0:
        return "vente"
    return None


@dataclass
class ScoreBreakdown:
    trend: float
    momentum: float
    breakout_volatility: float
    relative_volume: float
    risk_reward: float
    technical_score: float
    news_score: float | None
    final_score: float
    news_veto: bool
    rationale: list[str] = field(default_factory=list)


def compute_score(ind: dict, direction: str, risk_reward: float, news_info: dict | None) -> ScoreBreakdown:
    sign = 1 if direction == "achat" else -1
    rationale: list[str] = []

    # --- Tendance ---
    trend = 0.0
    if ind["ma50"] is not None:
        aligned = (sign > 0 and ind["close"] > ind["ma50"]) or (sign < 0 and ind["close"] < ind["ma50"])
        if aligned:
            trend = 80.0
            rationale.append(
                f"Prix {'au-dessus' if sign > 0 else 'en-dessous'} de la MA50"
                + (f" et MA200" if ind["ma200"] is not None else "")
            )
            if ind["ma200"] is not None:
                aligned200 = (sign > 0 and ind["ma50"] > ind["ma200"]) or (sign < 0 and ind["ma50"] < ind["ma200"])
                if aligned200:
                    trend = 100.0

    # --- Momentum ---
    rsi_component = _clamp((ind["rsi"] - 50) * 4 * sign)
    macd_favorable = (ind["macd_hist"] - ind["macd_hist_prev"]) * sign > 0
    momentum = rsi_component * 0.7 + (30 if macd_favorable else 0)
    momentum = _clamp(momentum)
    rationale.append(f"RSI {ind['rsi']:.0f}" + (", MACD favorable" if macd_favorable else ""))

    # --- Cassure / volatilité ---
    breakout_hit = (sign > 0 and ind["breakout_up"]) or (sign < 0 and ind["breakout_down"])
    breakout_volatility = 100.0 if breakout_hit else 40.0
    if breakout_hit:
        rationale.append("Cassure du plus " + ("haut" if sign > 0 else "bas") + " sur 20 jours")

    # --- Volume relatif ---
    if ind["relative_volume"] is not None:
        relative_volume = _clamp((ind["relative_volume"] - 1.0) * 100)
        if ind["relative_volume"] > 1.2:
            rationale.append(f"Volume {ind['relative_volume']:.1f}x la moyenne")
    else:
        relative_volume = 50.0  # neutre (ex: forex, pas de vrai volume disponible)

    # --- Ratio risque/récompense ---
    rr_component = _clamp((risk_reward - 1.0) * 50)
    rationale.append(f"Ratio risque/récompense {risk_reward:.2f}")

    w = config.SCORE_WEIGHTS
    technical_score = (
        trend * w["trend"]
        + momentum * w["momentum"]
        + breakout_volatility * w["breakout_volatility"]
        + relative_volume * w["relative_volume"]
        + rr_component * w["risk_reward"]
    )

    news_score = None
    news_veto = False
    final_score = technical_score
    if news_info is not None:
        news_score = news_info.get("score")
        news_veto = bool(news_info.get("veto", False))
        note = news_info.get("note")
        if note:
            rationale.append(f"Actualité : {note}")
        if news_score is not None:
            final_score = technical_score * (1 - config.NEWS_SCORE_WEIGHT) + news_score * config.NEWS_SCORE_WEIGHT

    return ScoreBreakdown(
        trend=trend,
        momentum=momentum,
        breakout_volatility=breakout_volatility,
        relative_volume=relative_volume,
        risk_reward=rr_component,
        technical_score=technical_score,
        news_score=news_score,
        final_score=_clamp(final_score),
        news_veto=news_veto,
        rationale=rationale,
    )
