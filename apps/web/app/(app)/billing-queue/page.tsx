import Link from "next/link";

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

export default async function BillingQueuePage() {
  let items: Awaited<ReturnType<typeof getBillingQueue>> = [];
  let loadFailed = false;

  try {
    items = await getBillingQueue();
  } catch {
    loadFailed = true;
  }

  const showEmpty = loadFailed || items.length === 0;

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">
          Billing queue
        </h1>
        <p className="mt-1 text-sm text-zinc-500">
          Charge readiness and coder workflow ·{" "}
          <code className="text-xs">GET /billing-queue</code>
        </p>
      </div>

      {showEmpty ? (
        <Card className="border-zinc-200">
          <CardHeader>
            <CardTitle className="text-lg">Queue</CardTitle>
            <CardDescription>
              {loadFailed
                ? "We could not load billing items from the API. Verify connectivity and try again."
                : "No billing items yet. Submit a visit charge to populate the queue."}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link
              href="/visits/new"
              className="inline-flex rounded-lg bg-emerald-700 px-4 py-2.5 text-sm font-medium text-white shadow hover:bg-emerald-800"
            >
              New visit (placeholder)
            </Link>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Ready for billing</CardTitle>
            <CardDescription>{items.length} item(s)</CardDescription>
          </CardHeader>
          <CardContent className="overflow-x-auto p-0">
            <table className="w-full min-w-[800px] text-left text-sm">
              <thead>
                <tr className="border-b border-zinc-200 bg-zinc-50/80">
                  <th className="px-5 py-3 font-medium text-zinc-600">Patient</th>
                  <th className="px-5 py-3 font-medium text-zinc-600">MRN</th>
                  <th className="px-5 py-3 font-medium text-zinc-600">Provider</th>
                  <th className="px-5 py-3 font-medium text-zinc-600">ICD-10</th>
                  <th className="px-5 py-3 font-medium text-zinc-600">CPT</th>
                  <th className="px-5 py-3 font-medium text-zinc-600">Queue</th>
                  <th className="px-5 py-3 font-medium text-zinc-600">Readiness</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100">
                {items.map((row) => (
                  <tr key={row.queue_id} className="hover:bg-zinc-50/80">
                    <td className="px-5 py-4 font-medium text-zinc-900">
                      {row.patient_name}
                    </td>
                    <td className="px-5 py-4 font-mono text-xs text-zinc-600">
                      {row.mrn ?? "—"}
                    </td>
                    <td className="px-5 py-4 text-zinc-600">{row.provider_name}</td>
                    <td className="px-5 py-4 font-mono text-xs text-zinc-600">
                      {row.primary_icd10 ?? "—"}
                    </td>
                    <td className="px-5 py-4 font-mono text-xs text-zinc-600">
                      {row.primary_cpt ?? "—"}
                    </td>
                    <td className="px-5 py-4">
                      <Badge variant="neutral">{row.queue_status}</Badge>
                    </td>
                    <td className="px-5 py-4">
                      <span className="text-zinc-700">{String(row.readiness_score)}</span>
                      <span className="ml-2 text-xs text-zinc-400">
                        {row.readiness_status}
                      </span>
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
