import Link from "next/link";
import { notFound } from "next/navigation";

import { getFacilityCensus } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export const dynamic = "force-dynamic";

function FlagCell({ value }: { value: boolean }) {
  return (
    <Badge variant={value ? "warning" : "success"}>
      {value ? "Yes" : "No"}
    </Badge>
  );
}

export default async function CensusPage({
  params,
}: {
  params: Promise<{ facilityId: string }>;
}) {
  const { facilityId } = await params;

  let rows: Awaited<ReturnType<typeof getFacilityCensus>> = [];
  let errorMessage: string | null = null;

  try {
    rows = await getFacilityCensus(facilityId);
  } catch (e) {
    const msg = e instanceof Error ? e.message : "";
    if (msg.includes("404") || msg.toLowerCase().includes("not found")) {
      notFound();
    }
    errorMessage = msg || "Failed to load census.";
  }

  return (
    <div className="mx-auto max-w-[1100px] space-y-6">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">
            Facility census
          </h1>
          <p className="mt-1 font-mono text-xs text-zinc-400">{facilityId}</p>
        </div>
        <Link
          href="/facilities"
          className={cn(
            buttonVariants({ variant: "outline", size: "sm" }),
            "w-fit text-xs",
          )}
        >
          ← All facilities
        </Link>
      </div>

      {errorMessage ? (
        <Card className="border-amber-200 bg-amber-50/40">
          <CardHeader>
            <CardTitle className="text-amber-900">Census unavailable</CardTitle>
            <CardDescription className="text-amber-900/80">
              {errorMessage}
            </CardDescription>
          </CardHeader>
        </Card>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>Inpatient census</CardTitle>
          <CardDescription>
            {rows.length} patient{rows.length === 1 ? "" : "s"} ·{" "}
            <code className="text-xs">GET /facilities/n…/census</code>
          </CardDescription>
        </CardHeader>
        <CardContent className="overflow-x-auto p-0">
          <table className="w-full min-w-[960px] text-left text-sm">
            <thead>
              <tr className="border-b border-zinc-200 bg-zinc-50/80">
                <th className="px-4 py-3 font-medium text-zinc-600">MRN</th>
                <th className="px-4 py-3 font-medium text-zinc-600">Patient</th>
                <th className="px-4 py-3 font-medium text-zinc-600">DOB</th>
                <th className="px-4 py-3 font-medium text-zinc-600">Gender</th>
                <th className="px-4 py-3 font-medium text-zinc-600">Payer</th>
                <th className="px-4 py-3 font-medium text-zinc-600">Room</th>
                <th className="px-4 py-3 font-medium text-zinc-600">Care</th>
                <th className="px-4 py-3 font-medium text-zinc-600">Due</th>
                <th className="px-4 py-3 font-medium text-zinc-600">Unsigned</th>
                <th className="px-4 py-3 font-medium text-zinc-600">Charges</th>
                <th className="px-4 py-3 font-medium text-zinc-600" />
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100">
              {rows.length === 0 && !errorMessage ? (
                <tr>
                  <td
                    colSpan={11}
                    className="px-4 py-12 text-center text-sm text-zinc-500"
                  >
                    No census rows for this facility.
                  </td>
                </tr>
              ) : null}
              {rows.map((r) => (
                <tr key={r.census_id} className="hover:bg-zinc-50/80">
                  <td className="px-4 py-3 font-mono text-xs text-zinc-700">
                    {r.mrn ?? "—"}
                  </td>
                  <td className="px-4 py-3 font-medium text-zinc-900">
                    {r.patient_name ?? "—"}
                  </td>
                  <td className="px-4 py-3 text-zinc-600">{r.date_of_birth ?? "—"}</td>
                  <td className="px-4 py-3 text-zinc-600">{r.gender ?? "—"}</td>
                  <td className="max-w-[140px] truncate px-4 py-3 text-zinc-600">
                    {r.payer_name ?? "—"}
                  </td>
                  <td className="px-4 py-3 text-zinc-600">
                    {[r.room_number, r.bed_number].filter(Boolean).join(" / ") || "—"}
                  </td>
                  <td className="px-4 py-3 text-zinc-600">
                    {r.care_level ?? "—"}
                  </td>
                  <td className="px-4 py-3">
                    <FlagCell value={r.visit_due_flag} />
                  </td>
                  <td className="px-4 py-3">
                    <FlagCell value={r.unsigned_note_flag} />
                  </td>
                  <td className="px-4 py-3">
                    <FlagCell value={r.missing_charge_flag} />
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Link
                      href={`/patients/${r.patient_id}`}
                      className={cn(
                        buttonVariants({ variant: "outline", size: "sm" }),
                        "text-xs",
                      )}
                    >
                      Open chart
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
