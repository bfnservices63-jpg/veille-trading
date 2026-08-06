"""Modèle de données représentant une position proposée."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from src.signals.levels import Levels
from src.signals.scoring import ScoreBreakdown


@dataclass
class Signal:
    symbol: str
    market: str
    session: str
    direction: str  # achat | vente
    last_close: float
    atr: float
    levels: Levels
    score: ScoreBreakdown
    raw: dict = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.utcnow)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "symbol": self.symbol,
            "market": self.market,
            "session": self.session,
            "direction": self.direction,
            "raw": self.raw,
            "last_close": self.last_close,
            "atr": self.atr,
            "entry": self.levels.entry,
            "stop": self.levels.stop,
            "tp1": self.levels.tp1,
            "tp2": self.levels.tp2,
            "risk_reward": self.levels.risk_reward,
            "position_size": self.levels.position_size,
            "risk_amount_eur": self.levels.risk_amount_eur,
            "final_score": self.score.final_score,
            "technical_score": self.score.technical_score,
            "news_score": self.score.news_score,
            "rationale": self.score.rationale,
            "generated_at": self.generated_at.isoformat(),
            "outcome": "PENDING",
        }
