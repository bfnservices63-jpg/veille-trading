"""Envoi de l'email via SMTP Gmail (mot de passe d'application)."""
from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src import config

logger = logging.getLogger(__name__)

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


def send_email(subject: str, html_body: str) -> None:
    if not config.GMAIL_ADDRESS or not config.GMAIL_APP_PASSWORD:
        raise RuntimeError(
            "GMAIL_ADDRESS / GMAIL_APP_PASSWORD manquants — configurez les secrets avant l'envoi."
        )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config.GMAIL_ADDRESS
    msg["To"] = config.RECIPIENT_EMAIL
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
        server.starttls()
        server.login(config.GMAIL_ADDRESS, config.GMAIL_APP_PASSWORD)
        server.sendmail(config.GMAIL_ADDRESS, [config.RECIPIENT_EMAIL], msg.as_string())
    logger.info("Email envoyé à %s : %s", config.RECIPIENT_EMAIL, subject)


def send_failure_alert(context: str, error: str) -> None:
    """Email minimal en cas d'échec du pipeline, pour ne pas laisser l'utilisateur sans nouvelles."""
    subject = f"⚠️ Robot Trading — échec du pipeline ({context})"
    body = f"""<html><body style="font-family:monospace;">
    <p>Le pipeline "{context}" a échoué aujourd'hui.</p>
    <p>Erreur : {error}</p>
    <p>Vérifiez les logs GitHub Actions du dépôt pour le détail.</p>
    </body></html>"""
    try:
        send_email(subject, body)
    except Exception:
        logger.exception("Impossible d'envoyer même l'email d'alerte d'échec")
