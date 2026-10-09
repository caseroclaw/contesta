"""Orquestador de llamada: STT → RAG → memoria → respuesta (PLAN-MVP §8)."""
from __future__ import annotations

from . import store
from .adapters import Agenda, KnowledgeBase, Memory, Notifier
from .verticals import dental

kb = KnowledgeBase()
memory = Memory()
agenda = Agenda()
notifier = Notifier()


def greet(caller_name: str | None, from_number: str) -> str:
    prof = memory.recall(from_number)
    memory.remember(from_number)
    if caller_name:
        return (f"Hola {caller_name}, soy la recepcionista de la clínica. "
                f"{'¿Quiere el mismo hueco de siempre?' if prof['known'] else '¿En qué puedo ayudarle?'}")
    return ("Hola, soy la recepcionista virtual de la clínica. "
            "¿En qué puedo ayudarle?")


def process_turn(business_id: str, call_id: str, from_number: str,
                 transcript: str, caller_name: str | None = None) -> dict:
    """Procesa un turno transcrito y devuelve {reply, intent, escalate}."""
    call = store.get_call(call_id) or {}
    history = (call.get("transcript") or "")
    store.update_call(call_id, transcript=(history + f"\nLLAMANTE: {transcript}").strip())

    if dental.is_emergency(transcript):
        reply = ("Esto parece una emergencia: por favor llame al 112 ahora mismo. "
                 "Aviso a la clínica igualmente.")
        store.update_call(call_id, intent="emergencia", escalated=1)
        notifier.send_owner(f"⚠️ EMERGENCIA en llamada {call_id}: {transcript[:200]}")
        return {"reply": reply, "intent": "emergencia", "escalate": True}

    intent = dental.detect_intent(transcript)

    if intent == "urgencia":
        slots = agenda.slots(business_id, "urgencia")
        reply = (f"Entiendo que le duele. {dental.DISCLAIMER_CLINICO} "
                 f"Puedo ofrecerle hoy: {slots[0]} o {slots[1]}. ¿Le viene bien alguno?")
    elif intent == "precio":
        answer, _src = kb.answer(business_id, transcript)
        base = (answer or "la primera visita incluye valoración completa").rstrip(". ")
        reply = (f"Sobre precios: {base}. {dental.DISCLAIMER_CLINICO} "
                 "¿Quiere que le reserve una valoración sin compromiso?")
    elif intent == "horario":
        answer, _src = kb.answer(business_id, transcript)
        base = answer or "abrimos de lunes a viernes de 9:00 a 20:00"
        reply = f"Nuestro horario: {base}. ¿Le reservo un hueco?"
    elif intent == "cita":
        slots = agenda.slots(business_id, "primera visita")
        reply = (f"Tengo libre {slots[0]} y {slots[1]}. "
                 "Dígame cuál prefiere y se lo confirmo por WhatsApp.")
    elif intent == "humano":
        reply = ("Por supuesto, paso aviso ahora mismo para que le llamen "
                 "en menos de 30 minutos. ¿A qué número le devolvemos la llamada?")
        store.update_call(call_id, intent=intent, escalated=1)
        notifier.send_owner(f"📞 Llamada {call_id} pide humano: {transcript[:200]}")
        return {"reply": reply, "intent": intent, "escalate": True}
    else:
        # Regla anti-alucinación: si no lo sé, lo apunto (PLAN-MVP riesgo RAG).
        reply = ("Tomo nota de su consulta y se la paso a la clínica para que "
                 "le llamen con la respuesta exacta. ¿Me confirma su nombre y teléfono?")

    store.update_call(call_id, intent=intent)
    return {"reply": reply, "intent": intent, "escalate": False}
