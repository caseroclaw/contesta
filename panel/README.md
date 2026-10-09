# Panel del dueño (Next.js + TS)

Panel mínimo de la semana 2: el dueño ve sus citas sin ayuda.
Consume `GET /v1/business/{id}/dashboard`. Sin credenciales externas.

Muestra: llamadas del día, citas generadas, grabaciones,
conversión llamada → cita. Métrica reina: **citas recuperadas este mes**.

## Arranque

```bash
cd panel
cp .env.example .env.local   # ajuste CONTESTA_API_URL / CONTESTA_BUSINESS_ID
npm install
npm run dev                  # http://localhost:3001
```

Para ver otro negocio sin cambiar el `.env`: `http://localhost:3001/?business=<ID>`.

Producción: `npm run build && npm start`.

## Reporte diario automático

`scripts/daily-report.mjs` lee el dashboard y emite Markdown (sin credenciales):

```bash
node scripts/daily-report.mjs --business demo-dental --api http://localhost:8000
node scripts/daily-report.mjs --business demo-dental --out reporte-2026-10-10.md
```

Cron diario 08:00:

```
0 8 * * * cd /ruta/contesta/panel && node scripts/daily-report.mjs --business <ID> >> /var/log/contesta-reporte.log
```

## Notas

- `llamadas_hoy` se calcula en fecha UTC del servidor (ver `app/routers/dashboard.py`).
- En sandbox no hay audio real: la columna de grabaciones muestra la lista y
  el enlace «Escuchar» aparece solo cuando el backend devuelve `audio_uri`
  (piloto con SIP + consentimiento firmado).
