"""Rendu de la page historique/performance (docs/history.html)."""
from __future__ import annotations

from src import config
from src.render_common import build_env


def render_history(stats: dict, recent_entries: list[dict]) -> str:
    env = build_env()
    template = env.get_template("history.html.j2")
    return template.render(stats=stats, recent_entries=recent_entries)


def write_history(html: str) -> None:
    config.DOCS_DIR.mkdir(parents=True, exist_ok=True)
    (config.DOCS_DIR / "history.html").write_text(html, encoding="utf-8")
