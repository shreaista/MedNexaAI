import { Suspense } from "react";
import Link from "next/link";

import { AppBreadcrumbs } from "@/components/layout/breadcrumbs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { NewVisitWorkflow } from "./new-visit-workflow";

function VisitSkeleton() {
  return (
    <div className="animate-pulse space-y-6">
      <Card>
        <CardContent className="h-32 py-8">
          <div className="h-4 w-40 rounded bg-zinc-100" />
        </CardContent>
      </Card>
      <Card>
        <CardContent className="h-64 py-8">
          <div className="h-4 w-56 rounded bg-zinc-100" />
        </CardContent>
      </Card>
    </div>
  );
}

export default async function NewVisitPage({
  searchParams,
}: {
  searchParams?: Promise<{ patientId?: string; facilityId?: string }>;
}) {
  const q = await (searchParams ??
    Promise.resolve({} as { patientId?: string; facilityId?: string }));

  const patientId = q.patientId?.trim();
  const facilityId = q.facilityId?.trim();
  const hasEncounterContext = !!(patientId && facilityId);

  const breadcrumbItems = [
    { label: "Dashboard", href: "/dashboard" },
    { label: "Facilities", href: "/facilities" },
    ...(facilityId
      ? [{ label: "Census", href: `/facilities/${encodeURIComponent(facilityId)}/census` }]
      : []),
    ...(patientId && facilityId
      ? [
          {
            label: "Patient chart",
            href: `/patients/${encodeURIComponent(patientId)}?facilityId=${encodeURIComponent(facilityId)}`,
          },
        ]
      : []),
    { label: "New visit" },
  ];

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <AppBreadcrumbs items={breadcrumbItems} />
      <div className="flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">
            New Visit
          </h1>
          <p className="mt-1 max-w-xl text-sm text-zinc-500">
            Document the encounter and route the charge to the billing queue via the live MedNexa API.
          </p>
        </div>
        <Link
          href="/dashboard"
          className="text-sm font-medium text-emerald-800 hover:underline"
        >
          ← Dashboard
        </Link>
      </div>

      {!hasEncounterContext ? (
        <Card className="border border-sky-200 bg-sky-50/60">
          <CardHeader className="pb-2">
            <CardTitle className="text-base text-sky-950">Start from census</CardTitle>
            <CardDescription className="text-sky-900/90">
              Please select a patient from Census first.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-3">
            <Link
              href="/facilities"
              className={cn(buttonVariants({ variant: "default" }), "bg-emerald-700 hover:bg-emerald-800")}
            >
              Go to Facilities
            </Link>
          </CardContent>
        </Card>
      ) : null}

      <Suspense fallback={<VisitSkeleton />}>
        <NewVisitWorkflow />
      </Suspense>
    </div>
  );
}
