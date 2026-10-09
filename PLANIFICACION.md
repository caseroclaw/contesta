# PLANIFICACIÓN — Contesta (recepcionista por voz 24/7)

Ficha: https://claw.antoniocasero.com/portfolio/portfolio-2026-10-09-Q29udG ·
Repo: https://github.com/caseroclaw/contesta · Sandbox: `~/sandbox/contesta`

## 1. Objetivo

Piloto vendible en 2 semanas: 2 centros (vertical dental) atendiendo llamadas
reales fuera de horario con supervisión humana. Éxito = 10+ citas por centro y
cero quejas de "parece un robot malo".

## 2. Alcance → módulos (qué hay ya en el repo)

- **F1 Voz local** → `adapters.VoiceEngine` (stub) + `POST …/voice/enroll`
  (bloquea sin consentimiento firmado). Real: VoiceStudio on-premise/UE.
- **F2 Conocimiento** → `adapters.KnowledgeBase` + `POST …/knowledge` y
  `POST …/corrections` (la corrección del dueño crea versión+1 de la wiki).
  Real: WeKnora + pgvector.
- **F3 Memoria** → `adapters.Memory` (`recall`/`remember` por teléfono).
  Real: Hindsight. El saludo ya personaliza ("¿el mismo hueco de siempre?").
- **F4 Cualificación + agenda** → `orchestrator.process_turn` + guion
  `verticals/dental.py` + `POST …/calls/{id}/confirm`. Real: Calendar/Cal.com.
- **F5 Escalado humano** → urgencias, petición de humano y emergencias (112)
  avisan al dueño por WhatsApp con resumen. Fallback SIP al móvil si el
  sistema cae (`SIP_FALLBACK_MOBILE`).
- **F6 Panel** → `GET …/dashboard`: llamadas, citas recuperadas, conversión,
  escaladas. Métrica reina: **citas recuperadas/mes**.

Reglas anti-riesgo ya implementadas: aviso legal de grabación al descolgar,
derivación de emergencias al 112, disclaimer clínico (sin diagnósticos) y
**"si no lo sé, lo apunto"** en vez de alucinar precios/horarios.

## 3. Fases

**Semana 1 — Núcleo + telefonía (días 1–5)**
1. Contratar trunk SIP español con portabilidad + número piloto (día 1).
2. Gateway SIP → `WS /v1/calls/{id}/media` con Asterisk/FreeSWITCH (días 1–2).
3. VoiceStudio en VPS UE con GPU: benchmark latencia <1 s (días 2–3).
   Si no da la talla: TTS cloud UE temporal + reintento local en fase 2.
4. WeKnora + Postgres/pgvector: ingesta web/PDF de 2 clínicas piloto (días 3–4).
5. Agenda real (Google Calendar) + WhatsApp Business API (día 5).

**Semana 2 — Piloto supervisado (días 6–10)**
6. Clonación de voz con consentimiento firmado + aprobación de guion por cada
   dueño (día 6). Sin firma no hay piloto en ese centro.
7. Puesta en marcha fuera de horario con operador revisando el 100 % de las
   llamadas; correcciones por WhatsApp → wiki (días 7–10).
8. Panel en Next.js mínimo + reporte diario de citas recuperadas al dueño.
9. Cierre: 10+ citas/centro, satisfacción por llamada, decisión de pasar a
   190–320 €/mes (días 9–10).

**Después (fase 2)**: memoria entre llamadas (Hindsight completo), verticales
taller y despacho, recordatorios anti-no-show, multi-sede/franquicia con
ranking de recuperadas, modo 100 % on-premise, Dolibarr/Odoo + TPV de señal.

## 4. Esfuerzo y precio

7–10 días-hombre senior (lo delicado: SIP + latencia de voz local).
Setup 1.100–1.800 €/sede + 190–320 €/mes. Con 8 sedes ≈ 12.000 € + 2.000 €/mes.
El cliente lo paga con 2–3 primeras visitas recuperadas al mes.

## 5. Riesgos y mitigación

- Voz local lenta/mala → benchmark previo + fallback cloud UE temporal.
- Alucinación de precios → RAG con fuente + modo "lo apunto".
- RGPD/grabaciones → aviso legal, cifrado, borrado a petición, DPA.
- Rechazo al robot → voz de la casa + escalado a la primera fricción.
- Caída del sistema → desvío automático al móvil del dueño.

## 6. Desarrollo sandbox

Todo el trabajo vive aislado en `~/sandbox/contesta` (venv propio, SQLite
local, adapters stub sin credenciales). Rama `main` = estable; el piloto se
desarrolla en `dev`. CI (pytest) en cada push.
