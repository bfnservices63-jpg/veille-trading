#!/usr/bin/env python3
"""Surveillance légère (toutes les 2-3h, jour et nuit) : détecte un événement majeur et alerte immédiatement.

Ne touche pas aux positions/données de marché du jour — job court, peu coûteux en minutes Actions.
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import config  # noqa: E402
from src.news import claude_analyzer, gdelt_source, rss_source  # noqa: E402
from src.notify import mailer  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("run_news_watch")


def _load_state() -> dict:
    if config.NEWS_STATE_PATH.exists():
        return json.loads(config.NEWS_STATE_PATH.read_text(encoding="utf-8"))
    return {}


def _save_state(state: dict) -> None:
    config.HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    config.NEWS_STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    try:
        articles = gdelt_source.fetch_all_geopolitical(hours=config.NEWS_WATCH_HOURS_LOOKBACK)
        articles += rss_source.fetch_all_feeds()
        result = claude_analyzer.check_urgent_event(articles)

        state = _load_state()
        last_headline = state.get("last_urgent_headline")

        if result.get("urgent") and result.get("headline") != last_headline:
            subject = f"🚨 Alerte marché : {result['headline']}"
            body = f"""<html><body style="font-family:monospace; background:#0d1117; color:#c9d1d9; padding:16px;">
            <h2>{result['headline']}</h2>
            <p>{result.get('description', '')}</p>
            <p><b>Recommandation :</b> {result.get('recommendation', '')}</p>
            <p style="color:#8b949e; font-size:12px;">Alerte générée automatiquement par l'analyse news continue.
            Ceci ne remplace pas votre propre jugement.</p>
            </body></html>"""
            mailer.send_email(subject, body)
            logger.info("Alerte urgente envoyée : %s", result["headline"])
            state["last_urgent_headline"] = result["headline"]
            state["last_check"] = datetime.now(timezone.utc).isoformat()
            _save_state(state)
        else:
            logger.info("Aucun événement majeur nouveau détecté.")
            state["last_check"] = datetime.now(timezone.utc).isoformat()
            _save_state(state)

        return 0
    except Exception as exc:
        logger.exception("La surveillance news a échoué")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
