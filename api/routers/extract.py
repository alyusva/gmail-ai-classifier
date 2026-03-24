"""
POST /extract  — Descarga emails de Gmail para un usuario concreto.
"""
from fastapi import APIRouter, Depends, BackgroundTasks
from pydantic import BaseModel

from api.dependencies import get_supabase, require_auth, get_gmail_token, check_quota
from api.gmail import build_gmail_service

router = APIRouter()


class ExtractRequest(BaseModel):
    max_emails: int = 500


class ExtractResponse(BaseModel):
    status: str
    extracted: int
    skipped: int


def _parse_sender(from_header: str) -> tuple[str, str]:
    """Extrae (nombre, email) del header From."""
    import re
    m = re.match(r'^(.*?)\s*<([^>]+)>', from_header)
    if m:
        return m.group(1).strip().strip('"'), m.group(2).strip()
    return "", from_header.strip()


@router.post("", response_model=ExtractResponse)
async def extract_emails(
    body: ExtractRequest,
    user_id: str = Depends(require_auth),
    supabase=Depends(get_supabase),
    quota: dict = Depends(check_quota),
):
    token_data = get_gmail_token(user_id, supabase)
    service = build_gmail_service(token_data, user_id, supabase)

    extracted = 0
    skipped = 0
    page_token = None
    batch: list[dict] = []

    while extracted + skipped < body.max_emails:
        params: dict = {"userId": "me", "maxResults": min(100, body.max_emails - extracted - skipped)}
        if page_token:
            params["pageToken"] = page_token

        result = service.users().messages().list(**params).execute()
        messages = result.get("messages", [])
        if not messages:
            break

        for msg_ref in messages:
            msg = service.users().messages().get(
                userId="me", id=msg_ref["id"],
                format="metadata",
                metadataHeaders=["From", "Subject", "Date"],
            ).execute()

            headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
            sender_raw = headers.get("From", "")
            sender_name, sender_email = _parse_sender(sender_raw)

            batch.append({
                "id":              msg["id"],
                "thread_id":       msg.get("threadId"),
                "subject":         headers.get("Subject"),
                "sender":          sender_name,
                "sender_email":    sender_email,
                "snippet":         msg.get("snippet", "")[:300],
                "date":            headers.get("Date"),
                "labels_original": msg.get("labelIds", []),
                "is_read":         "UNREAD" not in msg.get("labelIds", []),
                "user_id":         user_id,
            })

            if len(batch) >= 50:
                res = supabase.table("emails").upsert(batch, on_conflict="id").execute()
                extracted += len(batch)
                batch = []

        page_token = result.get("nextPageToken")
        if not page_token:
            break

    # Último batch
    if batch:
        supabase.table("emails").upsert(batch, on_conflict="id").execute()
        extracted += len(batch)

    # Actualizar contador de uso
    supabase.table("subscriptions").update({
        "emails_used": quota["emails_used"] + extracted
    }).eq("user_id", user_id).execute()

    return ExtractResponse(status="ok", extracted=extracted, skipped=skipped)
