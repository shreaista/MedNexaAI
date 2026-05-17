import Link from "next/link";

import { AppBreadcrumbs } from "@/components/layout/breadcrumbs";
import { getBillingQueue } from "@/lib/api";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export const dynamic = "force-dynamic";

type Search = { charged?: string; charge_id?: string };

function workflowStatusVariant(raw: string): "success" | "warning" | "info" | "muted" | "neutral" {
  const u = raw.toUpperCase();
  if (u === "READY") return "success";
  if (u === "NEEDS_REVIEW") return "warning";
  if (u === "SUBMITTED") return "info";
  if (u === "NEW") return "muted";
  return "neutral";
}

export default async function BillingQueuePage({
  searchParams,
}: {
  searchParams?: Promise<Search>;
}) {
  const q = await (searchParams ?? Promise.resolve({} as Search));
  const chargedOk = q.charged === "1";

  let items: Awaited<ReturnType<typeof getBillingQueue>> = [];
  let loadFailed = false;

  try {
    items = await getBillingQueue();
  } catch {
    loadFailed = true;
  }

  const showEmpty = loadFailed || items.length === 0;
  const emptyCopy = loadFailed
    ? "We could not load billing items from the API. Verify connectivity and try again."
    : "No billing items yet. Submit a visit charge to populate this queue.";

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <AppBreadcrumbs
        items={[
          { label: "Dashboard", href: "/dashboard" },
          { label: "Billing queue" },
        ]}
      />
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">
          Billing queue
        </h1>
        <p className="mt-1 text-sm text-zinc-500">
          Charge readiness and coder workflow ·{" "}
          <code className="text-xs">GET /billing-queue</code>
        </p>
      </div>

      {chargedOk && !loadFailed ? (
        <Card className="border-emerald-200 bg-emerald-50/50">
          <CardHeader className="py-4">
            <CardTitle className="text-base text-emerald-950">Charge captured</CardTitle>
            <CardDescription className="text-emerald-900/85">
              The visit workflow completed and a billing queue row was created.
              {q.charge_id ? (
                <>
                  {" "}
                  Charge id ·{" "}
                  <span className="font-mono text-xs text-emerald-900">{q.charge_id}</span>
                </>
              ) : null}
            </CardDescription>
          </CardHeader>
        </Card>
      ) : null}

      {showEmpty ? (
        <Card className="border-zinc-200">
          <CardHeader>
            <CardTitle className="text-lg">Queue</CardTitle>
            <CardDescription>{emptyCopy}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-3">
              <Link
                href="/facilities"
                className="inline-flex rounded-lg bg-emerald-700 px-4 py-2.5 text-sm font-medium text-white shadow hover:bg-emerald-800"
              >
                Facilities
              </Link>
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Ready for billing</CardTitle>
            <CardDescription>{items.length} item(s)</CardDescription>
          </CardHeader>
          <CardContent className="overflow-x-auto p-0">
            <table className="w-full min-w-[1080px] text-left text-sm">
              <thead>
                <tr className="border-b border-zinc-200 bg-zinc-50/80">
                  <th className="px-4 py-3 font-medium text-zinc-600">Patient name</th>
                  <th className="px-4 py-3 font-medium text-zinc-600">MRN</th>
                  <th className="px-4 py-3 font-medium text-zinc-600">Provider name</th>
                  <th className="px-4 py-3 font-medium text-zinc-600">Primary ICD‑10</th>
                  <th className="px-4 py-3 font-medium text-zinc-600">Primary CPT</th>
                  <th className="px-4 py-3 font-medium text-zinc-600">Charge status</th>
                  <th className="px-4 py-3 font-medium text-zinc-600">Queue status</th>
                  <th className="px-4 py-3 font-medium text-zinc-600">Readiness score</th>
                  <th className="px-4 py-3 font-medium text-zinc-600">Readiness status</th>
                  <th className="px-4 py-3 font-medium text-zinc-600">Priority</th>
                  <th className="px-4 py-3 font-medium text-zinc-600">Created at</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100">
                {items.map((row) => (
                  <tr key={row.queue_id} className="hover:bg-zinc-50/80">
                    <td className="px-4 py-4 font-medium text-zinc-900">
                      {row.patient_name}
                    </td>
                    <td className="px-4 py-4 font-mono text-xs text-zinc-600">
                      {row.mrn ?? "—"}
                    </td>
                    <td className="px-4 py-4 text-zinc-600">{row.provider_name}</td>
                    <td className="px-4 py-4 font-mono text-xs text-zinc-600">
                      {row.primary_icd10 ?? "—"}
                    </td>
                    <td className="px-4 py-4 font-mono text-xs text-zinc-600">
                      {row.primary_cpt ?? "—"}
                    </td>
                    <td className="px-4 py-4">
                      <Badge variant={workflowStatusVariant(String(row.charge_status))}>
                        {row.charge_status}
                      </Badge>
                    </td>
                    <td className="px-4 py-4">
                      <Badge variant={workflowStatusVariant(String(row.queue_status))}>
                        {row.queue_status}
                      </Badge>
                    </td>
                    <td className="px-4 py-4 font-medium text-zinc-800">
                      {String(row.readiness_score)}
                    </td>
                    <td className="px-4 py-4">
                      <Badge variant={workflowStatusVariant(String(row.readiness_status))}>
                        {row.readiness_status}
                      </Badge>
                    </td>
                    <td className="px-4 py-4 font-medium uppercase text-xs text-zinc-600">
                      {row.priority}
                    </td>
                    <td className="whitespace-nowrap px-4 py-4 text-xs text-zinc-500">
                      {new Date(row.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
