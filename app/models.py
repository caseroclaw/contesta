"""Entidades del dominio (PLAN-MVP §9)."""
from __future__ import annotations

from pydantic import BaseModel, Field


class Business(BaseModel):
    id: str
    name: str
    vertical: str = "dental"  # dental | taller | despacho
    timezone: str = "Europe/Madrid"


class Caller(BaseModel):
    phone_hash: str
    name: str | None = None
    history_count: int = 0
    preferences: str = ""


class Call(BaseModel):
    id: str
    business_id: str
    from_number: str
    caller_name: str | None = None
    transcript: str = ""
    intent: str = "desconocida"
    appointment_id: str | None = None
    escalated: bool = False


class Appointment(BaseModel):
    id: str
    business_id: str
    call_id: str
    slot: str
    service: str
    status: str = "propuesta"  # propuesta | confirmada | cancelada


class KnowledgeDoc(BaseModel):
    id: str
    business_id: str
    source: str
    content: str
    version: int = 1


# ---- Requests ----

class IncomingCall(BaseModel):
    business_id: str = "demo-dental"
    from_number: str = "+34600000000"
    caller_name: str | None = None


class Turn(BaseModel):
    transcript: str = Field(min_length=1)


class KnowledgeIngest(BaseModel):
    source: str = "web"
    content: str = Field(min_length=1)


class VoiceEnroll(BaseModel):
    voice_name: str = "recepcionista"
    consent_signed: bool = False
    audio_sample_ref: str | None = None


class ConfirmAppointment(BaseModel):
    slot: str
    service: str = "primera visita"
