#!/usr/bin/env node
// Reporte diario automático del dueño. Sin credenciales externas:
// solo lee GET /v1/business/{id}/dashboard y emite Markdown.
//
// Uso:
//   node scripts/daily-report.mjs --business demo-dental --api http://localhost:8000 [--out reporte-2026-10-10.md]
// Cron (todos los días 08:00):
//   0 8 * * * cd /ruta/contesta/panel && node scripts/daily-report.mjs --business <ID> >> /var/log/contesta-reporte.log

function arg(name, fallback) {
  const i = process.argv.indexOf(`--${name}`);
  return i >= 0 && process.argv[i + 1] ? process.argv[i + 1] : (process.env[name.toUpperCase()] ?? fallback);
}

const business = arg("business", process.env.CONTESTA_BUSINESS_ID ?? "demo-dental");
const api = (arg("api", process.env.CONTESTA_API_URL ?? "http://localhost:8000")).replace(/\/$/, "");
const out = arg("out", null);

const res = await fetch(`${api}/v1/business/${encodeURIComponent(business)}/dashboard`);
if (!res.ok) {
  console.error(`ERROR: dashboard ${res.status} en ${api}`);
  process.exit(1);
}
const d = await res.json();
const hoy = new Date().toISOString().slice(0, 10);

const citas = (d.citas ?? []).map((c) => `- ${c.slot} — ${c.service} (${c.status})`).join("\n") || "_Sin citas todavía._";

const md = `# Contesta — reporte diario ${hoy}
Negocio: ${d.business_id}

- ★ Citas recuperadas este mes: **${d.citas_recuperadas}**
- Llamadas hoy: **${d.llamadas_hoy}** (total: ${d.llamadas})
- Conversión llamada → cita: **${d.conversion_llamada_cita_pct}%**
- Escaladas a humano: **${d.escaladas}**

## Citas generadas
${citas}
`;

if (out) {
  const { writeFileSync } = await import("node:fs");
  writeFileSync(out, md);
  console.log(`Reporte escrito en ${out}`);
} else {
  process.stdout.write(md);
}
