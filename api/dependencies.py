"""
Dependencias compartidas de FastAPI: autenticación, Supabase, etc.
"""
import json
import os
from functools import lru_cache

from fastapi import Depends, HTTPException, Header, status
from supabase import create_client, Client

SUPABASE_URL      = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
FASTAPI_SECRET    = os.environ.get("FASTAPI_SECRET", "")


@lru_cache
def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def require_auth(
    x_user_id: str = Header(..., description="UUID del usuario autenticado"),
    x_api_secret: str = Header(..., description="Secret compartido Next.js ↔ FastAPI"),
) -> str:
    """
    Valida que la petición viene del backend Next.js (secret compartido)
    y devuelve el user_id.
    """
    if FASTAPI_SECRET and x_api_secret != FASTAPI_SECRET:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Secret inválido")
    if not x_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user_id requerido")
    return x_user_id


def get_gmail_token(user_id: str, supabase: Client = Depends(get_supabase)) -> dict:
    """
    Recupera y parsea el token Gmail del usuario desde Supabase.
    """
    res = supabase.table("gmail_tokens").select("token_data").eq("user_id", user_id).single().execute()
    if not res.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay token de Gmail para este usuario. El usuario debe autenticarse primero."
        )
    return json.loads(res.data["token_data"])


def check_quota(user_id: str, supabase: Client = Depends(get_supabase)) -> dict:
    """
    Verifica que el usuario no haya superado su cuota mensual.
    """
    res = supabase.table("subscriptions") \
        .select("plan, status, emails_limit, emails_used") \
        .eq("user_id", user_id).single().execute()

    sub = res.data or {"plan": "free", "status": "active", "emails_limit": 1000, "emails_used": 0}

    if sub["status"] not in ("active",):
        raise HTTPException(status_code=402, detail="Suscripción inactiva. Revisa tu plan.")

    if sub["emails_used"] >= sub["emails_limit"]:
        raise HTTPException(
            status_code=429,
            detail=f"Límite mensual alcanzado ({sub['emails_limit']} emails). Actualiza tu plan."
        )
    return sub
