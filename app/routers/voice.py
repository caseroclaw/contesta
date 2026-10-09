"""Alta de voz del negocio. Sin consentimiento firmado no hay clonación."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .. import store
from ..models import VoiceEnroll

router = APIRouter(prefix="/v1/business", tags=["voice"])


@router.post("/{business_id}/voice/enroll")
def enroll(business_id: str, body: VoiceEnroll):
    if not body.consent_signed:
        raise HTTPException(400, "consentimiento de voz no firmado: alta denegada")
    return {"ok": True, **store.enroll_voice(business_id, body.voice_name)}
