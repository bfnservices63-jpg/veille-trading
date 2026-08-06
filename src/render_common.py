"""Environnement Jinja2 partagé entre l'email et le dashboard (mêmes filtres, même style)."""
from __future__ import annotations

from jinja2 import Environment, FileSystemLoader

from src import config

MARKET_COLORS = {
    "forex": "#58a6ff",
    "crypto": "#d29922",
    "stocks": "#bc8cff",
    "indices": "#39c5cf",
}

SESSION_LABELS = {
    "24h": "24h/24",
    "EU": "Session Europe (~9h-17h30 Paris)",
    "US": "Session US (~15h30-22h Paris)",
}


def fmt_price(value: float) -> str:
    if value is None:
        return "-"
    if abs(value) >= 100:
        return f"{value:,.2f}".replace(",", " ")
    if abs(value) >= 1:
        return f"{value:.4f}"
    return f"{value:.6f}"


def fmt_pct(value: float | None) -> str:
    return "-" if value is None else f"{value:.0f}%"


def fmt_size(value: float) -> str:
    return f"{value:,.4f}".replace(",", " ")


def score_color(score: float) -> str:
    if score >= 70:
        return "#3fb950"
    if score >= 45:
        return "#d29922"
    return "#f85149"


def direction_color(direction: str) -> str:
    return "#3fb950" if direction == "achat" else "#f85149"


def market_color(market: str) -> str:
    return MARKET_COLORS.get(market, "#8b949e")


def market_label(market: str) -> str:
    return config.MARKET_LABELS.get(market, market)


def session_label(session: str) -> str:
    return SESSION_LABELS.get(session, session)


def build_env() -> Environment:
    env = Environment(loader=FileSystemLoader(str(config.TEMPLATES_DIR)), autoescape=True)
    env.filters["price"] = fmt_price
    env.filters["pct"] = fmt_pct
    env.filters["size"] = fmt_size
    env.filters["score_color"] = score_color
    env.filters["direction_color"] = direction_color
    env.filters["market_color"] = market_color
    env.filters["market_label"] = market_label
    env.filters["session_label"] = session_label
    return env
