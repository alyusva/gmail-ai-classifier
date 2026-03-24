#!/usr/bin/env python3
"""
Renueva el Gmail Watch antes de que caduque (expira cada 7 días).

Uso:
    python scripts/renew_gmail_watch.py               # Renueva si quedan < 2 días
    python scripts/renew_gmail_watch.py --force       # Fuerza renovación siempre
    python scripts/renew_gmail_watch.py --status      # Muestra estado actual

Configurar en cron para ejecutar diariamente:
    0 9 * * * cd /ruta/al/proyecto && python scripts/renew_gmail_watch.py >> logs/watch.log 2>&1
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from loguru import logger

PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from gmail_classifier.extractor import get_gmail_service
from gmail_classifier import config

# Fichero donde se guarda el estado del watch
WATCH_STATE_FILE = PROJECT_DIR / "data" / "gmail_watch.json"

# Renovar si quedan menos de N días para la expiración
RENEW_THRESHOLD_DAYS = 2


def load_watch_state() -> dict:
    """Carga el estado del watch guardado localmente."""
    if WATCH_STATE_FILE.exists():
        try:
            return json.loads(WATCH_STATE_FILE.read_text())
        except Exception:
            pass
    return {}


def save_watch_state(state: dict):
    """Guarda el estado del watch."""
    WATCH_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    WATCH_STATE_FILE.write_text(json.dumps(state, indent=2))


def get_expiration_info(state: dict) -> tuple[datetime | None, float | None]:
    """Devuelve (expiration_datetime, days_remaining) o (None, None) si no hay watch."""
    exp_ms = state.get("expiration")
    if not exp_ms:
        return None, None
    exp_dt = datetime.fromtimestamp(int(exp_ms) / 1000, tz=timezone.utc)
    now = datetime.now(tz=timezone.utc)
    days_remaining = (exp_dt - now).total_seconds() / 86400
    return exp_dt, days_remaining


def renew_watch(topic_name: str) -> dict:
    """Llama a Gmail API para renovar el watch."""
    service = get_gmail_service()
    request = {
        "labelIds": ["INBOX"],
        "topicName": topic_name,
    }
    result = service.users().watch(userId="me", body=request).execute()
    logger.success("Watch renovado: historyId={}, expiration={}ms", result.get("historyId"), result.get("expiration"))
    return result


def stop_watch() -> None:
    """Detiene el watch actual."""
    service = get_gmail_service()
    service.users().stop(userId="me").execute()
    logger.info("Watch detenido.")


def cmd_status(state: dict):
    exp_dt, days = get_expiration_info(state)
    if not exp_dt:
        print("⚠️  Sin watch activo. Ejecuta con --force para crear uno.")
        return
    status = "🟢 OK" if days > RENEW_THRESHOLD_DAYS else "🔴 URGENTE (caducará pronto)"
    print(f"\n{'='*50}")
    print(f"  Gmail Watch Status")
    print(f"{'='*50}")
    print(f"  Estado:       {status}")
    print(f"  Expira:       {exp_dt.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"  Días restantes: {days:.1f}")
    print(f"  History ID:   {state.get('historyId', '—')}")
    topic = state.get("topicName", "—")
    print(f"  Topic:        {topic}")
    print(f"{'='*50}\n")


def main():
    parser = argparse.ArgumentParser(description="Renueva el Gmail Watch de Pub/Sub")
    parser.add_argument("--force", action="store_true", help="Fuerza la renovación aunque no sea necesaria")
    parser.add_argument("--status", action="store_true", help="Muestra el estado actual sin renovar")
    parser.add_argument("--stop", action="store_true", help="Detiene el watch activo")
    parser.add_argument(
        "--topic",
        default=None,
        help="Nombre del topic de Pub/Sub (ej: projects/mi-proyecto/topics/gmail-notifications)",
    )
    args = parser.parse_args()

    logger.remove()
    logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level:^8}</level> | {message}")

    state = load_watch_state()

    if args.status:
        cmd_status(state)
        return

    if args.stop:
        stop_watch()
        state.pop("expiration", None)
        state.pop("historyId", None)
        save_watch_state(state)
        return

    # Determinar si hay que renovar
    exp_dt, days = get_expiration_info(state)

    if not args.force and exp_dt and days is not None and days > RENEW_THRESHOLD_DAYS:
        logger.info("Watch OK — quedan {:.1f} días, no es necesario renovar.", days)
        cmd_status(state)
        return

    # Necesitamos el topic para renovar
    topic_name = args.topic or state.get("topicName")
    if not topic_name:
        logger.error(
            "No se encontró el topic de Pub/Sub. Pásalo con --topic:\n"
            "  python scripts/renew_gmail_watch.py --topic projects/TU_PROYECTO/topics/gmail-notifications"
        )
        sys.exit(1)

    reason = "forzado" if args.force else f"caduca en {days:.1f} días" if days else "no había watch"
    logger.info("Renovando watch ({})…", reason)

    result = renew_watch(topic_name)

    # Guardar estado actualizado
    state.update({
        "historyId": result.get("historyId"),
        "expiration": result.get("expiration"),
        "topicName": topic_name,
        "renewed_at": datetime.now(tz=timezone.utc).isoformat(),
    })
    save_watch_state(state)
    cmd_status(state)


if __name__ == "__main__":
    main()
