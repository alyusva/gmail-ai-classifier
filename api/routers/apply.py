"""
POST /apply  — Aplica etiquetas en Gmail para las clasificaciones pendientes.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.dependencies import get_supabase, require_auth, get_gmail_token
from api.gmail import build_gmail_service

router = APIRouter()

LABEL_PREFIX = "AutoSort"


class ApplyResponse(BaseModel):
    status:  str
    applied: int
    errors:  int


def _get_or_create_label(service, name: str, label_cache: dict) -> str:
    if name in label_cache:
        return label_cache[name]

    # Buscar label existente
    labels_res = service.users().labels().list(userId="me").execute()
    for lbl in labels_res.get("labels", []):
        if lbl["name"] == name:
            label_cache[name] = lbl["id"]
            return lbl["id"]

    # Crear label
    new_lbl = service.users().labels().create(userId="me", body={
        "name": name,
        "labelListVisibility": "labelShow",
        "messageListVisibility": "show",
    }).execute()
    label_cache[name] = new_lbl["id"]
    return new_lbl["id"]


@router.post("", response_model=ApplyResponse)
async def apply_labels(
    user_id: str = Depends(require_auth),
    supabase=Depends(get_supabase),
):
    token_data = get_gmail_token(user_id, supabase)
    service = build_gmail_service(token_data, user_id, supabase)

    # Cargar clasificaciones pendientes con su email_id
    pending_res = supabase.table("classifications") \
        .select("email_id, labels") \
        .eq("user_id", user_id) \
        .eq("applied", False) \
        .limit(200) \
        .execute()

    pending = pending_res.data or []
    applied = 0
    errors  = 0
    label_cache: dict[str, str] = {}
    applied_ids: list[str] = []

    for cls in pending:
        try:
            label_ids = [
                _get_or_create_label(service, f"{LABEL_PREFIX}/{lbl}", label_cache)
                for lbl in (cls["labels"] or [])
            ]
            if label_ids:
                service.users().messages().modify(
                    userId="me",
                    id=cls["email_id"],
                    body={"addLabelIds": label_ids},
                ).execute()
            applied_ids.append(cls["email_id"])
            applied += 1
        except Exception:
            errors += 1

    # Marcar como aplicados en bulk
    if applied_ids:
        from datetime import datetime, timezone
        supabase.table("classifications").update({
            "applied":    True,
            "applied_at": datetime.now(timezone.utc).isoformat(),
        }).in_("email_id", applied_ids).eq("user_id", user_id).execute()

    return ApplyResponse(status="ok", applied=applied, errors=errors)
