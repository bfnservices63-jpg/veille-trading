"""Journal append-only des signaux générés, source de vérité pour le suivi de performance."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from src import config
from src.signals.models import Signal


def append_signals(signals: list[Signal]) -> None:
    config.HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    with open(config.SIGNALS_LOG_PATH, "a", encoding="utf-8") as f:
        for s in signals:
            entry = s.to_dict()
            entry["logged_at"] = datetime.now(timezone.utc).isoformat()
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def load_all() -> list[dict]:
    if not config.SIGNALS_LOG_PATH.exists():
        return []
    entries = []
    with open(config.SIGNALS_LOG_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def overwrite_all(entries: list[dict]) -> None:
    config.HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    with open(config.SIGNALS_LOG_PATH, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
