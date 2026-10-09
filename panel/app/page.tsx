import { getDashboard } from "../lib/api";

export const dynamic = "force-dynamic";

function fmtFecha(iso: string | null): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString("es-ES", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
  } catch {
    return iso;
  }
}

export default async function Page({ searchParams }: { searchParams: { business?: string } }) {
  const apiUrl = process.env.CONTESTA_API_URL ?? "http://localhost:8000";
  const businessId = searchParams.business ?? process.env.CONTESTA_BUSINESS_ID ?? "demo-dental";

  let dash;
  try {
    dash = await getDashboard(apiUrl, businessId);
  } catch (e) {
    return (
      <main>
        <header className="top"><h1>Contesta — Panel del dueño</h1></header>
        <div className="error">
          No se puede contactar con la API ({apiUrl}). Arranque el backend y recargue.
          <div className="muted">{String(e)}</div>
        </div>
      </main>
    );
  }

  return (
    <main>
      <header className="top">
        <div>
          <h1>Contesta — Panel del dueño</h1>
          <p>Negocio: {dash.business_id}</p>
        </div>
      </header>

      <div className="cards">
        <div className="card queen">
          <small>Citas recuperadas este mes ★</small>
          <strong>{dash.citas_recuperadas}</strong>
        </div>
        <div className="card">
          <small>Llamadas hoy</small>
          <strong>{dash.llamadas_hoy}</strong>
        </div>
        <div className="card">
          <small>Llamadas (total)</small>
          <strong>{dash.llamadas}</strong>
        </div>
        <div className="card">
          <small>Conversión llamada → cita</small>
          <strong>{dash.conversion_llamada_cita_pct}%</strong>
        </div>
        <div className="card">
          <small>Escaladas a humano</small>
          <strong>{dash.escaladas}</strong>
        </div>
      </div>

      <section>
        <h2>Citas generadas ({dash.citas.length})</h2>
        {dash.citas.length === 0 ? (
          <p className="muted">Aún no hay citas. Aparecerán aquí en cuanto la recepcionista confirme la primera.</p>
        ) : (
          <table>
            <thead><tr><th>Hueco</th><th>Servicio</th><th>Estado</th></tr></thead>
            <tbody>
              {dash.citas.map((c) => (
                <tr key={c.id}>
                  <td>{c.slot}</td>
                  <td>{c.service}</td>
                  <td><span className={`badge ${c.status === "confirmada" ? "ok" : ""}`}>{c.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section>
        <h2>Llamadas y grabaciones ({dash.llamadas_detalle.length})</h2>
        {dash.llamadas_detalle.length === 0 ? (
          <p className="muted">Sin llamadas registradas todavía.</p>
        ) : (
          <table>
            <thead><tr><th>Fecha</th><th>Llamante</th><th>Motivo</th><th>Cita</th><th>Grabación</th></tr></thead>
            <tbody>
              {dash.llamadas_detalle.map((l) => (
                <tr key={l.id}>
                  <td>{fmtFecha(l.started_at)}</td>
                  <td>{l.caller_name ?? "—"}{l.escalated ? ' ⚠' : ""}</td>
                  <td><span className="badge">{l.intent}</span></td>
                  <td>{l.appointment_id ? "✓" : "—"}</td>
                  <td>
                    {l.audio_uri ? <a href={l.audio_uri}>Escuchar</a> : <span className="muted">solo piloto</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <p className="muted">Las grabaciones con audio real están disponibles en el piloto (SIP + consentimiento). En sandbox se muestra la lista sin audio.</p>
      </section>
    </main>
  );
}
