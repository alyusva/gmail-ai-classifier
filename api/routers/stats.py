"""
GET /stats  — Estadísticas del usuario.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.dependencies import get_supabase, require_auth

router = APIRouter()


class StatsResponse(BaseModel):
    total_emails:    int
    classified:      int
    unclassified:    int
    applied:         int
    pending_apply:   int
    plan:            str
    emails_limit:    int
    emails_used:     int
    distribution:    dict[str, int]


@router.get("", response_model=StatsResponse)
async def get_stats(
    user_id: str = Depends(require_auth),
    supabase=Depends(get_supabase),
):
    total    = supabase.table("emails").select("*", count="exact", head=True).eq("user_id", user_id).execute().count or 0
    cls_res  = supabase.table("classifications").select("applied", count="exact").eq("user_id", user_id).execute()
    classified   = cls_res.count or 0
    applied      = sum(1 for r in (cls_res.data or []) if r["applied"])
    pending_apply = classified - applied

    dist_res = supabase.table("classification_summary").select("label, email_count").eq("user_id", user_id).execute()
    distribution = {r["label"]: r["email_count"] for r in (dist_res.data or [])}

    sub_res = supabase.table("subscriptions").select("plan, emails_limit, emails_used").eq("user_id", user_id).single().execute()
    sub = sub_res.data or {"plan": "free", "emails_limit": 1000, "emails_used": 0}

    return StatsResponse(
        total_emails=total,
        classified=classified,
        unclassified=total - classified,
        applied=applied,
        pending_apply=pending_apply,
        plan=sub["plan"],
        emails_limit=sub["emails_limit"],
        emails_used=sub["emails_used"],
        distribution=distribution,
    )
