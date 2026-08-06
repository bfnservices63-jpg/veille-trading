"""Récupération de flux RSS gratuits pour compléter GDELT (économie, entreprises, crypto)."""
from __future__ import annotations

import logging

import feedparser

logger = logging.getLogger(__name__)

FEEDS = {
    "bbc_world": "http://feeds.bbci.co.uk/news/world/rss.xml",
    "bbc_business": "http://feeds.bbci.co.uk/news/business/rss.xml",
    "yahoo_finance": "https://finance.yahoo.com/news/rssindex",
    "coindesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
}


def fetch_feed(url: str, max_items: int = 15) -> list[dict]:
    try:
        parsed = feedparser.parse(url)
    except Exception as exc:
        logger.warning("Flux RSS indisponible (%s): %s", url, exc)
        return []

    entries = []
    for e in parsed.entries[:max_items]:
        entries.append(
            {
                "title": e.get("title", ""),
                "summary": e.get("summary", ""),
                "published": e.get("published", ""),
                "link": e.get("link", ""),
            }
        )
    return entries


def fetch_all_feeds() -> list[dict]:
    articles: list[dict] = []
    for name, url in FEEDS.items():
        for entry in fetch_feed(url):
            entry["feed"] = name
            articles.append(entry)
    return articles
