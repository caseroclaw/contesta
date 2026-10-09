"""Guion del vertical dental (piloto). Taller y despacho reutilizan la estructura."""

AVISO_LEGAL = (
    "Le informo de que esta llamada puede ser grabada para mejorar el servicio. "
    "Si es una emergencia médica, llame al 112."
)

DISCLAIMER_CLINICO = (
    "Le doy información general de la clínica; el diagnóstico lo hace "
    "el profesional en consulta."
)

# (intención, palabras clave)
INTENTS = {
    "urgencia": ["dolor", "urgente", "urgencia", "roto", "rotura", "sangr", "hinchad", "golpe"],
    "emergencia": ["no puedo respirar", "desmay", "112", "ambulancia", "emergencia"],
    "precio": ["precio", "cuánto", "cuesta", "tarifa", "presupuesto", "vale"],
    "horario": ["horario", "abrís", "abierto", "cerrado", "cuándo", "hora"],
    "cita": ["cita", "reservar", "hueco", "disponible", "pedir hora", "me apunto"],
    "humano": ["persona", "humano", "responsable", "director", "que me llamen", "operador"],
}


def detect_intent(text: str) -> str:
    t = text.lower()
    for intent, kws in INTENTS.items():
        if any(k in t for k in kws):
            return intent
    return "desconocida"


def is_emergency(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in INTENTS["emergencia"])
