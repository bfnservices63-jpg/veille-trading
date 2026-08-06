"""Configuration centrale du système. Modifiez les valeurs ci-dessous selon vos besoins."""
from __future__ import annotations

import os
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT_DIR = Path(__file__).resolve().parent.parent
WATCHLISTS_DIR = ROOT_DIR / "watchlists"
HISTORY_DIR = ROOT_DIR / "history"
DOCS_DIR = ROOT_DIR / "docs"
TEMPLATES_DIR = ROOT_DIR / "templates"
SIGNALS_LOG_PATH = HISTORY_DIR / "signals_log.jsonl"
NEWS_STATE_PATH = HISTORY_DIR / "news_watch_state.json"

TIMEZONE = ZoneInfo("Europe/Paris")
DAILY_REPORT_HOUR_PARIS = 20  # heure locale Paris visée pour l'envoi du soir (voir daily_pipeline.yml)
NEWS_WATCH_HOURS_LOOKBACK = 3  # fenêtre de récupération des news pour la surveillance fréquente

# --- Capital et gestion du risque ---
# À AJUSTER : montant réel de votre capital de trading (vous avez indiqué une fourchette 1000-5000€).
CAPITAL_TOTAL_EUR = float(os.environ.get("CAPITAL_TOTAL_EUR", 3000))
RISK_PER_TRADE_PCT = 0.01  # 1% du capital risqué par position

# --- Sélection des signaux ---
MIN_SIGNALS = 10
MAX_SIGNALS = 15
MIN_RISK_REWARD = 1.2
MAX_SHARE_PER_MARKET = 0.4  # pas plus de 40% des picks du jour issus d'un seul marché

# --- Niveaux ATR ---
STOP_ATR_MULT = 1.5
TP1_ATR_MULT = 2.0
TP2_ATR_MULT = 3.0
ENTRY_PULLBACK_ATR_MULT = 0.25

# --- Poids du score composite (somme = 1.0) ---
SCORE_WEIGHTS = {
    "trend": 0.30,
    "momentum": 0.25,
    "breakout_volatility": 0.20,
    "relative_volume": 0.15,
    "risk_reward": 0.10,
}
NEWS_SCORE_WEIGHT = 0.20  # poids de l'ajustement news, appliqué en plus du score technique (voir scoring.py)

# --- Email ---
GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL", "bfn.services63@gmail.com")

# --- Anthropic (analyse news) ---
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5")

# --- Dashboard ---
# À AJUSTER après la première publication GitHub Pages : https://<votre-user>.github.io/<repo>/
DASHBOARD_URL = os.environ.get("DASHBOARD_URL", "https://<votre-user>.github.io/<repo>/")

# --- Watchlists ---
WATCHLIST_FILES = {
    "forex": WATCHLISTS_DIR / "forex.yaml",
    "crypto": WATCHLISTS_DIR / "crypto.yaml",
    "stocks": WATCHLISTS_DIR / "stocks.yaml",
    "indices": WATCHLISTS_DIR / "indices.yaml",
}

MARKET_LABELS = {
    "forex": "Forex",
    "crypto": "Crypto",
    "stocks": "Actions",
    "indices": "Indices/CFD",
}

# Marchés fermés le week-end (position forcée à la clôture le vendredi soir)
WEEKEND_CLOSED_MARKETS = {"forex", "stocks", "indices"}
