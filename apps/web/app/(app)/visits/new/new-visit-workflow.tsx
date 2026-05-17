"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";

import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  createVisit,
  createVisitNote,
  signNote,
  addDiagnosis,
  addProcedure,
  submitCharge,
  getDefaultSigningUserId,
  getPatient,
  getProviders,
  getBrowserApiBase,
  type PatientDetail,
  type ProviderListItem,
} from "@/lib/api";
import { cn } from "@/lib/utils";

const inputClass =
  "w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-900 shadow-sm focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20";

function formatProviderOption(p: ProviderListItem): string {
  const name = p.full_name?.trim() || "Unknown provider";
  const spec = p.specialty?.trim();
  return spec ? `${name} - ${spec}` : name;
}

function buildFullSoapNote(parts: {
  subjective: string;
  objective: string;
  assessment: string;
  plan: string;
}): string {
  const sec = (title: string, body: string) =>
    body.trim() ? `${title}:\n${body.trim().replace(/\s+$/mu, "")}\n\n` : "";
  let s =
    sec("Subjective", parts.subjective) +
    sec("Objective", parts.objective) +
    sec("Assessment", parts.assessment) +
    sec("Plan", parts.plan);
  s = s.trim();
  return s || "(No narrative entered)";
}

export function NewVisitWorkflow() {
  const router = useRouter();
  const sp = useSearchParams();
  const patientId = sp.get("patientId");
  const facilityId = sp.get("facilityId");
  const initial =
    patientId && facilityId ? { patientId, facilityId } : null;

  const apiOk = !!getBrowserApiBase();

  const [patient, setPatient] = useState<PatientDetail | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loadingPatient, setLoadingPatient] = useState(false);
  const [providersRaw, setProvidersRaw] = useState<ProviderListItem[]>([]);
  const [selectedProviderId, setSelectedProviderId] = useState<string | null>(null);
  const [loadingProviders, setLoadingProviders] = useState(false);
  const [providersError, setProvidersError] = useState<string | null>(null);

  const [visitType, setVisitType] = useState("Follow-up");
  const [specialty, setSpecialty] = useState("Internal Medicine");
  const [chiefComplaint, setChiefComplaint] = useState("");
  const [subjective, setSubjective] = useState("");
  const [objective, setObjective] = useState("");
  const [assessment, setAssessment] = useState("");
  const [plan, setPlan] = useState("");
  const [fullNote, setFullNote] = useState("");

  const [icd10Code, setIcd10Code] = useState("I10");
  const [icd10Desc, setIcd10Desc] = useState("Essential hypertension");
  const [cptCode, setCptCode] = useState("99309");
  const [cptDesc, setCptDesc] = useState("Subsequent nursing facility care");
  const [modifier, setModifier] = useState("");
  const [units, setUnits] = useState("1");

  const [submitError, setSubmitError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [stepHint, setStepHint] = useState<string | null>(null);
  const [successToast, setSuccessToast] = useState<string | null>(null);

  const loadEncounterData = useCallback(async () => {
    if (!patientId || !facilityId) {
      setPatient(null);
      setProvidersRaw([]);
      setSelectedProviderId(null);
      setLoadError(null);
      setProvidersError(null);
      setLoadingPatient(false);
      setLoadingProviders(false);
      return;
    }
    if (!getBrowserApiBase()) {
      setPatient(null);
      setProvidersRaw([]);
      setLoadError("NEXT_PUBLIC_API_BASE_URL is not configured.");
      setProvidersError("NEXT_PUBLIC_API_BASE_URL is not configured.");
      setLoadingPatient(false);
      setLoadingProviders(false);
      return;
    }

    setLoadingPatient(true);
    setLoadingProviders(true);
    setLoadError(null);
    setProvidersError(null);

    const [pres, prs] = await Promise.allSettled([getPatient(patientId), getProviders()]);

    if (pres.status === "fulfilled") {
      setPatient(pres.value);
      setLoadError(null);
    } else {
      setPatient(null);
      setLoadError(
        pres.reason instanceof Error ? pres.reason.message : "Unable to load patient.",
      );
    }

    if (prs.status === "fulfilled") {
      setProvidersRaw(prs.value);
      setProvidersError(null);
    } else {
      setProvidersRaw([]);
      setProvidersError(
        prs.reason instanceof Error ? prs.reason.message : "Could not load providers.",
      );
    }

    setLoadingPatient(false);
    setLoadingProviders(false);
  }, [patientId, facilityId]);

  useEffect(() => {
    void loadEncounterData();
  }, [loadEncounterData]);

  const bothFetchesComplete = !loadingPatient && !loadingProviders;

  const providersActive = useMemo(
    () =>
      providersRaw.filter((p) => String(p.status ?? "").toUpperCase() === "ACTIVE"),
    [providersRaw],
  );

  /** Tenant filtering only after patient + providers responses are both finished. */
  const providersFiltered = useMemo(() => {
    if (!bothFetchesComplete || !patient) {
      return [] as ProviderListItem[];
    }
    const tid = patient.tenant_id?.trim();
    if (!tid) {
      return providersActive;
    }
    return providersActive.filter((p) => String(p.tenant_id) === String(tid));
  }, [bothFetchesComplete, patient, providersActive]);

  const noProvidersForTenant =
    bothFetchesComplete &&
    !!patient?.tenant_id?.trim() &&
    providersActive.length > 0 &&
    providersFiltered.length === 0;

  useEffect(() => {
    if (loadingPatient || loadingProviders) return;
    if (!patient) {
      setSelectedProviderId(null);
      return;
    }
    if (!providersFiltered.length) {
      setSelectedProviderId(null);
      return;
    }
    setSelectedProviderId((prev) => {
      const ids = providersFiltered.map((p) => String(p.provider_id));
      if (prev && ids.includes(prev)) return prev;
      return String(providersFiltered[0]!.provider_id);
    });
  }, [loadingPatient, loadingProviders, patient, providersFiltered]);

  const mismatchFacility =
    patient && patient.facility_id && patient.facility_id !== initial?.facilityId;

  let structuralBlockReason: string | null = null;
  if (!initial) {
    structuralBlockReason =
      "Please select a patient from Census first (open Facilities → View Census → Open chart).";
  } else if (!apiOk) {
    structuralBlockReason = "Configure NEXT_PUBLIC_API_BASE_URL in .env.local.";
  } else if (mismatchFacility) {
    structuralBlockReason = "facilityId in the URL does not match the patient’s attributed facility.";
  }

  const unitsNum = Number(String(units).replaceAll(",", ""));
  const unitsOk = Number.isFinite(unitsNum) && unitsNum > 0;

  const formComplete =
    !!chiefComplaint.trim() &&
    !!subjective.trim() &&
    !!objective.trim() &&
    !!assessment.trim() &&
    !!plan.trim() &&
    !!fullNote.trim() &&
    !!icd10Code.trim() &&
    !!cptCode.trim() &&
    unitsOk;

  const patientLoaded = !!(patient && !loadingPatient && !loadError);

  const submitBlocked =
    !!structuralBlockReason ||
    busy ||
    !patient ||
    !!loadError ||
    loadingPatient ||
    loadingProviders ||
    !!providersError ||
    !selectedProviderId ||
    !formComplete;

  const submitHint =
    !initial || busy || structuralBlockReason
      ? null
      : providersError
        ? providersError
        : loadingPatient || loadingProviders
          ? null
          : loadError
            ? loadError
            : !patient
              ? null
              : !selectedProviderId
                ? null
                : !formComplete
                  ? "Fill chief complaint, all SOAP sections, full note, ICD-10, CPT, and units (> 0)."
                  : null;

  async function submitWorkflow() {
    if (!initial || !patient || !selectedProviderId) return;
    const signingUserIdLocal = getDefaultSigningUserId();
    if (!signingUserIdLocal) {
      setSubmitError(
        "Set NEXT_PUBLIC_SIGNING_USER_ID to a users.user_id (required to sign the visit note).",
      );
      return;
    }

    setBusy(true);
    setSubmitError(null);
    setStepHint(null);

    const composedNote = fullNote.trim() || buildFullSoapNote({
      subjective,
      objective,
      assessment,
      plan,
    });

    let workflowStep = "";
    try {
      workflowStep = "POST /visits";
      setStepHint("Creating visit…");
      const visit = await createVisit({
        tenant_id: patient.tenant_id,
        facility_id: initial.facilityId,
        patient_id: patient.patient_id,
        provider_id: selectedProviderId,
        visit_type: visitType.trim() || "visit",
        specialty: specialty.trim() || "general",
        chief_complaint: chiefComplaint.trim() || null,
      });

      workflowStep = `POST /visits/${visit.visit_id}/notes`;
      setStepHint("Saving clinical note…");
      const note = await createVisitNote(visit.visit_id, {
        tenant_id: patient.tenant_id,
        patient_id: patient.patient_id,
        provider_id: selectedProviderId,
        subjective: subjective.trim() || null,
        objective: objective.trim() || null,
        assessment: assessment.trim() || null,
        plan: plan.trim() || null,
        full_note: composedNote,
        ai_generated: false,
      });

      workflowStep = `PUT /notes/${note.note_id}/sign`;
      setStepHint("Signing note…");
      await signNote(note.note_id, { signed_by: signingUserIdLocal });

      workflowStep = `POST /visits/${visit.visit_id}/diagnoses`;
      setStepHint("Adding diagnosis…");
      await addDiagnosis(visit.visit_id, {
        tenant_id: patient.tenant_id,
        icd10_code: icd10Code.trim(),
        description: icd10Desc.trim() || null,
        is_ai_suggested: false,
      });

      workflowStep = `POST /visits/${visit.visit_id}/procedures`;
      setStepHint("Adding procedure…");
      const u = Number(String(units).replaceAll(",", ""));
      await addProcedure(visit.visit_id, {
        tenant_id: patient.tenant_id,
        cpt_code: cptCode.trim(),
        description: cptDesc.trim() || null,
        modifier: modifier.trim() || undefined,
        units: Number.isFinite(u) && u > 0 ? u : 1,
        is_ai_suggested: false,
      });

      workflowStep = `POST /visits/${visit.visit_id}/charges`;
      setStepHint("Submitting charge…");
      const wf = await submitCharge(visit.visit_id);

      setStepHint(null);
      setSuccessToast(
        `Charge queued · readiness ${wf.readiness_status} (${wf.readiness_score}). Redirecting…`,
      );
      setTimeout(() => {
        router.replace(
          `/billing-queue?charged=1&charge_id=${encodeURIComponent(wf.charge_id)}`,
        );
      }, 1600);
    } catch (e) {
      const detail = e instanceof Error ? e.message : String(e);
      setSubmitError(workflowStep ? `${workflowStep} — ${detail}` : detail || "Workflow failed.");
    } finally {
      setBusy(false);
      setStepHint(null);
    }
  }

  return (
    <div className="space-y-6">
      {successToast ? (
        <div
          className="fixed bottom-6 left-1/2 z-50 max-w-lg -translate-x-1/2 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-950 shadow-lg"
          role="status"
        >
          {successToast}
        </div>
      ) : null}

      {initial ? (
        <Card>
          <CardHeader>
            <CardTitle>Encounter context</CardTitle>
            <CardDescription className="font-mono text-xs text-zinc-500">
              patientId={initial.patientId}&nbsp;·&nbsp;facilityId={initial.facilityId}
            </CardDescription>
            <p className="pt-2 font-mono text-[10px] leading-snug text-zinc-400">
              patientLoaded={String(patientLoaded)} · providersRawCount={providersRaw.length} ·
              providersFilteredCount=
              {bothFetchesComplete ? providersFiltered.length : "…"} · selectedProviderId=
              {selectedProviderId ?? "none"}
            </p>
          </CardHeader>
          <CardContent className="space-y-3">
            {providersError ? (
              <div className="rounded-lg border border-rose-200 bg-rose-50/70 px-3 py-2 text-sm text-rose-900">
                Providers: {providersError}
              </div>
            ) : null}
            {loadingPatient ? (
              <p className="text-sm text-zinc-500">Loading patient…</p>
            ) : loadError ? (
              <div className="rounded-lg border border-rose-200 bg-rose-50/70 px-3 py-2 text-sm text-rose-900">
                Patient: {loadError}{" "}
                <button type="button" className="font-medium underline" onClick={() => void loadEncounterData()}>
                  Retry
                </button>
              </div>
            ) : patient ? (
              <>
                <p className="text-sm font-medium text-zinc-900">
                  {patient.patient_name}
                  {patient.mrn ? (
                    <span className="ml-2 font-mono text-xs text-zinc-500">MRN {patient.mrn}</span>
                  ) : null}
                </p>
                {mismatchFacility ? (
                  <p className="text-sm text-amber-900">
                    Warning: census URL facility differs from the patient record in the database.
                  </p>
                ) : null}
              </>
            ) : null}
          </CardContent>
        </Card>
      ) : null}

      {structuralBlockReason && initial ? (
        <Card className="border-amber-200 bg-amber-50/40">
          <CardContent className="py-4 text-sm text-amber-950">{structuralBlockReason}</CardContent>
        </Card>
      ) : null}

      {initial ? (
        <>
          {/* Visit details */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">A. Visit Details</CardTitle>
              <CardDescription>Creates the encounter via POST /visits</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4 sm:grid-cols-2">
              <label className="col-span-full space-y-1 sm:col-span-2">
                <span className="text-xs font-semibold uppercase text-zinc-500">Provider</span>
                {loadingPatient || loadingProviders ? (
                  <p className="rounded-lg border border-zinc-200 bg-zinc-50 px-3 py-2 text-sm text-zinc-500">
                    Loading patient and providers…
                  </p>
                ) : providersError ? (
                  <p className="rounded-lg border border-rose-200 bg-rose-50/60 px-3 py-2 text-sm text-rose-900">
                    Could not load provider directory — see Encounter context for the API error message.
                  </p>
                ) : bothFetchesComplete && loadError && !patient ? (
                  <p className="rounded-lg border border-rose-200 bg-rose-50/60 px-3 py-2 text-sm text-rose-900">
                    Patient record failed to load. Fix the error in Encounter context above.
                  </p>
                ) : bothFetchesComplete &&
                  patient &&
                  noProvidersForTenant ? (
                  <p className="rounded-lg border border-amber-200 bg-amber-50/70 px-3 py-2 text-sm text-amber-950">
                    No providers returned for this tenant.
                  </p>
                ) : bothFetchesComplete && patient && providersFiltered.length === 0 && !noProvidersForTenant ? (
                  <p className="rounded-lg border border-zinc-200 bg-zinc-50 px-3 py-2 text-sm text-zinc-700">
                    {providersRaw.length === 0
                      ? "GET /providers returned an empty list."
                      : providersActive.length === 0
                        ? "No ACTIVE providers in the directory response."
                        : "No providers available to select."}
                  </p>
                ) : bothFetchesComplete &&
                  patient &&
                  selectedProviderId &&
                  providersFiltered.some((x) => String(x.provider_id) === selectedProviderId) ? (
                  <select
                    className={inputClass}
                    value={selectedProviderId}
                    onChange={(e) => {
                      const id = e.target.value;
                      setSelectedProviderId(id || null);
                    }}
                  >
                    {providersFiltered.map((p) => (
                      <option key={String(p.provider_id)} value={String(p.provider_id)}>
                        {formatProviderOption(p)}
                      </option>
                    ))}
                  </select>
                ) : (
                  <p className="rounded-lg border border-zinc-200 bg-zinc-50 px-3 py-2 text-sm text-zinc-500">
                    Waiting for patient and provider data…
                  </p>
                )}
              </label>
              <label className="space-y-1">
                <span className="text-xs font-semibold uppercase text-zinc-500">Visit type</span>
                <input
                  value={visitType}
                  onChange={(e) => setVisitType(e.target.value)}
                  className={inputClass}
                />
              </label>
              <label className="space-y-1">
                <span className="text-xs font-semibold uppercase text-zinc-500">Specialty</span>
                <input value={specialty} onChange={(e) => setSpecialty(e.target.value)} className={inputClass} />
              </label>
              <label className="col-span-full space-y-1">
                <span className="text-xs font-semibold uppercase text-zinc-500">Chief complaint</span>
                <input
                  value={chiefComplaint}
                  onChange={(e) => setChiefComplaint(e.target.value)}
                  className={inputClass}
                  placeholder="Reason for visit / presenting concern"
                />
              </label>
            </CardContent>
          </Card>

      {/* Clinical note */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">B. Clinical Note</CardTitle>
          <CardDescription>
            SOAP sections and aggregate narrative (submitted as full_note to the API)
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {(["Subjective", "Objective", "Assessment", "Plan"] as const).map((label, i) => {
            const setter = [setSubjective, setObjective, setAssessment, setPlan][i]!;
            const value = [subjective, objective, assessment, plan][i]!;
            return (
              <label key={label} className="block space-y-2">
                <span className="text-xs font-medium uppercase text-zinc-500">{label}</span>
                <textarea
                  value={value}
                  onChange={(e) => setter(e.target.value)}
                  rows={label === "Subjective" || label === "Objective" ? 4 : 3}
                  className={inputClass}
                />
              </label>
            );
          })}
          <label className="block space-y-2">
            <span className="text-xs font-semibold uppercase text-zinc-500">Full note (aggregate)</span>
            <textarea
              value={fullNote}
              onChange={(e) => setFullNote(e.target.value)}
              rows={5}
              className={inputClass}
              placeholder="Required for submit (or Generate from SOAP after filling all sections)."
            />
          </label>
          <div>
            <Button
              type="button"
              variant="outline"
              onClick={() =>
                setFullNote(
                  buildFullSoapNote({ subjective, objective, assessment, plan }),
                )
              }
            >
              Generate AI Note Placeholder
            </Button>
            <p className="mt-2 text-xs text-zinc-500">
              Fills full note from SOAP fields (no external AI call).
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Coding */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">C. Coding</CardTitle>
          <CardDescription>Primary ICD-10 and CPT for the charge workflow</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <label className="space-y-1">
            <span className="text-xs font-semibold uppercase text-zinc-500">ICD-10 code</span>
            <input value={icd10Code} onChange={(e) => setIcd10Code(e.target.value)} className={inputClass} />
          </label>
          <label className="space-y-1">
            <span className="text-xs font-semibold uppercase text-zinc-500">ICD-10 description</span>
            <input value={icd10Desc} onChange={(e) => setIcd10Desc(e.target.value)} className={inputClass} />
          </label>
          <label className="space-y-1">
            <span className="text-xs font-semibold uppercase text-zinc-500">CPT code</span>
            <input value={cptCode} onChange={(e) => setCptCode(e.target.value)} className={inputClass} />
          </label>
          <label className="space-y-1">
            <span className="text-xs font-semibold uppercase text-zinc-500">CPT description</span>
            <input value={cptDesc} onChange={(e) => setCptDesc(e.target.value)} className={inputClass} />
          </label>
          <label className="space-y-1">
            <span className="text-xs font-semibold uppercase text-zinc-500">Modifier</span>
            <input value={modifier} onChange={(e) => setModifier(e.target.value)} className={inputClass} />
          </label>
          <label className="space-y-1">
            <span className="text-xs font-semibold uppercase text-zinc-500">Units</span>
            <input value={units} onChange={(e) => setUnits(e.target.value)} className={inputClass} />
          </label>
        </CardContent>
      </Card>

      {/* Submit */}
      <Card className="border-emerald-100 bg-emerald-50/20">
        <CardHeader>
          <CardTitle className="text-lg">D. Submit</CardTitle>
          <CardDescription>
            Visit → note → sign → diagnosis → procedure → charge, then billing queue
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {stepHint ? (
            <p className="text-sm font-medium text-emerald-900">{stepHint}</p>
          ) : null}
          {submitError ? (
            <div className="rounded-lg border border-rose-200 bg-rose-50/70 px-4 py-3 text-sm text-rose-900">
              {submitError}
            </div>
          ) : null}
          <div className="flex flex-wrap gap-3">
            <Button
              type="button"
              disabled={submitBlocked}
              className="bg-emerald-700 hover:bg-emerald-800"
              onClick={() => void submitWorkflow()}
            >
              {busy ? "Working…" : "Submit Visit and Charge"}
            </Button>
            <Link
              href={`/patients/${encodeURIComponent(initial.patientId)}${
                initial.facilityId ? `?facilityId=${encodeURIComponent(initial.facilityId)}` : ""
              }`}
              className={cn(buttonVariants({ variant: "outline" }), busy && "pointer-events-none opacity-50")}
            >
              Back to chart
            </Link>
          </div>
          {!busy && submitHint ? <p className="text-xs text-zinc-600">{submitHint}</p> : null}
        </CardContent>
      </Card>
        </>
      ) : null}
    </div>
  );
}
