"""
Helper para construir el servicio de Gmail usando el token almacenado en Supabase.
"""
import json
import tempfile
import os

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from supabase import Client


def build_gmail_service(token_data: dict, user_id: str, supabase: Client):
    """
    Construye el servicio Gmail a partir del token_data guardado.
    Refresca el access_token si ha expirado y actualiza Supabase.
    """
    creds = Credentials(
        token=token_data.get("token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=token_data.get("client_id") or os.environ.get("GOOGLE_CLIENT_ID"),
        client_secret=token_data.get("client_secret") or os.environ.get("GOOGLE_CLIENT_SECRET"),
        scopes=token_data.get("scopes", [
            "https://www.googleapis.com/auth/gmail.modify",
            "https://www.googleapis.com/auth/gmail.labels",
        ]),
    )

    # Refrescar si ha expirado
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        # Persistir el nuevo access_token en Supabase
        updated = json.loads(json.dumps(token_data))
        updated["token"] = creds.token
        supabase.table("gmail_tokens").update({
            "token_data": json.dumps(updated),
            "updated_at": "now()",
        }).eq("user_id", user_id).execute()

    return build("gmail", "v1", credentials=creds)
