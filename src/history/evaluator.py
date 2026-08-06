"""Vérifie si les signaux passés ont touché leur stop ou leur objectif, pour un vrai suivi de performance."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

import pandas as pd

from src.data.base import Candidate, DataSourceUnavailable
from src.data.fetch import fetch_ohlcv
from src.history import logger as history_logger

logger = logging.getLogger(__name__)

LOOKAHEAD_DAYS = 10  # au-delà, un signal ni SL ni TP touché est marqué EXPIRED


def _candidate_from_entry(entry: dict) -> Candidate:
    return Candidate(symbol=entry["symbol"], market=entry["market"], session=entry.get("session", "24h"), raw=entry.get("raw", {}))


def _first_hit(df: pd.DataFrame, since: datetime, direction: str, stop: float, tp1: float) -> str | None:
    """Regarde les barres depuis 'since' et renvoie 'SL_HIT', 'TP_HIT' ou None si rien touché encore."""
    since_ts = pd.Timestamp(since)
    if since_ts.tzinfo is None:
        since_ts = since_ts.tz_localize("UTC")
    future = df[df.index > since_ts]
    for _, row in future.iterrows():
        if direction == "achat":
            hit_stop = row["low"] <= stop
            hit_tp = row["high"] >= tp1
        else:
            hit_stop = row["high"] >= stop
            hit_tp = row["low"] <= tp1
        if hit_stop and hit_tp:
            return "SL_HIT"  # prudence : si les deux sont touchés la même barre, on suppose le pire cas
        if hit_stop:
            return "SL_HIT"
        if hit_tp:
            return "TP_HIT"
    return None


def evaluate_pending_signals() -> dict:
    """Met à jour l'historique et renvoie des statistiques agrégées."""
    entries = history_logger.load_all()
    now = datetime.now(timezone.utc)

    for entry in entries:
        if entry.get("outcome") != "PENDING":
            continue
        generated_at = datetime.fromisoformat(entry["generated_at"])
        try:
            candidate = _candidate_from_entry(entry)
            df = fetch_ohlcv(candidate)
            outcome = _first_hit(df, generated_at, entry["direction"], entry["stop"], entry["tp1"])
            if outcome:
                entry["outcome"] = outcome
            elif (now - generated_at.replace(tzinfo=timezone.utc) if generated_at.tzinfo is None else now - generated_at).days > LOOKAHEAD_DAYS:
                entry["outcome"] = "EXPIRED"
        except DataSourceUnavailable as exc:
            logger.warning("Impossible d'évaluer %s : %s", entry["symbol"], exc)
        except Exception:
            logger.exception("Erreur d'évaluation pour %s", entry.get("symbol"))

    history_logger.overwrite_all(entries)
    return compute_stats(entries)


def close_positions_before_weekend(weekend_markets: set[str]) -> None:
    """Clôture au prix du marché toute position PENDING sur un marché fermé le week-end
    (forex/actions/indices), pour éviter un risque de gap à la réouverture du lundi.
    À appeler uniquement lors du run du vendredi soir. La crypto (24h/7) n'est pas concernée.
    """
    entries = history_logger.load_all()
    changed = False
    for entry in entries:
        if entry.get("outcome") != "PENDING" or entry["market"] not in weekend_markets:
            continue
        try:
            candidate = _candidate_from_entry(entry)
            df = fetch_ohlcv(candidate)
            current_price = float(df["close"].iloc[-1])
            sign = 1 if entry["direction"] == "achat" else -1
            risk = abs(entry["entry"] - entry["stop"])
            realized_r = ((current_price - entry["entry"]) * sign) / risk if risk else 0.0
            entry["outcome"] = "CLOSED_WEEKEND"
            entry["realized_r"] = realized_r
            entry["closed_price"] = current_price
            changed = True
        except DataSourceUnavailable as exc:
            logger.warning("Impossible de clôturer %s avant le week-end : %s", entry["symbol"], exc)
        except Exception:
            logger.exception("Erreur de clôture week-end pour %s", entry.get("symbol"))
    if changed:
        history_logger.overwrite_all(entries)


def compute_stats(entries: list[dict]) -> dict:
    resolved = [e for e in entries if e.get("outcome") in ("SL_HIT", "TP_HIT")]
    wins = [e for e in resolved if e["outcome"] == "TP_HIT"]
    win_rate = (len(wins) / len(resolved) * 100) if resolved else None

    r_multiples = []
    for e in resolved:
        r = e["risk_reward"] if e["outcome"] == "TP_HIT" else -1.0
        r_multiples.append(r)
    avg_r = sum(r_multiples) / len(r_multiples) if r_multiples else None

    by_market: dict[str, dict] = {}
    for e in resolved:
        m = e["market"]
        by_market.setdefault(m, {"total": 0, "wins": 0})
        by_market[m]["total"] += 1
        if e["outcome"] == "TP_HIT":
            by_market[m]["wins"] += 1
    for m, d in by_market.items():
        d["win_rate"] = (d["wins"] / d["total"] * 100) if d["total"] else None

    return {
        "total_resolved": len(resolved),
        "total_pending": len([e for e in entries if e.get("outcome") == "PENDING"]),
        "win_rate": win_rate,
        "avg_r_multiple": avg_r,
        "by_market": by_market,
    }
