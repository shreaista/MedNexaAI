/**
 * MedNexa AI — HTTP client for the public Phase 1 API.
 * Requires NEXT_PUBLIC_API_BASE_URL (no trailing slash required).
 */

const DEMO_FACILITY_ID =
  process.env.NEXT_PUBLIC_DEMO_FACILITY_ID ?? "";

/** Required for PUT /notes/{id}/sign (`signed_by` → users.user_id). */
export function getDefaultSigningUserId(): string | undefined {
  const v = process.env.NEXT_PUBLIC_SIGNING_USER_ID?.trim();
  return v || undefined;
}

function getBaseUrl(): string {
  const raw = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  if (!raw) {
    return "";
  }
  return raw.replace(/\/+$/, "");
}

function buildUrl(path: string): string {
  const base = getBaseUrl();
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${base}${p}`;
}

function formatDetailFromBody(data: unknown): string | null {
  if (typeof data !== "object" || data === null || !("detail" in data)) {
    return null;
  }
  const detail = (data as { detail: unknown }).detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const parts = detail.map((entry) => {
      if (
        typeof entry === "object" &&
        entry !== null &&
        "msg" in entry &&
        typeof (entry as { msg: unknown }).msg === "string"
      ) {
        return (entry as { msg: string }).msg;
      }
      return JSON.stringify(entry);
    });
    return parts.filter(Boolean).join("; ");
  }
  return JSON.stringify(detail);
}

/** Parse HTTP response body as JSON; throw with API `detail` when not OK. */
async function parseJsonFromResponse(res: Response): Promise<unknown> {
  const text = await res.text();
  if (!text) {
    if (!res.ok) {
      throw new Error(res.statusText || `Request failed (${res.status})`);
    }
    return undefined;
  }
  let data: unknown;
  try {
    data = JSON.parse(text);
  } catch {
    throw new Error("Invalid JSON response from API");
  }
  if (!res.ok) {
    throw new Error(formatDetailFromBody(data) ?? res.statusText ?? `Request failed (${res.status})`);
  }
  return data;
}

async function parseJson<T>(res: Response): Promise<T> {
  const data = await parseJsonFromResponse(res);
  return data as T;
}

export type HealthResponse = {
  status: string;
  service: string;
};

export type Facility = {
  facility_id: string;
  tenant_id: string;
  tenant_name: string;
  facility_name: string;
  facility_type: string | null;
  address_line1: string | null;
  city: string | null;
  state: string | null;
  zip_code: string | null;
  status: string;
};

export type CensusRow = {
  census_id: string;
  facility_id: string;
  patient_id: string;
  mrn: string | null;
  patient_name: string | null;
  first_name: string | null;
  last_name: string | null;
  date_of_birth: string | null;
  gender: string | null;
  payer_name: string | null;
  insurance_member_id: string | null;
  room_number: string | null;
  bed_number: string | null;
  care_level: string | null;
  visit_due_flag: boolean;
  unsigned_note_flag: boolean;
  missing_charge_flag: boolean;
  status: string | null;
};

export type PatientDetail = {
  patient_id: string;
  tenant_id: string;
  facility_id: string | null;
  facility_name: string | null;
  mrn: string | null;
  first_name: string | null;
  last_name: string | null;
  patient_name: string;
  date_of_birth: string | null;
  gender: string | null;
  payer_name: string | null;
  insurance_member_id: string | null;
  status: string | null;
  admission_date: string | null;
  discharge_date: string | null;
};

export type ProviderListItem = {
  provider_id: string;
  tenant_id: string;
  user_id: string | null;
  full_name: string;
  npi: string | null;
  specialty: string | null;
  provider_type: string | null;
  status: string;
};

export type BillingQueueItem = {
  queue_id: string;
  queue_status: string;
  priority: string;
  queue_reason: string;
  charge_id: string;
  charge_status: string;
  patient_id: string;
  patient_name: string;
  mrn: string | null;
  provider_name: string;
  primary_icd10: string | null;
  primary_cpt: string | null;
  readiness_score: string | number;
  readiness_status: string;
  created_at: string;
};

export type VisitCreatedOut = {
  visit_id: string;
  visit_status: string;
  patient_id: string;
  provider_id: string;
};

export type NoteCreatedOut = {
  note_id: string;
  note_status: string;
};

export type NoteSignedOut = {
  note_id: string;
  note_status: string;
  signed_at: string;
};

export type DiagnosisCreatedOut = {
  diagnosis_id: string;
};

export type ProcedureCreatedOut = {
  procedure_id: string;
};

export type ChargeWorkflowResult = {
  visit_id: string;
  visit_status: string;
  charge_id: string;
  queue_id: string;
  readiness_score: number;
  readiness_status: string;
  recommendation: string;
  total_units: number | null;
  documentation_support_status: string;
  message?: string | null;
};

export type CreateVisitPayload = {
  tenant_id: string;
  facility_id: string;
  patient_id: string;
  provider_id: string;
  visit_type: string;
  specialty: string;
  chief_complaint?: string | null;
};

export type CreateVisitNotePayload = {
  tenant_id: string;
  patient_id: string;
  provider_id: string;
  subjective?: string | null;
  objective?: string | null;
  assessment?: string | null;
  plan?: string | null;
  full_note?: string | null;
  ai_generated?: boolean;
};

export type SignNotePayload = {
  signed_by: string;
};

export type AddDiagnosisPayload = {
  tenant_id: string;
  icd10_code: string;
  description?: string | null;
  is_ai_suggested?: boolean;
};

export type AddProcedurePayload = {
  tenant_id: string;
  cpt_code: string;
  description?: string | null;
  modifier?: string | null;
  units?: string | number;
  is_ai_suggested?: boolean;
};

type FetchOptions = {
  cache?: RequestCache;
  next?: { revalidate?: number | false; tags?: string[] };
};

async function get<T>(path: string, options?: FetchOptions): Promise<T> {
  if (!getBaseUrl()) {
    throw new Error("NEXT_PUBLIC_API_BASE_URL is not configured.");
  }
  const res = await fetch(buildUrl(path), {
    method: "GET",
    headers: { Accept: "application/json" },
    cache: options?.cache ?? "no-store",
    next: options?.next,
  });
  return parseJson<T>(res);
}

async function mutateJson<T>(
  path: string,
  method: "POST" | "PUT",
  body: unknown,
): Promise<T> {
  if (!getBaseUrl()) {
    throw new Error("NEXT_PUBLIC_API_BASE_URL is not configured.");
  }
  const res = await fetch(buildUrl(path), {
    method,
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body ?? {}),
    cache: "no-store",
  });
  return parseJson<T>(res);
}

export function getBrowserApiBase(): string | undefined {
  const b = getBaseUrl();
  return b || undefined;
}

export async function getHealth(): Promise<HealthResponse> {
  return get<HealthResponse>("/health");
}

export async function getFacilities(): Promise<Facility[]> {
  return get<Facility[]>("/facilities");
}

export async function getFacilityCensus(facilityId: string): Promise<CensusRow[]> {
  return get<CensusRow[]>(`/facilities/${facilityId}/census`);
}

export async function getPatient(patientId: string): Promise<PatientDetail> {
  return get<PatientDetail>(`/patients/${patientId}`);
}

/** Normalize GET /providers body to a plain array (handles occasional wrapper shapes). */
function normalizeProvidersList(data: unknown): ProviderListItem[] {
  if (Array.isArray(data)) {
    return data as ProviderListItem[];
  }
  if (data !== null && typeof data === "object") {
    const o = data as Record<string, unknown>;
    if (Array.isArray(o.items)) return o.items as ProviderListItem[];
    if (Array.isArray(o.providers)) return o.providers as ProviderListItem[];
    if (Array.isArray(o.data)) return o.data as ProviderListItem[];
  }
  return [];
}

/**
 * GET `${NEXT_PUBLIC_API_BASE_URL}/providers` and return the JSON array (or normalized list).
 * Uses an explicit URL so browser requests match the working Azure endpoint.
 */
export async function getProviders(): Promise<ProviderListItem[]> {
  const base = getBaseUrl();
  if (!base) {
    throw new Error("NEXT_PUBLIC_API_BASE_URL is not configured.");
  }
  const url = `${base}/providers`;
  let res: Response;
  try {
    res = await fetch(url, {
      method: "GET",
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
  } catch (e) {
    const msg = e instanceof Error ? e.message : "Network error";
    throw new Error(msg);
  }
  const data = await parseJsonFromResponse(res);
  return normalizeProvidersList(data);
}

export async function getVisit(visitId: string): Promise<unknown> {
  return get<unknown>(`/visits/${visitId}`);
}

export async function createVisit(payload: CreateVisitPayload): Promise<VisitCreatedOut> {
  return mutateJson<VisitCreatedOut>("/visits", "POST", payload);
}

export async function createVisitNote(
  visitId: string,
  payload: CreateVisitNotePayload,
): Promise<NoteCreatedOut> {
  return mutateJson<NoteCreatedOut>(`/visits/${visitId}/notes`, "POST", payload);
}

export async function signNote(
  noteId: string,
  payload: SignNotePayload,
): Promise<NoteSignedOut> {
  return mutateJson<NoteSignedOut>(`/notes/${noteId}/sign`, "PUT", payload);
}

export async function addDiagnosis(
  visitId: string,
  payload: AddDiagnosisPayload,
): Promise<DiagnosisCreatedOut> {
  return mutateJson<DiagnosisCreatedOut>(`/visits/${visitId}/diagnoses`, "POST", payload);
}

export async function addProcedure(
  visitId: string,
  payload: AddProcedurePayload,
): Promise<ProcedureCreatedOut> {
  return mutateJson<ProcedureCreatedOut>(`/visits/${visitId}/procedures`, "POST", payload);
}

export async function submitCharge(visitId: string): Promise<ChargeWorkflowResult> {
  return mutateJson<ChargeWorkflowResult>(`/visits/${visitId}/charges`, "POST", {});
}

export async function getBillingQueue(): Promise<BillingQueueItem[]> {
  return get<BillingQueueItem[]>("/billing-queue");
}

export function getDemoFacilityIdHint(): string | null {
  return DEMO_FACILITY_ID || null;
}

export const apiClient = {
  createVisit,
  createNote: createVisitNote,
  signNote,
  addDiagnosis,
  addProcedure,
  submitChargeFromVisit: submitCharge,
};
