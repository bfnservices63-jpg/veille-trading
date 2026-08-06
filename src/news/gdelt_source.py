"""Récupération d'articles géopolitiques via l'API gratuite GDELT (GDELT DOC 2.0)."""
from __future__ import annotations

import logging

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
TIMEOUT_S = 20

# Requêtes couvrant le périmètre demandé : géopolitique/guerres, banques centrales, crypto.
QUERIES = [
    "war OR conflict OR sanctions OR military",
    "central bank OR interest rate OR inflation",
    "cryptocurrency regulation OR crypto hack",
]


def fetch_recent_articles(query: str, hours: int = 6, max_records: int = 40) -> list[dict]:
    params = {
        "query": query,
        "mode": "artlist",
        "maxrecords": max_records,
        "format": "json",
        "timespan": f"{hours}h",
        "sort": "datedesc",
    }
    try:
        resp = requests.get(BASE_URL, params=params, timeout=TIMEOUT_S)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logger.warning("GDELT indisponible pour la requête %r : %s", query, exc)
        return []

    articles = data.get("articles", [])
    return [
        {
            "title": a.get("title", ""),
            "url": a.get("url", ""),
            "date": a.get("seendate", ""),
            "source": a.get("domain", ""),
        }
        for a in articles
    ]


def fetch_all_geopolitical(hours: int = 6) -> list[dict]:
    articles: list[dict] = []
    for q in QUERIES:
        articles.extend(fetch_recent_articles(q, hours=hours))
    return articles
