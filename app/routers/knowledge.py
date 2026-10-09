"""Conocimiento del centro: ingesta → wiki RAG auto-mantenida."""
from __future__ import annotations

from fastapi import APIRouter

from .. import store
from ..models import KnowledgeIngest

router = APIRouter(prefix="/v1/business", tags=["knowledge"])


@router.post("/{business_id}/knowledge")
def ingest(business_id: str, body: KnowledgeIngest):
    doc = store.add_knowledge(business_id, body.source, body.content)
    # Las correcciones del dueño por WhatsApp entran por aquí (F2): nueva versión.
    return {"ok": True, **doc}


@router.post("/{business_id}/corrections")
def correction(business_id: str, body: KnowledgeIngest):
    """Corrección del dueño → actualiza la wiki (versión+1)."""
    doc = store.add_knowledge(business_id, f"correccion:{body.source}", body.content)
    return {"ok": True, "updated": True, **doc}
