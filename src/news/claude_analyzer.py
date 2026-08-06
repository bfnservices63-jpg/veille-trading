"""Analyse du contexte humain/géopolitique via l'API Anthropic (Claude).

Coût pay-as-you-go assumé (voir plan) : seul écart au budget 0€ strict.
En cas d'échec (clé absente, API indisponible), l'analyse news est neutralisée
(score neutre, aucun veto) plutôt que de faire planter tout le pipeline —
le rapport reste alors purement technique pour le jour concerné.
"""
from __future__ import annotations

import json
import logging
import re

from src import config

logger = logging.getLogger(__name__)

_NEWS_ANALYSIS_SYSTEM_PROMPT = """Tu es un analyste de marché qui évalue l'impact d'actualités \
(géopolitique, guerres, banques centrales, entreprises, crypto) sur des instruments financiers.
Réponds UNIQUEMENT avec un objet JSON valide, sans texte autour, au format exact suivant :
{
  "summary": "résumé en 2-3 phrases des événements notables",
  "impacts": [
    {"market": "forex|crypto|stocks|indices", "symbol_hint": "mot-clé ou null si impact global au marché",
     "score": 0-100 (50=neutre, >50=favorable, <50=défavorable), "veto": true/false,
     "note": "courte explication en français"}
  ]
}
"veto": true signifie que le risque est trop élevé aujourd'hui pour proposer une position sur cet instrument/marché.
Si aucune actualité notable, renvoie "impacts": []."""

_URGENT_SYSTEM_PROMPT = """Tu surveilles l'actualité en continu pour détecter des événements majeurs \
susceptibles d'impacter significativement les marchés financiers dans les prochaines heures \
(escalade de guerre, crash éclair, décision surprise de banque centrale, défaut souverain, etc.).
Réponds UNIQUEMENT avec un objet JSON valide, sans texte autour :
{"urgent": true/false, "headline": "titre court ou null", "description": "explication en français ou null",
 "recommendation": "recommandation de prudence en français ou null"}
Ne signale "urgent": true que pour un événement réellement majeur et nouveau, pas pour de l'actualité de routine."""


def _extract_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("Aucun objet JSON trouvé dans la réponse de Claude")
    return json.loads(match.group(0))


def _call_claude(system_prompt: str, user_content: str) -> dict | None:
    if not config.ANTHROPIC_API_KEY:
        logger.warning("ANTHROPIC_API_KEY absente : analyse news désactivée pour ce run")
        return None
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        response = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=2000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_content}],
        )
        text = "".join(block.text for block in response.content if hasattr(block, "text"))
        return _extract_json(text)
    except Exception as exc:
        logger.warning("Appel API Claude échoué : %s", exc)
        return None


def _format_articles(articles: list[dict]) -> str:
    lines = []
    for a in articles[:80]:
        title = a.get("title", "").strip()
        source = a.get("source") or a.get("feed") or ""
        if title:
            lines.append(f"- [{source}] {title}")
    return "\n".join(lines) if lines else "(aucun article récupéré)"


def analyze_market_impact(articles: list[dict], markets: list[str]) -> dict:
    """Renvoie {"summary": str, "impacts": [...]} ; dict vide si l'analyse échoue."""
    user_content = (
        f"Marchés suivis : {', '.join(markets)}.\n\nArticles récents :\n{_format_articles(articles)}"
    )
    result = _call_claude(_NEWS_ANALYSIS_SYSTEM_PROMPT, user_content)
    if result is None:
        return {"summary": "Analyse news indisponible aujourd'hui.", "impacts": []}
    return result


def build_news_context(impacts: list[dict], candidates) -> dict:
    """Transforme la liste d'impacts Claude en dict {symbol: {score, veto, note}} pour le scoring.

    Le rapprochement symbol_hint <-> symbole se fait par correspondance textuelle simple
    et par marché ; en l'absence de correspondance sur un instrument donné, aucun ajustement
    n'est appliqué (score neutre par défaut dans scoring.py).
    """
    context: dict = {}
    for impact in impacts:
        market = impact.get("market")
        hint = (impact.get("symbol_hint") or "").lower()
        entry = {"score": impact.get("score", 50), "veto": impact.get("veto", False), "note": impact.get("note", "")}
        for c in candidates:
            if c.market != market:
                continue
            if hint and hint not in c.symbol.lower():
                continue
            context[c.symbol] = entry
    return context


def check_urgent_event(articles: list[dict]) -> dict:
    user_content = f"Articles très récents :\n{_format_articles(articles)}"
    result = _call_claude(_URGENT_SYSTEM_PROMPT, user_content)
    if result is None:
        return {"urgent": False, "headline": None, "description": None, "recommendation": None}
    return result
