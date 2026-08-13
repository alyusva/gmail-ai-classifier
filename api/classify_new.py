"""
Función Vercel (cron semanal): clasifica el correo nuevo de Gmail.

No usa base de datos: el correo "nuevo" se detecta con una simple query de
Gmail (`-label:IA`), porque todo email ya procesado lleva siempre la label
de marca MARKER_LABEL (por defecto "IA") además de su(s) categoría(s), que
son labels sueltas de nivel superior (sin prefijo compartido). Ver
vercel.json para la programación del cron y README.md para cómo configurar
las credenciales.
"""
import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gmail_classifier import config, gmail_auth  # noqa: E402
from gmail_classifier.applier import (  # noqa: E402
    apply_labels_to_message,
    create_gmail_label,
    get_existing_labels,
)
from gmail_classifier.classifier import classify_emails, get_client  # noqa: E402
from gmail_classifier.extractor import build_email_record, fetch_message_metadata  # noqa: E402

NEW_MAIL_QUERY = f"-label:{config.MARKER_LABEL} newer_than:10d"
MAX_PAGES = 5  # cota de seguridad (~2500 mensajes) por ejecución


def _ensure_labels(service) -> dict[str, str]:
    """Crea (si hace falta) la label de marca + una por categoría, sueltas
    de nivel superior (sin prefijo compartido).

    A diferencia de `applier.ensure_labels_exist`, no toca SQLite: aquí no
    hay base de datos local disponible. Devuelve {nombre: label_id}, p.ej.
    {"IA": "...", "Trabajo": "...", "Bancos/Finanzas": "...", ...}.
    """
    existing = get_existing_labels(service)
    all_categories = [*config.DEFAULT_TAXONOMY, config.FALLBACK_CATEGORY]
    names = [config.MARKER_LABEL, *all_categories]

    label_map = {}
    for name in names:
        if name in existing:
            label_map[name] = existing[name]
        else:
            label_map[name] = create_gmail_label(service, name)
            time.sleep(0.2)

    return label_map


def _list_new_message_ids(service) -> list[str]:
    ids = []
    page_token = None
    for _ in range(MAX_PAGES):
        kwargs = {"userId": "me", "q": NEW_MAIL_QUERY, "maxResults": 500}
        if page_token:
            kwargs["pageToken"] = page_token
        result = service.users().messages().list(**kwargs).execute()
        ids.extend(m["id"] for m in result.get("messages", []))
        page_token = result.get("nextPageToken")
        if not page_token:
            break
    return ids


def run_incremental_classification() -> dict:
    service = gmail_auth.get_service_from_refresh_token()
    label_map = _ensure_labels(service)
    marker_id = label_map[config.MARKER_LABEL]

    message_ids = _list_new_message_ids(service)
    if not message_ids:
        return {"found": 0, "processed": 0, "errors": 0, "distribution": {}}

    emails = []
    for msg_id in message_ids:
        msg = fetch_message_metadata(service, msg_id)
        if msg:
            emails.append(build_email_record(msg))
        time.sleep(0.02)

    client = get_client()
    distribution: dict[str, int] = {}
    processed = 0
    errors = 0

    for i in range(0, len(emails), config.CLASSIFY_BATCH_SIZE):
        batch = emails[i : i + config.CLASSIFY_BATCH_SIZE]
        results = classify_emails(client, batch, config.DEFAULT_TAXONOMY)
        time.sleep(1)

        for r in results:
            categories = r["labels"]
            add_ids = [marker_id]
            for cat in categories:
                lid = label_map.get(cat)
                if lid:
                    add_ids.append(lid)

            try:
                apply_labels_to_message(service, r["email_id"], add_ids)
                processed += 1
                for cat in categories:
                    distribution[cat] = distribution.get(cat, 0) + 1
                time.sleep(0.05)
            except Exception:
                errors += 1

    return {
        "found": len(message_ids),
        "processed": processed,
        "errors": errors,
        "distribution": distribution,
    }


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        expected_secret = os.getenv("CRON_SECRET", "")
        auth_header = self.headers.get("Authorization", "")

        if not expected_secret or auth_header != f"Bearer {expected_secret}":
            self._respond(401, {"error": "No autorizado"})
            return

        try:
            summary = run_incremental_classification()
            self._respond(200, {"ok": True, **summary})
        except Exception as e:
            self._respond(500, {"ok": False, "error": str(e)})

    def _respond(self, status: int, payload: dict):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)
