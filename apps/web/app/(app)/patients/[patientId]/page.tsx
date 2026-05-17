import type { ReactNode } from "react";
import Link from "next/link";
import { notFound } from "next/navigation";

import { AppBreadcrumbs } from "@/components/layout/breadcrumbs";
import { getPatient } from "@/lib/api";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export const dynamic = "force-dynamic";

function formatDate(raw: string | null | undefined): string {
  if (!raw) return "—";
  if (/^\d{4}-\d{2}-\d{2}$/.test(raw)) {
    const [y, m, d] = raw.split("-").map(Number);
    return new Date(y, (m ?? 1) - 1, d).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
      timeZone: "UTC",
    });
  }
  const t = Date.parse(raw);
  return Number.isNaN(t) ? raw : new Date(t).toLocaleDateString();
}

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
        <CardDescription>Live data will connect in a future release</CardDescription>
      </CardHeader>
      <CardContent className="text-sm text-zinc-500">
        {children ?? <p>No data from API for this section yet.</p>}
      </CardContent>
    </Card>
  );
}

export default async function PatientPage({
  params,
  searchParams,
}: {
  params: Promise<{ patientId: string }>;
  searchParams?: Promise<{ facilityId?: string }>;
}) {
  const [{ patientId }, qp] = await Promise.all([
    params,
    searchParams ?? Promise.resolve({} as { facilityId?: string }),
  ]);

  let patient: Awaited<ReturnType<typeof getPatient>>;

  try {
    patient = await getPatient(patientId);
  } catch {
    notFound();
  }

  const facilityForVisit =
    qp.facilityId?.trim() || patient.facility_id?.trim() || null;

  const displayName = patient.patient_name || "Patient";

  const newVisitHref = facilityForVisit
    ? `/visits/new?patientId=${encodeURIComponent(patient.patient_id)}&facilityId=${encodeURIComponent(facilityForVisit)}`
    : null;

  const crumbItems = [
    { label: "Dashboard", href: "/dashboard" as const },
    { label: "Facilities", href: "/facilities" as const },
    ...(qp.facilityId
      ? [{ label: "Census", href: `/facilities/${qp.facilityId}/census` as const }]
      : []),
    { label: "Patient chart" },
  ];

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <AppBreadcrumbs items={crumbItems} />

      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 flex-1 space-y-4">
          <div>
            <p className="text-xs font-medium uppercase tracking-widest text-emerald-800/70">
              Patient chart
            </p>
            <h1 className="mt-1 text-2xl font-semibold tracking-tight text-zinc-900">
              {displayName}
            </h1>
          </div>
          <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm">
            <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <div>
                <dt className="text-xs font-medium uppercase text-zinc-400">MRN</dt>
                <dd className="mt-1 font-mono text-sm text-zinc-900">{patient.mrn ?? "—"}</dd>
              </div>
              <div>
                <dt className="text-xs font-medium uppercase text-zinc-400">DOB</dt>
                <dd className="mt-1 text-sm text-zinc-900">{formatDate(patient.date_of_birth)}</dd>
              </div>
              <div>
                <dt className="text-xs font-medium uppercase text-zinc-400">Gender</dt>
                <dd className="mt-1 text-sm text-zinc-900">{patient.gender ?? "—"}</dd>
              </div>
              <div>
                <dt className="text-xs font-medium uppercase text-zinc-400">Payer</dt>
                <dd className="mt-1 text-sm text-zinc-900">{patient.payer_name ?? "—"}</dd>
              </div>
              <div>
                <dt className="text-xs font-medium uppercase text-zinc-400">Insurance member ID</dt>
                <dd className="mt-1 font-mono text-sm text-zinc-900">
                  {patient.insurance_member_id ?? "—"}
                </dd>
              </div>
              <div>
                <dt className="text-xs font-medium uppercase text-zinc-400">Facility</dt>
                <dd className="mt-1 text-sm font-medium text-zinc-900">
                  {patient.facility_name ?? "—"}
                </dd>
              </div>
              <div>
                <dt className="text-xs font-medium uppercase text-zinc-400">Admission date</dt>
                <dd className="mt-1 text-sm text-zinc-900">{formatDate(patient.admission_date)}</dd>
              </div>
            </dl>
            <p className="mt-4 font-mono text-[11px] text-zinc-400">{patient.patient_id}</p>
            {qp.facilityId?.trim() && patient.facility_id ? (
              qp.facilityId.trim() !== patient.facility_id ? (
                <p className="mt-3 max-w-xl text-xs text-amber-900">
                  URL facility differs from attributed facility — the visit workflow will still validate
                  against the database.
                </p>
              ) : null
            ) : null}
          </div>
        </div>
        {newVisitHref ? (
          <Link
            href={newVisitHref}
            className={cn(
              buttonVariants({ variant: "default" }),
              "h-fit w-fit shrink-0 bg-emerald-700 shadow-sm hover:bg-emerald-800",
            )}
          >
            Start New Visit
          </Link>
        ) : (
          <div className="max-w-xs shrink-0 rounded-lg border border-amber-200 bg-amber-50/70 px-3 py-2 text-xs text-amber-950">
            Start new visit requires facility context — open the chart from census or assign a facility.
          </div>
        )}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <PlaceholderSection title="AI Patient Summary">
          <p>MedNexa AI will summarize longitudinal context here.</p>
        </PlaceholderSection>
        <PlaceholderSection title="Recent Visits" />
        <PlaceholderSection title="Diagnoses" />
        <PlaceholderSection title="Charges" />
      </div>

      <div className="flex flex-wrap gap-4 border-t border-zinc-100 pt-4">
        <Link href="/facilities" className="text-sm font-medium text-emerald-800 hover:underline">
          ← Facilities
        </Link>
        <Link href="/billing-queue" className="text-sm font-medium text-emerald-800 hover:underline">
          Billing Queue
        </Link>
        {facilityForVisit ? (
          <Link
            href={`/facilities/${facilityForVisit}/census`}
            className="text-sm font-medium text-emerald-800 hover:underline"
          >
            ← Census
          </Link>
        ) : null}
      </div>
    </div>
  );
}
