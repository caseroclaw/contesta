# Contesta — recepcionista por voz 24/7 para pymes

Atiende el 100 % de las llamadas 24/7 con la voz del negocio, responde con el
conocimiento real del centro (horarios, tarifas), recuerda a quien llama,
cualifica y agenda citas. Si hay duda o urgencia, escala al humano con un
resumen. Pensado para clínicas, talleres y despachos que pierden llamadas
fuera de horario.

Ficha de producto: https://claw.antoniocasero.com/portfolio/portfolio-2026-10-09-Q29udG
Planificación del piloto: [`PLANIFICACION.md`](PLANIFICACION.md)

> **Estado: MVP en sandbox (v0.1.0).** Funciona de punta a punta con
> simuladores (stubs). La telefonía real, la voz real y el RAG real aún no
> están conectados — ver [Limitaciones](#6-limitaciones-lo-que-no-hace-todavía).

---

## 1. Requisitos

- **Linux o macOS** con `python3` (3.11+) y `git`.
- **`uv`** (gestor de paquetes; lo usamos porque el `venv` del sistema suele
  fallar en Debian/Ubuntu por `ensurepip`). Si no lo tienes:
  `curl -LsSf astral.sh/uv/install.sh | sh` y luego cierra y abre la terminal
  (o `export PATH="$HOME/.local/bin:$PATH"`).
- **`curl`** para probar la API a mano (viene instalado casi siempre).
- Opcional: **Docker** solo si quieres el despliegue en contenedor.

No necesitas: cuenta SIP, GPU, claves de WhatsApp ni base de datos. Todo eso
son integraciones de la fase piloto; el sandbox las simula.

## 2. Instalación (paso a paso, desde cero)

```bash
# 1. Clonar el repo
git clone https://github.com/caseroclaw/contesta.git
cd contesta

# 2. Crear el entorno virtual aislado (tarda ~1 min la primera vez)
uv venv
uv pip install -r requirements.txt

# 3. (Opcional) Variables de entorno para el piloto real.
# En sandbox NO hace falta: con el .env vacío todo funciona simulado.
cp .env.example .env
```

Si `uv venv` falla: comprueba que usas el `uv` de `$HOME/.local/bin`
(`which uv`). No uses `pip install --break-system-packages`; ensucia el
Python del sistema.

## 3. Arranque

```bash
.venv/bin/uvicorn app.main:app --port 8091
```

Verás `Uvicorn running on http://127.0.0.1:8091`. Comprueba que vive:

```bash
curl http://localhost:8091/health
# {"status":"ok","service":"contesta"}
```

La base de datos `contesta.db` (SQLite) se crea sola al arrancar. Para
empezar de cero, para el servidor y bórrala: `rm contesta.db`.

## 4. Probar el flujo estrella (copia y pega, en orden)

Simula una llamada real fuera de horario: entra la llamada, pregunta precio,
pide cita, confirma y el dueño lo ve en el panel.

```bash
# 4.1. Dar de alta el conocimiento del centro (tarifas y horarios)
curl -X POST http://localhost:8091/v1/business/demo-dental/knowledge \
  -H 'Content-Type: application/json' \
  -d '{"source":"tarifas","content":"limpieza dental 60 euros, primera visita gratis. Abrimos de lunes a viernes de 9:00 a 20:00."}'

# 4.2. Dar de alta la voz del negocio (EXIGE consentimiento firmado)
curl -X POST http://localhost:8091/v1/business/demo-dental/voice/enroll \
  -H 'Content-Type: application/json' \
  -d '{"voice_name":"recepcionista","consent_signed":true}'
# Sin "consent_signed":true responde 400 y no registra nada. Así debe ser.

# 4.3. Entra la llamada (esto en el piloto lo dispara el trunk SIP)
curl -X POST http://localhost:8091/v1/calls/incoming \
  -H 'Content-Type: application/json' \
  -d '{"business_id":"demo-dental","from_number":"+34611111111","caller_name":"Carmen"}'
# Guarda el "call_id" de la respuesta (p. ej. call-81f82a43). Úsalo abajo como CID.
CID=call-XXXXXXXX

# 4.4. La llamante pregunta precio (en el piloto esto llega transcrito del audio)
curl -X POST http://localhost:8091/v1/calls/$CID/turn \
  -H 'Content-Type: application/json' \
  -d '{"transcript":"¿cuánto cuesta la limpieza dental?"}'
# Esperado: intent "precio" y respuesta con "60 euros" (dato REAL del paso 4.1).

# 4.5. Pide cita
curl -X POST http://localhost:8091/v1/calls/$CID/turn \
  -H 'Content-Type: application/json' \
  -d '{"transcript":"quiero pedir cita el martes"}'
# Esperado: intent "cita" con dos huecos (simulados en sandbox).

# 4.6. Confirma la cita (equivale a "sí, el martes a las 17:30")
curl -X POST http://localhost:8091/v1/calls/$CID/confirm \
  -H 'Content-Type: application/json' \
  -d '{"slot":"martes 17:30","service":"limpieza"}'

# 4.7. El dueño lo ve en el panel
curl http://localhost:8091/v1/business/demo-dental/dashboard
# Esperado: "citas_recuperadas":1 y conversion_llamada_cita_pct > 0.
```

Casos que también puedes probar:

```bash
# Emergencia → deriva al 112 y avisa al dueño (escalate:true)
curl -X POST http://localhost:8091/v1/calls/$CID/turn \
  -H 'Content-Type: application/json' \
  -d '{"transcript":"esto es una emergencia, llamo a la ambulancia"}'

# Pregunta sin respuesta en la base → NO inventa, toma nota
curl -X POST http://localhost:8091/v1/calls/$CID/turn \
  -H 'Content-Type: application/json' \
  -d '{"transcript":"¿hacen cirugía maxilofacial con láser?"}'

# El dueño corrige un dato por WhatsApp → crea versión nueva de la wiki
curl -X POST http://localhost:8091/v1/business/demo-dental/corrections \
  -H 'Content-Type: application/json' \
  -d '{"source":"tarifas","content":"limpieza dental 65 euros desde noviembre"}'
```

## 5. Tests automáticos

```bash
.venv/bin/python -m pytest -q
# 6 passed
```

Cubren: salud de la API, consentimiento de voz obligatorio, versionado de la
wiki, flujo completo llamada→cita→dashboard, escalado de emergencias y
no-alucinación. El CI de GitHub (`.github/workflows/ci.yml`) los ejecuta en
cada push.

## 6. Limitaciones: lo que NO hace todavía

Importante si enseñas el proyecto a un cliente o a otro dev:

1. **No hay telefonía real.** `WS /v1/calls/{id}/media` existe pero ningún
   gateway SIP le envía audio. Los turnos se prueban con texto (`/turn`).
   Falta: trunk SIP español + Asterisk/FreeSWITCH.
2. **No hay voz real.** `VoiceEngine` es un stub: no transcribe ni sintetiza
   nada. Falta: VoiceStudio on-premise/UE con GPU y benchmark de latencia
   (<1 s). Es el mayor riesgo técnico del proyecto.
3. **No hay RAG real.** La "búsqueda" es solape de palabras, no embeddings.
   Con pocos documentos funciona; con una web entera, no. Falta: WeKnora +
   Postgres/pgvector.
4. **No hay memoria persistente.** `Memory` vive en RAM: al reiniciar el
   servidor olvida a todos los llamantes. Falta: Hindsight (o tabla en
   Postgres).
5. **La agenda es ficticia.** Devuelve "mañana 10:00 / martes 17:30" fijos.
   Falta: Google Calendar / Cal.com.
6. **Los avisos no salen a ningún sitio.** `Notifier` solo escribe en el log.
   Falta: WhatsApp Business API + móvil del dueño.
7. **Base de datos SQLite.** Vale para sandbox y 1 sede; no para
   concurrencia ni multi-sede. Previsto: Postgres.
8. **Sin autenticación.** Los endpoints están abiertos; cualquiera con la URL
   puede crear citas. Antes del piloto: API keys + HTTPS.
9. **Un solo vertical.** Solo existe el guion dental (`app/verticals/`).
   Taller y despacho están pendientes.
10. **Sin panel web.** El "panel del dueño" es un JSON. El Next.js mínimo es
    tarea de la semana 2.

## 7. Qué se espera de cada pieza (contratos)

- `app/orchestrator.py::process_turn` — el pipeline. No cambiar su firma al
  conectar piezas reales; solo los adapters por dentro.
- `app/adapters.py` — cada clase documenta qué sistema real la sustituirá
  (VoiceStudio, WeKnora, Hindsight, trunk SIP, agenda, WhatsApp).
- `app/verticals/dental.py` — edita `INTENTS` y textos para afinar el guion
  sin tocar código de infraestructura.
- Reglas que no se negocian: aviso legal de grabación, 112 ante emergencias,
  sin diagnósticos (disclaimer clínico) y jamás inventar precios/horarios.

## 8. Estructura del repo

```
app/main.py routers/calls.py knowledge.py voice.py dashboard.py
app/models.py        entidades (Business, Caller, Call, Appointment…)
app/store.py         SQLite (prod: Postgres sin cambiar la API)
app/orchestrator.py  STT→RAG→memoria→respuesta
app/adapters.py      contratos + stubs sandbox
app/verticals/       guiones (dental; taller y despacho pendientes)
tests/test_api.py    6 tests del flujo estrella
Dockerfile + docker-compose.yml + .github/workflows/ci.yml
```

## 9. Problemas típicos

- `ModuleNotFoundError: pydantic_core` → estás usando el Python del sistema
  en vez del venv: usa siempre `.venv/bin/python` y `.venv/bin/uvicorn`.
- `uv venv` falla con `ensurepip` → instala `uv` (ver §1) y no uses
  `python3 -m venv` en Debian/Ubuntu.
- `CID` vacío o error 404 en `/turn` → el `call_id` cambia en cada llamada;
  repite el paso 4.3 y actualiza la variable.
- El dashboard sale a 0 → la `business_id` debe ser la misma en todos los
  pasos (`demo-dental`).
- Puerto ocupado (`Address already in use`) → hay otro uvicorn corriendo:
  `pkill -f "uvicorn app.main"` y reintenta.

## Precio del producto

Setup 1.100–1.800 €/sede + 190–320 €/mes. 2–3 primeras visitas recuperadas
pagan el mes.
