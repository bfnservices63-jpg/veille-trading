# Robot Trading — analyse de marché quotidienne automatisée

Système automatisé qui analyse chaque jour Forex, Crypto, Actions et Indices/CFD, sélectionne les
10 à 15 meilleures opportunités (indicateurs techniques + analyse d'actualité géopolitique/économique
via l'API Claude), et envoie un email récapitulatif avec un tableau de bord web consultable sur
PC et smartphone. Voir [DISCLAIMER.md](DISCLAIMER.md) — ce n'est pas un conseil financier.

## Mise en place initiale (une seule fois)

1. **Créer un dépôt GitHub public** (public car GitHub Pages gratuit ne fonctionne pas sur les
   dépôts privés). Poussez ce projet dedans.
2. **Gmail** : activez la validation en 2 étapes sur le compte qui enverra les emails, puis créez
   un [mot de passe d'application](https://myaccount.google.com/apppasswords) (16 caractères).
3. **Anthropic (Claude)** : créez une clé API sur [console.anthropic.com](https://console.anthropic.com)
   et ajoutez un moyen de paiement (usage pay-as-you-go, coût attendu très faible — quelques
   centimes/jour vu le faible volume de texte analysé).
4. Dans le dépôt GitHub → **Settings → Secrets and variables → Actions**, ajoutez :
   - `GMAIL_ADDRESS` — l'adresse Gmail expéditrice
   - `GMAIL_APP_PASSWORD` — le mot de passe d'application (étape 2)
   - `RECIPIENT_EMAIL` — l'adresse qui recevra le rapport (bfn.services63@gmail.com)
   - `ANTHROPIC_API_KEY` — la clé API Claude (étape 3)
5. **Settings → Pages** → Source : "Deploy from a branch", branche `main`, dossier `/docs`.
   L'URL sera `https://<votre-user>.github.io/<nom-du-repo>/`.
6. **Settings → Actions → General → Workflow permissions** → sélectionnez "Read and write
   permissions" (nécessaire pour que le job puisse committer l'historique et le dashboard).
7. Ouvrez `src/config.py` et ajustez **`CAPITAL_TOTAL_EUR`** à votre capital réel de trading
   (utilisé pour dimensionner les positions à 1% de risque par trade).
8. Mettez à jour **`DASHBOARD_URL`** dans `src/config.py` avec l'URL obtenue à l'étape 5.
9. Onglet **Actions** du dépôt → workflow "Rapport quotidien" → **Run workflow** (déclenchement
   manuel) pour valider tout le pipeline avant de faire confiance à la planification automatique.
10. Vérifiez la réception de l'email test (y compris le dossier spam) et l'affichage du dashboard
    sur PC et téléphone.

Après cette mise en place, **le système tourne seul, tous les jours, sans action de votre part.**

## Fonctionnement

- **Chaque soir (~20h Paris)** : `daily_pipeline.yml` récupère les données de marché (Binance +
  repli CoinGecko pour la crypto, Yahoo Finance pour forex/actions/indices), calcule les
  indicateurs techniques, analyse l'actualité récente via l'API Claude, sélectionne et classe les
  10-15 meilleures idées, envoie l'email et publie le tableau de bord (`docs/`, GitHub Pages),
  et journalise les signaux (`history/signals_log.jsonl`).
- **Toutes les 3h, en continu** : `news_watch.yml` vérifie s'il y a un événement majeur
  (géopolitique, crash, décision de banque centrale) et envoie une alerte email immédiate si oui.
- **Suivi de performance** : à chaque run, les signaux précédemment ouverts sont réévalués
  (stop ou objectif touché ?) et le taux de réussite réel s'affiche sur `docs/history.html`.
- **Le vendredi soir**, toute position encore ouverte sur forex/actions/indices (marchés fermés le
  week-end) est clôturée automatiquement au prix du marché pour éviter un risque de gap au lundi.
  La crypto (24h/7) continue de courir normalement.

## Structure du projet

```
watchlists/        listes d'instruments suivis par marché (modifiable)
src/config.py       tous les réglages (capital, poids du score, seuils...)
src/data/           récupération des données de marché (Binance, CoinGecko, yfinance)
src/signals/        indicateurs, scoring, niveaux d'entrée/stop/objectif, sélection finale
src/news/           récupération de news (GDELT, RSS) + analyse d'impact via Claude
src/history/        journal des signaux + évaluation de performance
src/notify/         génération et envoi de l'email
src/site/           génération du tableau de bord et de la page historique
templates/          gabarits HTML (email + dashboard, thème sombre, style terminal)
scripts/            points d'entrée exécutés par les tâches planifiées
.github/workflows/  planification (cron GitHub Actions)
tests/              tests unitaires (indicateurs, niveaux, scoring, sources de données)
```

## Personnaliser

- **Watchlists** : ajoutez/retirez des instruments dans `watchlists/*.yaml`.
- **Capital et risque** : `CAPITAL_TOTAL_EUR` et `RISK_PER_TRADE_PCT` dans `src/config.py`.
- **Nombre de signaux, seuils, poids du score** : section correspondante de `src/config.py`.
- **Heure d'envoi** : `DAILY_REPORT_HOUR_PARIS` dans `src/config.py` (adapter aussi les deux
  horaires cron dans `.github/workflows/daily_pipeline.yml` si vous changez d'heure cible).

## Tester en local

```bash
pip install -r requirements.txt
cp .env.example .env   # puis éditez .env avec vos vraies valeurs (ne pas committer .env)
python scripts/check_data_sources.py           # vérifie que Binance/Yahoo répondent
python scripts/run_pipeline.py --dry-run --skip-time-check   # génère docs/ sans envoyer d'email
pytest                                          # tests unitaires
```

## Limites connues (voir aussi DISCLAIMER.md)

- **Yahoo Finance (yfinance) est une bibliothèque non officielle** : les données forex/actions/
  indices peuvent être retardées, incomplètes, ou l'accès peut casser sans préavis si Yahoo modifie
  son site. Le pipeline détecte les données invalides/périmées et envoie une alerte plutôt que de
  publier un rapport erroné.
- **Binance peut être bloqué géographiquement** depuis les serveurs GitHub Actions (IP US) — un
  repli automatique vers CoinGecko est en place, avec une précision légèrement réduite (pas de
  vrai open/high/low sur l'API gratuite CoinGecko).
- **Ce n'est pas un flux temps réel** : le rapport du soir est une préparation de session
  (zones de prix + fenêtre horaire), pas un signal seconde par seconde.
- **Le dépôt GitHub est public** (contrainte du plan gratuit de GitHub Pages) : le code, les
  watchlists et les picks quotidiens sont visibles par quiconque connaît l'URL. Les commits
  automatiques utilisent une identité générique (`trading-bot`), sans donnée personnelle.
- **Les indices suivis sont des proxies gratuits pour les CFD** (valeur cash de l'indice) : un
  broker CFD réel appliquera un spread et un financement overnight différents.

## Coût réel

Tout est gratuit (GitHub Actions, GitHub Pages, Gmail SMTP, Binance/CoinGecko/Yahoo Finance) sauf
l'appel quotidien à l'API Claude pour l'analyse d'actualité, en pay-as-you-go (quelques centimes/jour
attendus). Aucun autre coût caché.
