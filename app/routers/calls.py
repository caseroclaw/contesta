"""Llamadas: webhook SIP, turnos y streaming media."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, WebSocket

from .. import orchestrator, store
from ..models import ConfirmAppointment, IncomingCall, Turn
from ..verticals.dental import AVISO_LEGAL

router = APIRouter(prefix="/v1/calls", tags=["calls"])


@router.post("/incoming")
def incoming(body: IncomingCall):
    call = store.create_call(body.business_id, body.from_number, body.caller_name)
    greeting = orchestrator.greet(body.caller_name, body.from_number)
    return {"call_id": call["id"], "legal_notice": AVISO_LEGAL, "greeting": greeting}


@router.post("/{call_id}/turn")
def turn(call_id: str, body: Turn):
    call = store.get_call(call_id)
    if not call:
        raise HTTPException(404, "llamada no encontrada")
    return orchestrator.process_turn(
        call["business_id"], call_id, call["from_number"],
        body.transcript, call.get("caller_name"))


@router.post("/{call_id}/confirm")
def confirm(call_id: str, body: ConfirmAppointment):
    call = store.get_call(call_id)
    if not call:
        raise HTTPException(404, "llamada no encontrada")
    apt = store.create_appointment(
        call["business_id"], call_id, body.slot, body.service)
    orchestrator.notifier.send_caller(
        call["from_number"],
        f"Cita confirmada: {body.service} el {body.slot}. ¡Le esperamos!")
    return apt


@router.websocket("/{call_id}/media")
async def media(ws: WebSocket, call_id: str):
    """Streaming bidireccional con el gateway SIP (audio real en piloto)."""
    await ws.accept()
    call = store.get_call(call_id)
    if not call:
        await ws.close(code=4404)
        return
    while True:
        try:
            frame = await ws.receive_json()
        except Exception:
            break
        transcript = frame.get("transcript", "")
        if not transcript:
            continue
        result = orchestrator.process_turn(
            call["business_id"], call_id, call["from_number"], transcript)
        await ws.send_json(result)
