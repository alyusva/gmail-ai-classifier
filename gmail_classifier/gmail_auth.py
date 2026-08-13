"""
Autenticación de Gmail sin flujo interactivo, a partir de un refresh_token
guardado como variable de entorno. Pensado para entornos sin filesystem
persistente ni navegador disponible (la función cron de Vercel).

El uso local/CLI sigue usando extractor.get_gmail_service(), que hace el
flujo OAuth interactivo la primera vez y cachea el token en data/token.json.
"""
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from loguru import logger

from . import config

TOKEN_URI = "https://oauth2.googleapis.com/token"


def get_service_from_refresh_token():
    """Construye el servicio de Gmail API a partir de GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET y GOOGLE_REFRESH_TOKEN (variables de entorno).

    El refresh_token se obtiene una vez corriendo el flujo interactivo local
    (extractor.get_gmail_service) y leyendo el campo "refresh_token" de
    data/token.json.
    """
    client_id = os.getenv("GOOGLE_CLIENT_ID", "")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")
    refresh_token = os.getenv("GOOGLE_REFRESH_TOKEN", "")

    missing = [
        name
        for name, value in [
            ("GOOGLE_CLIENT_ID", client_id),
            ("GOOGLE_CLIENT_SECRET", client_secret),
            ("GOOGLE_REFRESH_TOKEN", refresh_token),
        ]
        if not value
    ]
    if missing:
        raise RuntimeError(
            f"Faltan variables de entorno para autenticar con Gmail: {', '.join(missing)}"
        )

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri=TOKEN_URI,
        client_id=client_id,
        client_secret=client_secret,
        scopes=config.GMAIL_SCOPES,
    )
    creds.refresh(Request())
    logger.info("Credenciales de Gmail obtenidas vía refresh_token")

    return build("gmail", "v1", credentials=creds)
