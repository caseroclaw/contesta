"""Panel del dueño. Métrica reina: citas recuperadas este mes."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from .. import store

router = APIRouter(prefix="/v1/business", tags=["dashboard"])


def _hoy_utc() -> str:
    return datetime.now(timezone.utc).date().isoformat()


@router.get("/{business_id}/dashboard")
def dashboard(business_id: str):
    calls = store.list_calls(business_id)
    apts = store.list_appointments(business_id)
    recovered = [a for a in apts if a["status"] == "confirmada"]
    conv = round(100 * len(recovered) / len(calls), 1) if calls else 0.0
    hoy = _hoy_utc()
    detalle = [
        {
            "id": c["id"],
            "started_at": c.get("started_at"),
            "caller_name": c.get("caller_name"),
            "intent": c.get("intent", "desconocida"),
            "escalated": bool(c.get("escalated")),
            "appointment_id": c.get("appointment_id"),
            # Sandbox: sin audio real; en piloto es la URI de la grabación.
            "audio_uri": c.get("audio_uri"),
        }
        for c in calls
    ]
    return {
        "business_id": business_id,
        "llamadas": len(calls),
        "llamadas_hoy": sum(1 for c in calls if (c.get("started_at") or "")[:10] == hoy),
        "citas_recuperadas": len(recovered),
        "conversion_llamada_cita_pct": conv,
        "escaladas": sum(1 for c in calls if c["escalated"]),
        "llamadas_detalle": detalle,
        "citas": apts,
    }
