"""Tests del flujo estrella: llamada → cualifica → cita → dashboard."""
import os
import tempfile

db = tempfile.mktemp(suffix=".db")
os.environ["CONTESTA_DB"] = db

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)
BIZ = "demo-dental"


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_voice_enroll_requires_consent():
    r = client.post(f"/v1/business/{BIZ}/voice/enroll",
                    json={"voice_name": "recepcionista"})
    assert r.status_code == 400
    r = client.post(f"/v1/business/{BIZ}/voice/enroll",
                    json={"voice_name": "recepcionista", "consent_signed": True})
    assert r.json()["ok"] is True


def test_knowledge_ingest_versions():
    for i in range(2):
        r = client.post(f"/v1/business/{BIZ}/knowledge",
                        json={"source": "tarifas",
                              "content": f"limpieza dental 60 euros v{i}"})
        assert r.json()["version"] == i + 1


def test_full_call_flow():
    # 0. Conocimiento del centro (cada test es autosuficiente)
    client.post(f"/v1/business/{BIZ}/knowledge",
                json={"source": "tarifas-flujo",
                      "content": "limpieza dental 60 euros, primera visita gratis"})
    # 1. Entra la llamada fuera de horario
    inc = client.post("/v1/calls/incoming",
                      json={"business_id": BIZ, "from_number": "+34611111111",
                            "caller_name": "Carmen"}).json()
    cid = inc["call_id"]
    assert "Carmen" in inc["greeting"]

    # 2. Pregunta precio → responde con conocimiento real, sin inventar
    t = client.post(f"/v1/calls/{cid}/turn",
                    json={"transcript": "¿cuánto cuesta la limpieza dental?"}).json()
    assert t["intent"] == "precio" and "60 euros" in t["reply"]

    # 3. Pide cita → propone huecos reales
    t = client.post(f"/v1/calls/{cid}/turn",
                    json={"transcript": "quiero pedir cita el martes"}).json()
    assert t["intent"] == "cita" and "17:30" in t["reply"]

    # 4. Confirma → cita en calendario + WhatsApp
    apt = client.post(f"/v1/calls/{cid}/confirm",
                      json={"slot": "martes 17:30",
                            "service": "limpieza"}).json()
    assert apt["status"] == "confirmada"

    # 5. El dueño lo ve en el panel
    dash = client.get(f"/v1/business/{BIZ}/dashboard").json()
    assert dash["citas_recuperadas"] >= 1


def test_emergency_escalates():
    cid = client.post("/v1/calls/incoming",
                      json={"business_id": BIZ,
                            "from_number": "+34622222222"}).json()["call_id"]
    t = client.post(f"/v1/calls/{cid}/turn",
                    json={"transcript": "esto es una emergencia, llamo a la ambulancia"}).json()
    assert t["escalate"] is True and "112" in t["reply"]


def test_unknown_question_does_not_hallucinate():
    cid = client.post("/v1/calls/incoming",
                      json={"business_id": BIZ,
                            "from_number": "+34633333333"}).json()["call_id"]
    t = client.post(f"/v1/calls/{cid}/turn",
                    json={"transcript": "¿hacen cirugía maxilofacial con láser?"}).json()
    assert "tomo nota" in t["reply"].lower()
