import Link from "next/link";

import {
  getDemoFacilityIdHint,
  getFacilities,
  getFacilityCensus,
  getHealth,
} from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export const dynamic = "force-dynamic";

function StatCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: string | number;
  hint?: string;
}) {
  return (
    <Card className="overflow-hidden">
      <CardContent className="p-5">
        <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
          {label}
        </p>
        <p className="mt-2 text-3xl font-semibold tabular-nums text-zinc-900">
          {value}
        </p>
        {hint ? (
          <p className="mt-1 text-xs text-zinc-400">{hint}</p>
        ) : null}
      </CardContent>
    </Card>
  );
}

export default async function DashboardPage() {
  let health: Awaited<ReturnType<typeof getHealth>> | null = null;
  let facilities: Awaited<ReturnType<typeof getFacilities>> = [];
  let census: Awaited<ReturnType<typeof getFacilityCensus>> = [];
  let errorMessage: string | null = null;

  try {
    [health, facilities] = await Promise.all([getHealth(), getFacilities()]);

    const primaryFacility = facilities[0];
    const hintId = getDemoFacilityIdHint();
    const facilityId = primaryFacility?.facility_id ?? hintId ?? null;

    if (facilityId) {
      try {
        census = await getFacilityCensus(facilityId);
      } catch {
        census = [];
      }
    }
  } catch (e) {
    errorMessage = e instanceof Error ? e.message : "Unable to reach the API.";
  }

  const firstFacilityName = facilities[0]?.facility_name ?? "Primary facility";
  const visitsDue = census.filter((r) => r.visit_due_flag).length;
  const missingCharges = census.filter((r) => r.missing_charge_flag).length;
  const unsignedNotes = census.filter((r) => r.unsigned_note_flag).length;

  return (
    <div className="mx-auto max-w-6xl space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">
          Dashboard
        </h1>
        <p className="mt-1 text-sm text-zinc-500">
          Operational snapshot sourced from live MedNexa APIs.
        </p>
      </div>

      {health ? (
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="success">API {health.status}</Badge>
          <span className="text-xs text-zinc-400">{health.service}</span>
        </div>
      ) : null}

      {errorMessage ? (
        <Card className="border-rose-200 bg-rose-50/50">
          <CardHeader>
            <CardTitle className="text-rose-900">Connection issue</CardTitle>
            <CardDescription className="text-rose-800/80">
              {errorMessage}
            </CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-rose-900/90">
            <p>
              Set{" "}
              <code className="rounded bg-white/80 px-1.5 py-0.5 text-xs">
                NEXT_PUBLIC_API_BASE_URL
              </code>{" "}
              in{" "}
              <code className="rounded bg-white/80 px-1.5 py-0.5 text-xs">
                .env.local
              </code>{" "}
              and ensure Azure CORS allows this origin.
            </p>
          </CardContent>
        </Card>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <StatCard
          label="Facilities"
          value={facilities.length}
          hint="Active directory"
        />
        <StatCard
          label="Active patients"
          value={census.length}
          hint={firstFacilityName}
        />
        <StatCard
          label="Visits due"
          value={visitsDue}
          hint="Census flags"
        />
        <StatCard
          label="Missing charges"
          value={missingCharges}
          hint="Revenue integrity"
        />
        <StatCard
          label="Unsigned notes"
          value={unsignedNotes}
          hint="Documentation"
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Next steps</CardTitle>
            <CardDescription>
              Jump into facilities, census, or billing workflows.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-3">
            <Link
              href="/facilities"
              className="rounded-lg bg-emerald-700 px-4 py-2.5 text-sm font-medium text-white shadow hover:bg-emerald-800"
            >
              View facilities
            </Link>
            {facilities[0] ? (
              <Link
                href={`/facilities/${facilities[0].facility_id}/census`}
                className="rounded-lg border border-zinc-200 bg-white px-4 py-2.5 text-sm font-medium text-zinc-800 shadow-sm hover:bg-zinc-50"
              >
                Open census
              </Link>
            ) : null}
            <Link
              href="/billing-queue"
              className="rounded-lg border border-zinc-200 bg-white px-4 py-2.5 text-sm font-medium text-zinc-800 shadow-sm hover:bg-zinc-50"
            >
              Billing queue
            </Link>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Data scope</CardTitle>
            <CardDescription>
              Summary metrics use the first active facility returned by{" "}
              <code className="rounded bg-zinc-100 px-1">GET /facilities</code>{" "}
              and its census. If none, counts may be zero until data exists.
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    </div>
  );
}
