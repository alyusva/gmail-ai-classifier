"""
Módulo de extracción de emails desde Gmail API.
"""
import base64
import email.utils
import re
import time
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
from tqdm import tqdm

from . import config, db


def get_gmail_service():
    """Autentica y devuelve el servicio de Gmail API."""
    creds = None

    if config.TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(
            str(config.TOKEN_PATH), config.GMAIL_SCOPES
        )

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Renovando token de acceso...")
            creds.refresh(Request())
        else:
            if not config.CREDENTIALS_PATH.exists():
                logger.error(
                    "No se encontró credentials.json en {}",
                    config.CREDENTIALS_PATH,
                )
                raise FileNotFoundError(
                    f"Coloca tu credentials.json en {config.CREDENTIALS_PATH}"
                )
            logger.info("Iniciando flujo de autenticación OAuth2...")
            flow = InstalledAppFlow.from_client_secrets_file(
                str(config.CREDENTIALS_PATH), config.GMAIL_SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Guardar token
        config.TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        config.TOKEN_PATH.write_text(creds.to_json())
        logger.info("Token guardado en {}", config.TOKEN_PATH)

    return build("gmail", "v1", credentials=creds)


def parse_sender(from_header: str) -> tuple[str, str]:
    """Extrae nombre y email del header From."""
    if not from_header:
        return "", ""
    name, addr = email.utils.parseaddr(from_header)
    return name or addr, addr


def extract_headers(headers: list[dict]) -> dict:
    """Extrae headers relevantes de un mensaje."""
    result = {}
    for h in headers:
        name = h.get("name", "").lower()
        if name == "from":
            result["from"] = h.get("value", "")
        elif name == "subject":
            result["subject"] = h.get("value", "")
        elif name == "date":
            result["date"] = h.get("value", "")
    return result


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
)
def fetch_message_metadata(service, msg_id: str) -> Optional[dict]:
    """Obtiene metadata de un mensaje individual."""
    try:
        msg = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=msg_id,
                format="metadata",
                metadataHeaders=["From", "Subject", "Date"],
            )
            .execute()
        )
        return msg
    except Exception as e:
        logger.warning("Error obteniendo mensaje {}: {}", msg_id, e)
        raise


def extract_all_emails(max_emails: Optional[int] = None):
    """
    Extrae todos los emails de Gmail y los guarda en SQLite.
    Soporta reanudación mediante page token.
    """
    db.init_db()
    service = get_gmail_service()

    # Recuperar progreso
    page_token = db.get_progress("extract_page_token")
    total_extracted = int(db.get_progress("extract_count") or 0)

    if page_token:
        logger.info(
            "Reanudando extracción desde page_token guardado ({} emails previos)",
            total_extracted,
        )

    # Primero obtener el total estimado
    try:
        profile = service.users().getProfile(userId="me").execute()
        total_messages = profile.get("messagesTotal", 0)
        logger.info("Total de mensajes en la cuenta: ~{}", total_messages)
    except Exception:
        total_messages = 0

    if max_emails:
        total_messages = min(total_messages, max_emails)

    pbar = tqdm(
        initial=total_extracted,
        total=total_messages or None,
        desc="Extrayendo emails",
        unit="emails",
    )

    try:
        while True:
            # Listar IDs de mensajes
            kwargs = {
                "userId": "me",
                "maxResults": config.GMAIL_MAX_RESULTS_PER_PAGE,
            }
            if page_token:
                kwargs["pageToken"] = page_token

            results = service.users().messages().list(**kwargs).execute()
            messages = results.get("messages", [])

            if not messages:
                logger.info("No hay más mensajes.")
                break

            # Obtener metadata de cada mensaje en este batch
            batch_emails = []
            for msg_stub in messages:
                msg_id = msg_stub["id"]

                try:
                    msg = fetch_message_metadata(service, msg_id)
                except Exception as e:
                    logger.error("Saltando mensaje {} tras reintentos: {}", msg_id, e)
                    continue

                headers = extract_headers(msg.get("payload", {}).get("headers", []))
                sender_name, sender_email = parse_sender(headers.get("from", ""))
                label_ids = msg.get("labelIds", [])

                batch_emails.append(
                    {
                        "id": msg_id,
                        "thread_id": msg.get("threadId", ""),
                        "subject": headers.get("subject", "(sin asunto)"),
                        "sender": sender_name,
                        "sender_email": sender_email,
                        "snippet": msg.get("snippet", ""),
                        "date": headers.get("date", ""),
                        "labels": label_ids,
                        "is_read": "UNREAD" not in label_ids,
                    }
                )

                # Rate limiting suave
                time.sleep(0.02)

            # Guardar batch
            if batch_emails:
                db.save_emails_batch(batch_emails)
                total_extracted += len(batch_emails)
                pbar.update(len(batch_emails))

            # Guardar progreso
            next_page = results.get("nextPageToken")
            db.save_progress("extract_count", str(total_extracted))

            if next_page:
                db.save_progress("extract_page_token", next_page)
                page_token = next_page
            else:
                # Limpiar progreso al terminar
                db.save_progress("extract_page_token", "")
                break

            if max_emails and total_extracted >= max_emails:
                logger.info("Alcanzado límite de {} emails", max_emails)
                break

            logger.debug(
                "Batch procesado. Total: {} emails extraídos", total_extracted
            )

    finally:
        pbar.close()

    logger.success(
        "Extracción completada. {} emails guardados en la base de datos.",
        total_extracted,
    )
    return total_extracted
