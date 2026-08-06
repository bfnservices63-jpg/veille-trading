"""Rendu du tableau de bord statique (docs/index.html, publié par GitHub Pages)."""
from __future__ import annotations

from src import config
from src.render_common import build_env


def render_dashboard(
    report_date: str,
    signals: list[dict],
    underfilled: bool,
    urgent_alert: str | None = None,
) -> str:
    env = build_env()
    template = env.get_template("dashboard.html.j2")
    return template.render(
        report_date=report_date,
        signals=signals,
        underfilled=underfilled,
        min_signals=config.MIN_SIGNALS,
        urgent_alert=urgent_alert,
    )


def write_dashboard(html: str) -> None:
    config.DOCS_DIR.mkdir(parents=True, exist_ok=True)
    (config.DOCS_DIR / "index.html").write_text(html, encoding="utf-8")
