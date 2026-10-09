"""Panel del dueño. Métrica reina: citas recuperadas este mes."""
from __future__ import annotations

from fastapi import APIRouter

from .. import store

router = APIRouter(prefix="/v1/business", tags=["dashboard"])


@router.get("/{business_id}/dashboard")
def dashboard(business_id: str):
    calls = store.list_calls(business_id)
    apts = store.list_appointments(business_id)
    recovered = [a for a in apts if a["status"] == "confirmada"]
    conv = round(100 * len(recovered) / len(calls), 1) if calls else 0.0
    return {
        "business_id": business_id,
        "llamadas": len(calls),
        "citas_recuperadas": len(recovered),
        "conversion_llamada_cita_pct": conv,
        "escaladas": sum(1 for c in calls if c["escalated"]),
        "citas": apts,
    }
