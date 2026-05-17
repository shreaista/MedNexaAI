"use client";

import { useCallback, useEffect, useState } from "react";
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
  getDefaultProviderId,
  type PatientDetail,
  type ProviderListItem,
} from "@/lib/api";
import { cn } from "@/lib/utils";

const inputClass =
  "w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-900 shadow-sm focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20";

function formatProviderOption(p: ProviderListItem): string {
  const bits = [p.full_name];
  if (p.specialty?.trim()) bits.push(p.specialty.trim());
  if (p.npi?.trim()) bits.push(`NPI ${p.npi.trim()}`);
  return bits.join(" · ");
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
  const signingUserId = getDefaultSigningUserId();
  const envProviderFallback = getDefaultProviderId();

  const [patient, setPatient] = useState<PatientDetail | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loadingPatient, setLoadingPatient] = useState(false);
  const [providers, setProviders] = useState<ProviderListItem[]>([]);
  const [resolvedProviderId, setResolvedProviderId] = useState<string | null>(null);
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

  const loadPatient = useCallback(async () => {
    if (!patientId || !facilityId) {
      setPatient(null);
      setLoadingPatient(false);
      setLoadError(null);
      return;
    }
    setLoadingPatient(true);
    setLoadError(null);
    try {
      if (!getBrowserApiBase()) throw new Error("NEXT_PUBLIC_API_BASE_URL is not configured.");
      const p = await getPatient(patientId);
      setPatient(p);
    } catch (e) {
      setPatient(null);
      setLoadError(e instanceof Error ? e.message : "Unable to load patient.");
    } finally {
      setLoadingPatient(false);
    }
  }, [patientId, facilityId]);

  useEffect(() => {
    void loadPatient();
  }, [loadPatient]);

  useEffect(() => {
    if (!patient) {
      setProviders([]);
      setResolvedProviderId(null);
      setProvidersError(null);
      return;
    }
    setLoadingProviders(true);
    setProvidersError(null);
    void getProviders(patient.tenant_id)
      .then((list) => {
        setProviders(list);
        const first = list[0];
        if (first) {
          setResolvedProviderId(first.provider_id);
        } else if (envProviderFallback) {
          setResolvedProviderId(envProviderFallback);
        } else {
          setResolvedProviderId(null);
        }
      })
      .catch((e) => {
        setProviders([]);
        setProvidersError(e instanceof Error ? e.message : "Could not load providers.");
        if (envProviderFallback) {
          setResolvedProviderId(envProviderFallback);
        } else {
          setResolvedProviderId(null);
        }
      })
      .finally(() => setLoadingProviders(false));
  }, [patient, envProviderFallback]);

  const mismatchFacility =
    patient && patient.facility_id && patient.facility_id !== initial?.facilityId;

  let disabledReason: string | null = null;
  if (!initial) {
    disabledReason =
      "Please select a patient from Census first (open Facilities → View Census → Open chart).";
  } else if (!apiOk) {
    disabledReason = "Configure NEXT_PUBLIC_API_BASE_URL in .env.local.";
  } else if (!resolvedProviderId && !loadingProviders) {
    disabledReason =
      "No providers returned for this tenant. Add a row to public.providers or set NEXT_PUBLIC_PROVIDER_ID.";
  } else if (!signingUserId) {
    disabledReason =
      "Set NEXT_PUBLIC_SIGNING_USER_ID to a users.user_id (required to sign the visit note).";
  } else if (mismatchFacility) {
    disabledReason = "facilityId in the URL does not match the patient’s attributed facility.";
  }

  async function submitWorkflow() {
    if (!initial || !patient || !resolvedProviderId || !signingUserId) return;

    setBusy(true);
    setSubmitError(null);
    setStepHint(null);

    const composedNote = fullNote.trim() || buildFullSoapNote({
      subjective,
      objective,
      assessment,
      plan,
    });

    try {
      setStepHint("Creating visit…");
      const visit = await createVisit({
        tenant_id: patient.tenant_id,
        facility_id: initial.facilityId,
        patient_id: patient.patient_id,
        provider_id: resolvedProviderId,
        visit_type: visitType.trim() || "visit",
        specialty: specialty.trim() || "general",
        chief_complaint: chiefComplaint.trim() || null,
      });

      setStepHint("Saving clinical note…");
      const note = await createVisitNote(visit.visit_id, {
        tenant_id: patient.tenant_id,
        patient_id: patient.patient_id,
        provider_id: resolvedProviderId,
        subjective: subjective.trim() || null,
        objective: objective.trim() || null,
        assessment: assessment.trim() || null,
        plan: plan.trim() || null,
        full_note: composedNote,
        ai_generated: false,
      });

      setStepHint("Signing note…");
      await signNote(note.note_id, { signed_by: signingUserId });

      setStepHint("Adding diagnosis…");
      await addDiagnosis(visit.visit_id, {
        tenant_id: patient.tenant_id,
        icd10_code: icd10Code.trim(),
        description: icd10Desc.trim() || null,
        is_ai_suggested: false,
      });

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
      setSubmitError(e instanceof Error ? e.message : "Workflow failed.");
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
          </CardHeader>
          <CardContent className="space-y-3">
            {loadingPatient ? (
              <p className="text-sm text-zinc-500">Loading patient…</p>
            ) : loadError ? (
              <div className="rounded-lg border border-rose-200 bg-rose-50/70 px-3 py-2 text-sm text-rose-900">
                {loadError}{" "}
                <button type="button" className="font-medium underline" onClick={() => void loadPatient()}>
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
                {providersError && envProviderFallback ? (
                  <p className="text-xs text-amber-800">
                    Provider directory unavailable ({providersError}). Using env fallback.
                  </p>
                ) : providersError && !envProviderFallback ? (
                  <p className="text-xs text-rose-800">{providersError}</p>
                ) : null}
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

      {disabledReason && initial ? (
        <Card className="border-amber-200 bg-amber-50/40">
          <CardContent className="py-4 text-sm text-amber-950">{disabledReason}</CardContent>
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
                {loadingProviders ? (
                  <p className="rounded-lg border border-zinc-200 bg-zinc-50 px-3 py-2 text-sm text-zinc-500">
                    Loading providers from GET /providers…
                  </p>
                ) : null}
                {!loadingProviders &&
                resolvedProviderId &&
                providers.some((x) => x.provider_id === resolvedProviderId) ? (
                  <select
                    className={inputClass}
                    value={resolvedProviderId}
                    onChange={(e) => {
                      const id = e.target.value;
                      setResolvedProviderId(id || null);
                    }}
                  >
                    {providers.map((p) => (
                      <option key={p.provider_id} value={p.provider_id}>
                        {formatProviderOption(p)}
                      </option>
                    ))}
                  </select>
                ) : null}
                {!loadingProviders &&
                resolvedProviderId &&
                !providers.some((x) => x.provider_id === resolvedProviderId) ? (
                  <p className="rounded-lg border border-amber-200 bg-amber-50/70 px-3 py-2 text-sm text-amber-950">
                    Using configured provider fallback (<code className="text-xs">NEXT_PUBLIC_PROVIDER_ID</code>
                    ). No directory row to display.
                  </p>
                ) : null}
                {!loadingProviders && !resolvedProviderId ? (
                  <p className="rounded-lg border border-rose-200 bg-rose-50/60 px-3 py-2 text-sm text-rose-900">
                    No active providers for this tenant. Seed providers or set{" "}
                    <code className="text-xs">NEXT_PUBLIC_PROVIDER_ID</code>.
                  </p>
                ) : null}
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
              placeholder="If empty on submit, built automatically from SOAP above."
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
              disabled={
                !!disabledReason || busy || !patient || loadingPatient || loadingProviders
              }
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
        </CardContent>
      </Card>
        </>
      ) : null}
    </div>
  );
}
