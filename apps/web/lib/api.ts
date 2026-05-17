/**
 * MedNexa AI — HTTP client for the public Phase 1 API.
 * Requires NEXT_PUBLIC_API_BASE_URL (no trailing slash required).
 */

const DEMO_FACILITY_ID =
  process.env.NEXT_PUBLIC_DEMO_FACILITY_ID ?? ""; // optional UUID for dashboard fallback hints only

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

async function parseJson<T>(res: Response): Promise<T> {
  const text = await res.text();
  if (!text) {
    if (!res.ok) {
      throw new Error(res.statusText || `Request failed (${res.status})`);
    }
    return undefined as T;
  }
  let data: unknown;
  try {
    data = JSON.parse(text);
  } catch {
    throw new Error("Invalid JSON response from API");
  }
  if (!res.ok) {
    const detail =
      typeof data === "object" && data !== null && "detail" in data
        ? String((data as { detail: unknown }).detail)
        : res.statusText;
    throw new Error(detail || `Request failed (${res.status})`);
  }
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
  mrn: string | null;
  first_name: string | null;
  last_name: string | null;
  date_of_birth: string | null;
  gender: string | null;
  payer_name?: string | null;
  insurance_member_id?: string | null;
  status?: string | null;
  facility: {
    facility_id: string;
    tenant_id: string;
    facility_name: string;
    facility_type: string | null;
    address_line1: string | null;
    city: string | null;
    state: string | null;
    zip_code: string | null;
    status: string;
  } | null;
};

export type BillingQueueItem = {
  queue_id: string;
  queue_status: string;
  priority: string;
  charge_id: string;
  charge_status: string;
  patient_name: string;
  mrn: string | null;
  provider_name: string;
  primary_icd10: string | null;
  primary_cpt: string | null;
  readiness_score: string | number;
  readiness_status: string;
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

export async function getBillingQueue(): Promise<BillingQueueItem[]> {
  return get<BillingQueueItem[]>("/billing-queue");
}

/** Optional env hint for dashboard when API returns no facilities (non-hardcoded demo). */
export function getDemoFacilityIdHint(): string | null {
  return DEMO_FACILITY_ID || null;
}
