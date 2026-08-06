"""Charge les watchlists YAML en objets Candidate."""
from __future__ import annotations

import yaml

from src import config
from src.data.base import Candidate


def load_all_candidates() -> list[Candidate]:
    candidates: list[Candidate] = []
    for market, path in config.WATCHLIST_FILES.items():
        with open(path, encoding="utf-8") as f:
            entries = yaml.safe_load(f) or []
        for entry in entries:
            candidates.append(
                Candidate(
                    symbol=entry["symbol"],
                    market=market,
                    session=entry.get("session", "24h"),
                    raw=entry,
                )
            )
    return candidates
