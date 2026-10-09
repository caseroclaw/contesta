"""Adapters: contratos de integración con stubs de sandbox.

Cada clase define el contrato que usará la implementación real
(VoiceStudio, WeKnora, Hindsight, trunk SIP, agenda, WhatsApp).
Se seleccionan por variable de entorno; el orquestador no cambia.
"""
from __future__ import annotations

import logging
import os

log = logging.getLogger("contesta.adapters")


class VoiceEngine:
    """STT + TTS + clonación. Real: debpalash/VoiceStudio on-premise/UE."""

    def transcribe(self, audio: bytes) -> str:
        log.debug("stub STT: %d bytes", len(audio))
        return ""

    def speak(self, text: str, voice_id: str) -> bytes:
        log.debug("stub TTS [%s]: %s", voice_id, text[:60])
        return b""


class KnowledgeBase:
    """RAG + wiki auto-mantenida. Real: Tencent/WeKnora sobre Postgres/pgvector."""

    def __init__(self):
        from . import store
        self._store = store

    def answer(self, business_id: str, query: str) -> tuple[str, str | None]:
        hits = self._store.search_knowledge(business_id, query)
        if not hits:
            return "", None
        best = hits[0]
        return best["content"][:500], best["source"]


class Memory:
    """Memoria por llamante. Real: vectorize-io/hindsight."""

    def __init__(self):
        self._seen: dict[str, int] = {}

    def recall(self, phone_hash: str) -> dict:
        n = self._seen.get(phone_hash, 0)
        return {"visits": n, "known": n > 0}

    def remember(self, phone_hash: str) -> None:
        self._seen[phone_hash] = self._seen.get(phone_hash, 0) + 1


class Agenda:
    """Huecos reales + reserva. Real: Google Calendar / Cal.com."""

    def slots(self, business_id: str, service: str, n: int = 2) -> list[str]:
        # Sandbox: huecos fijos. Piloto: consultar calendario real.
        return ["mañana 10:00", "martes 17:30"][:n]

    def book(self, business_id: str, slot: str, service: str, caller: str) -> str:
        log.info("stub reserva %s %s para %s", slot, service, caller)
        return slot


class Notifier:
    """WhatsApp/SMS al dueño y al llamante. Real: WhatsApp Business API."""

    def __init__(self):
        self.owner_mobile = os.environ.get("OWNER_MOBILE", "")
        self.fallback_mobile = os.environ.get("SIP_FALLBACK_MOBILE", "")

    def send_owner(self, text: str) -> None:
        log.info("→ dueño (%s): %s", self.owner_mobile or "stub", text[:120])

    def send_caller(self, to: str, text: str) -> None:
        log.info("→ llamante %s: %s", to, text[:120])


def sip_fallback_number() -> str:
    """Desvío al móvil si el sistema cae (PLAN-MVP riesgo trunk)."""
    return os.environ.get("SIP_FALLBACK_MOBILE", "")
