#!/usr/bin/env python3
"""Pipeline complet du soir : données marché + news/IA + scoring + email + dashboard + historique.

Usage :
    python scripts/run_pipeline.py                  # run normal (vérifie l'heure locale Paris)
    python scripts/run_pipeline.py --skip-time-check # ignore la vérification d'heure (tests manuels)
    python scripts/run_pipeline.py --dry-run         # ne journalise pas et n'envoie pas d'email
"""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import config  # noqa: E402
from src.data.watchlist_loader import load_all_candidates  # noqa: E402
from src.history import evaluator, logger as history_logger  # noqa: E402
from src.news import claude_analyzer, gdelt_source, rss_source  # noqa: E402
from src.notify import email_template, mailer  # noqa: E402
from src.signals.screener import screen_candidates  # noqa: E402
from src.site import dashboard_template, history_page  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("run_pipeline")


def _in_target_window() -> bool:
    now_paris = datetime.now(config.TIMEZONE)
    return now_paris.hour == config.DAILY_REPORT_HOUR_PARIS


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="ne journalise pas, n'envoie pas d'email")
    parser.add_argument("--skip-time-check", action="store_true", help="ignore la vérification d'heure locale")
    args = parser.parse_args()

    now_paris = datetime.now(config.TIMEZONE)
    if not args.skip_time_check and not _in_target_window():
        logger.info("Hors fenêtre horaire cible (%sh Paris), heure actuelle %sh — on ne fait rien.",
                    config.DAILY_REPORT_HOUR_PARIS, now_paris.hour)
        return 0

    report_date = now_paris.strftime("%A %d %B %Y")

    try:
        candidates = load_all_candidates()
        logger.info("%d instruments dans les watchlists", len(candidates))

        articles = gdelt_source.fetch_all_geopolitical(hours=24) + rss_source.fetch_all_feeds()
        news_result = claude_analyzer.analyze_market_impact(articles, list(config.MARKET_LABELS.keys()))
        news_context = claude_analyzer.build_news_context(news_result.get("impacts", []), candidates)
        logger.info("Analyse news : %s (%d ajustements)", news_result.get("summary", "-"), len(news_context))

        result = screen_candidates(candidates, news_context)
        logger.info("%d signaux retenus, %d échecs de récupération de données",
                    len(result.signals), len(result.failures))

        if result.failures:
            for symbol, reason in result.failures:
                logger.warning("Échec %s : %s", symbol, reason)

        if not args.dry_run:
            history_logger.append_signals(result.signals)
            if now_paris.weekday() == 4:  # vendredi
                evaluator.close_positions_before_weekend(config.WEEKEND_CLOSED_MARKETS)
            stats = evaluator.evaluate_pending_signals()
        else:
            stats = evaluator.compute_stats(history_logger.load_all())

        signal_dicts = [s.to_dict() for s in result.signals]

        dashboard_html = dashboard_template.render_dashboard(
            report_date, signal_dicts, result.underfilled
        )
        email_html = email_template.render_email(
            report_date, signal_dicts, result.underfilled
        )
        entries = history_logger.load_all()
        history_html = history_page.render_history(stats, entries[-100:][::-1])

        dashboard_template.write_dashboard(dashboard_html)
        history_page.write_history(history_html)

        if not args.dry_run:
            subject = f"Positions du jour — {report_date} ({len(result.signals)} idées)"
            mailer.send_email(subject, email_html)
        else:
            logger.info("Mode --dry-run : email et journalisation ignorés. Fichiers docs/ générés quand même.")

        logger.info("Pipeline terminé avec succès.")
        return 0

    except Exception as exc:
        logger.exception("Le pipeline a échoué")
        if not args.dry_run:
            mailer.send_failure_alert("rapport quotidien", str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
