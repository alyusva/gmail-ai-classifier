"""
Módulo de base de datos Supabase (PostgreSQL) para almacenar emails y clasificaciones.
Expone la misma interfaz que db.py para que el resto del código sea agnóstico al backend.
"""
import json
from typing import Optional

from loguru import logger

from . import config


def _get_client():
    try:
        from supabase import create_client
    except ImportError:
        raise ImportError("Instala el cliente: pip install supabase")

    if not config.SUPABASE_URL or not config.SUPABASE_SERVICE_KEY:
        raise ValueError(
            "Configura SUPABASE_URL y SUPABASE_SERVICE_KEY en .env"
        )
    return create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_KEY)


def init_db():
    """Verifica la conexión con Supabase (las tablas se crean con las migraciones SQL)."""
    client = _get_client()
    client.table("emails").select("id").limit(1).execute()
    logger.info("Conexión a Supabase establecida ({})", config.SUPABASE_URL)


def save_progress(key: str, value: str):
    client = _get_client()
    client.table("progress").upsert({"key": key, "value": value}).execute()


def get_progress(key: str) -> Optional[str]:
    client = _get_client()
    res = client.table("progress").select("value").eq("key", key).maybe_single().execute()
    return res.data["value"] if res.data else None


def save_emails_batch(emails: list[dict]):
    """Inserta o ignora un batch de emails (upsert por id)."""
    client = _get_client()
    rows = [
        {
            "id": e["id"],
            "thread_id": e.get("thread_id", ""),
            "subject": e.get("subject", "(sin asunto)"),
            "sender": e.get("sender", ""),
            "sender_email": e.get("sender_email", ""),
            "snippet": e.get("snippet", ""),
            "date": e.get("date", ""),
            "labels_original": e.get("labels", []),
            "is_read": e.get("is_read", False),
        }
        for e in emails
    ]
    # onConflict="id" → upsert ignorando duplicados
    client.table("emails").upsert(rows, on_conflict="id").execute()


def get_unclassified_emails(limit: int = 50, offset: int = 0) -> list[dict]:
    """Emails que no tienen clasificación todavía."""
    client = _get_client()
    # Supabase no soporta LEFT JOIN directo en el SDK → usamos RPC o subquery.
    # Alternativa simple: obtener todos los email_id clasificados y excluirlos.
    classified = client.table("classifications").select("email_id").execute()
    classified_ids = {r["email_id"] for r in (classified.data or [])}

    res = (
        client.table("emails")
        .select("id, subject, sender, sender_email, snippet, date")
        .order("date", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )

    return [r for r in (res.data or []) if r["id"] not in classified_ids][:limit]


def save_classifications(classifications: list[dict]):
    """Guarda clasificaciones en batch (upsert por email_id)."""
    client = _get_client()
    rows = [
        {
            "email_id": c["email_id"],
            "labels": c["labels"],          # lista Python → text[] en Postgres
            "confidence": c.get("confidence", 0.0),
        }
        for c in classifications
    ]
    client.table("classifications").upsert(rows, on_conflict="email_id").execute()


def mark_as_applied(email_ids: list[str]):
    """Marca emails como etiquetados en Gmail."""
    client = _get_client()
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    for eid in email_ids:
        client.table("classifications").update(
            {"applied": True, "applied_at": now}
        ).eq("email_id", eid).execute()


def save_taxonomy_label(label: str, gmail_label_id: str = ""):
    client = _get_client()
    client.table("taxonomy").upsert(
        {"label": label, "gmail_label_id": gmail_label_id},
        on_conflict="label",
    ).execute()


def get_taxonomy() -> dict[str, str]:
    client = _get_client()
    res = client.table("taxonomy").select("label, gmail_label_id").execute()
    return {r["label"]: r["gmail_label_id"] for r in (res.data or [])}


def get_stats() -> dict:
    """Estadísticas generales."""
    client = _get_client()

    total = client.table("emails").select("id", count="exact").execute().count or 0
    classified = client.table("classifications").select("email_id", count="exact").execute().count or 0
    applied = (
        client.table("classifications")
        .select("email_id", count="exact")
        .eq("applied", True)
        .execute()
        .count or 0
    )

    # Distribución por etiqueta (labels es un array de texto en Postgres)
    rows = client.table("classifications").select("labels").execute().data or []
    distribution: dict[str, int] = {}
    for row in rows:
        for label in (row.get("labels") or []):
            distribution[label] = distribution.get(label, 0) + 1

    return {
        "total_emails": total,
        "classified": classified,
        "unclassified": total - classified,
        "applied": applied,
        "pending_apply": classified - applied,
        "distribution": dict(
            sorted(distribution.items(), key=lambda x: x[1], reverse=True)
        ),
    }


def get_unapplied_classifications(limit: int = 100) -> list[dict]:
    """Clasificaciones pendientes de aplicar, con datos del email."""
    client = _get_client()
    res = (
        client.table("classifications")
        .select("email_id, labels, emails(subject, sender)")
        .eq("applied", False)
        .limit(limit)
        .execute()
    )
    result = []
    for row in (res.data or []):
        email_info = row.get("emails") or {}
        result.append({
            "email_id": row["email_id"],
            "labels": row["labels"],
            "subject": email_info.get("subject", ""),
            "sender": email_info.get("sender", ""),
        })
    return result


def count_emails() -> int:
    client = _get_client()
    return client.table("emails").select("id", count="exact").execute().count or 0


def count_unclassified() -> int:
    client = _get_client()
    total = count_emails()
    classified = client.table("classifications").select("email_id", count="exact").execute().count or 0
    return total - classified
