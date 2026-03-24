"""
POST /classify  — Clasifica emails sin clasificar de un usuario con Claude.
"""
import os
import json
from fastapi import APIRouter, Depends
from pydantic import BaseModel

import anthropic
from api.dependencies import get_supabase, require_auth

router = APIRouter()

ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
BATCH_SIZE      = int(os.environ.get("CLASSIFY_BATCH_SIZE", "50"))

DEFAULT_TAXONOMY = [
    "Newsletters", "Compras/Pedidos", "Bancos/Finanzas", "Trabajo",
    "Redes Sociales", "Suscripciones/SaaS", "Notificaciones/Alertas",
    "Personal", "Spam/Promociones", "Desarrollo/Tech", "Formación/Educación",
    "Viajes/Transporte", "Gobierno/Administración", "Salud", "Otros",
]

SYSTEM_PROMPT = """Eres un clasificador de emails. Dado un lote de emails,
asigna 1-3 categorías a cada uno de la taxonomía proporcionada.
Responde ÚNICAMENTE con un JSON array con objetos {email_id, labels, confidence}.
confidence es un float entre 0 y 1."""


class ClassifyResponse(BaseModel):
    status: str
    classified: int


@router.post("", response_model=ClassifyResponse)
async def classify_emails(
    user_id: str = Depends(require_auth),
    supabase=Depends(get_supabase),
):
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    # Cargar taxonomía del usuario (o usar la por defecto)
    tax_res = supabase.table("taxonomy").select("label").eq("user_id", user_id).execute()
    taxonomy = [r["label"] for r in (tax_res.data or [])] or DEFAULT_TAXONOMY

    # Obtener emails sin clasificar
    classified_total = 0
    offset = 0

    while True:
        emails_res = supabase.table("emails") \
            .select("id, subject, sender, sender_email, snippet") \
            .eq("user_id", user_id) \
            .not_.in_("id", supabase.table("classifications").select("email_id").eq("user_id", user_id)) \
            .range(offset, offset + BATCH_SIZE - 1) \
            .execute()

        emails = emails_res.data or []
        if not emails:
            break

        # Construir prompt
        emails_text = "\n".join(
            f"ID:{e['id']} | De:{e.get('sender_email','')} | Asunto:{e.get('subject','')} | Snippet:{e.get('snippet','')[:150]}"
            for e in emails
        )
        prompt = f"Taxonomía: {json.dumps(taxonomy)}\n\nEmails:\n{emails_text}"

        msg = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        try:
            raw = msg.content[0].text.strip()
            # Extraer JSON si viene envuelto en ```
            if "```" in raw:
                raw = raw.split("```")[1].lstrip("json").strip()
            results = json.loads(raw)
        except Exception:
            offset += BATCH_SIZE
            continue

        rows = [
            {
                "email_id":      r["email_id"],
                "labels":        r.get("labels", ["Otros"]),
                "confidence":    float(r.get("confidence", 0.8)),
                "applied":       False,
                "user_id":       user_id,
            }
            for r in results if r.get("email_id")
        ]
        if rows:
            supabase.table("classifications").upsert(rows, on_conflict="email_id").execute()
            classified_total += len(rows)

        offset += BATCH_SIZE
        if len(emails) < BATCH_SIZE:
            break

    return ClassifyResponse(status="ok", classified=classified_total)
