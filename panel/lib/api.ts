export interface LlamadaDetalle {
  id: string;
  started_at: string | null;
  caller_name: string | null;
  intent: string;
  escalated: boolean;
  appointment_id: string | null;
  audio_uri: string | null;
}

export interface Cita {
  id: string;
  business_id: string;
  call_id: string;
  slot: string;
  service: string;
  status: string;
}

export interface Dashboard {
  business_id: string;
  llamadas: number;
  llamadas_hoy: number;
  citas_recuperadas: number;
  conversion_llamada_cita_pct: number;
  escaladas: number;
  llamadas_detalle: LlamadaDetalle[];
  citas: Cita[];
}

export async function getDashboard(apiUrl: string, businessId: string): Promise<Dashboard> {
  const res = await fetch(
    `${apiUrl.replace(/\/$/, "")}/v1/business/${encodeURIComponent(businessId)}/dashboard`,
    { cache: "no-store" }
  );
  if (!res.ok) throw new Error(`Dashboard ${res.status}: ${await res.text()}`);
  return res.json() as Promise<Dashboard>;
}
