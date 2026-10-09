# Contesta — recepcionista por voz 24/7 para pymes

Atiende el 100 % de las llamadas 24/7 con la voz del negocio, responde con el
conocimiento real del centro, recuerda a quien llama, cualifica y agenda citas.
Si hay duda o urgencia, escala al humano con resumen en 30 s.

Fuente: [ficha portfolio](https://claw.antoniocasero.com/portfolio/portfolio-2026-10-09-Q29udG) ·
Plan: [`PLANIFICACION.md`](PLANIFICACION.md)

## Estructura

```
app/
  main.py          FastAPI + routers
  models.py        Entidades (Business, Caller, Call, Appointment, KnowledgeDoc, Correction)
  store.py         Persistencia SQLite (prod: Postgres/pgvector)
  orchestrator.py  Pipeline de turno: STT→RAG→memoria→TTS→respuesta
  adapters.py      Interfaces SIP / voz / RAG / memoria / agenda / WhatsApp (stubs sandbox)
  verticals/       Guiones por vertical (dental, taller, despacho)
  routers/         calls, knowledge, voice, dashboard
tests/             pytest (API + orquestador)
```

## Sandbox (desarrollo aislado)

```bash
cd ~/sandbox/contesta
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8091
pytest -q
```

Los adapters son **stubs**: simulan VoiceStudio, WeKnora, Hindsight, trunk SIP,
agenda y WhatsApp sin credenciales. Se sustituyen por implementaciones reales
vía variables de entorno (ver `.env.example`) sin tocar el orquestador.

## Endpoints

- `POST /v1/calls/incoming` — webhook SIP: crea la llamada y devuelve el saludo
- `POST /v1/calls/{id}/turn` — procesa un turno transcrito (sandbox sin SIP)
- `WS /v1/calls/{id}/media` — streaming bidireccional con el gateway SIP
- `POST /v1/business/{id}/knowledge` — ingesta web/PDF/tarifas → wiki RAG
- `POST /v1/business/{id}/voice/enroll` — alta de voz (exige consentimiento firmado)
- `GET /v1/business/{id}/dashboard` — citas recuperadas, conversión, llamadas

## Precio

Setup 1.100–1.800 €/sede + 190–320 €/mes. 2–3 primeras visitas recuperadas pagan el mes.
