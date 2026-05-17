import type { ReactNode } from "react";
import Link from "next/link";
import { notFound } from "next/navigation";

import { getPatient } from "@/lib/api";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export const dynamic = "force-dynamic";

function PlaceholderSection({
  title,
  children,
}: {
  title: string;
  children?: ReactNode;
}) {
  return (
    <Card className="border-dashed border-zinc-200 bg-zinc-50/40">
      <CardHeader className="pb-2">
        <CardTitle className="text-base">{title}</CardTitle>
        <CardDescription>Coming soon · Phase 2+ integration</CardDescription>
      </CardHeader>
      <CardContent className="text-sm text-zinc-500">
        {children ?? <p>Content will appear when clinical APIs are wired.</p>}
      </CardContent>
    </Card>
  );
}

export default async function PatientPage({
  params,
}: {
  params: Promise<{ patientId: string }>;
}) {
  const { patientId } = await params;

  let patient: Awaited<ReturnType<typeof getPatient>>;

  try {
    patient = await getPatient(patientId);
  } catch {
    notFound();
  }

  const displayName =
    [patient.first_name, patient.last_name].filter(Boolean).join(" ") ||
    "Patient";

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <p className="text-xs font-medium uppercase tracking-widest text-emerald-800/70">
          Patient chart
        </p>
        <h1 className="mt-1 text-2xl font-semibold text-zinc-900">{displayName}</h1>
        <p className="mt-0.5 font-mono text-xs text-zinc-400">{patient.patient_id}</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Demographics</CardTitle>
          <CardDescription>From GET /patients</CardDescription>
        </CardHeader>
        <CardContent>
          <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <div>
              <dt className="text-xs font-medium uppercase text-zinc-400">MRN</dt>
              <dd className="mt-1 font-mono text-sm text-zinc-900">
                {patient.mrn ?? "—"}
              </dd>
            </div>
            <div>
              <dt className="text-xs font-medium uppercase text-zinc-400">DOB</dt>
              <dd className="mt-1 text-sm text-zinc-900">
                {patient.date_of_birth ?? "—"}
              </dd>
            </div>
            <div>
              <dt className="text-xs font-medium uppercase text-zinc-400">Gender</dt>
              <dd className="mt-1 text-sm text-zinc-900">{patient.gender ?? "—"}</dd>
            </div>
            {patient.payer_name !== undefined ? (
              <div>
                <dt className="text-xs font-medium uppercase text-zinc-400">Payer</dt>
                <dd className="mt-1 text-sm text-zinc-900">
                  {patient.payer_name ?? "—"}
                </dd>
              </div>
            ) : null}
            {patient.insurance_member_id !== undefined ? (
              <div>
                <dt className="text-xs font-medium uppercase text-zinc-400">Member ID</dt>
                <dd className="mt-1 font-mono text-sm text-zinc-900">
                  {patient.insurance_member_id ?? "—"}
                </dd>
              </div>
            ) : null}
            {patient.status !== undefined ? (
              <div>
                <dt className="text-xs font-medium uppercase text-zinc-400">Status</dt>
                <dd className="mt-1">
                  <Badge variant="neutral">{patient.status ?? "—"}</Badge>
                </dd>
              </div>
            ) : null}
          </dl>
          {patient.facility ? (
            <div className="mt-6 rounded-lg border border-zinc-100 bg-zinc-50/80 p-4">
              <p className="text-xs font-medium uppercase text-zinc-400">Facility</p>
              <p className="mt-1 text-sm font-medium text-zinc-900">
                {patient.facility.facility_name}
              </p>
              <p className="text-xs text-zinc-500">
                {[patient.facility.city, patient.facility.state]
                  .filter(Boolean)
                  .join(", ") || "—"}
              </p>
            </div>
          ) : null}
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <PlaceholderSection title="Patient summary" />
        <PlaceholderSection title="Recent notes" />
        <PlaceholderSection title="Diagnoses" />
        <PlaceholderSection title="Charges" />
      </div>

      <PlaceholderSection title="AI Clinical Copilot">
        <p>
          Ambient documentation, coding suggestions, and policy checks will surface here
          using MedNexa AI services.
        </p>
      </PlaceholderSection>

      <div className="flex gap-3">
        <Link
          href="/facilities"
          className="text-sm font-medium text-emerald-800 hover:underline"
        >
          ← Facilities
        </Link>
      </div>
    </div>
  );
}
