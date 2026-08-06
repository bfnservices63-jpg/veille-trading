"""Rendu du corps HTML de l'email quotidien."""
from __future__ import annotations

from src import config
from src.render_common import build_env


def render_email(
    report_date: str,
    signals: list[dict],
    underfilled: bool,
    urgent_alert: str | None = None,
) -> str:
    env = build_env()
    template = env.get_template("email.html.j2")
    return template.render(
        report_date=report_date,
        signals=signals,
        underfilled=underfilled,
        min_signals=config.MIN_SIGNALS,
        urgent_alert=urgent_alert,
        dashboard_url=config.DASHBOARD_URL,
    )
