import Link from "next/link";

import { AppBreadcrumbs } from "@/components/layout/breadcrumbs";
import { getFacilities } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export const dynamic = "force-dynamic";

export default async function FacilitiesPage() {
  let facilities: Awaited<ReturnType<typeof getFacilities>> = [];
  let errorMessage: string | null = null;

  try {
    facilities = await getFacilities();
  } catch (e) {
    errorMessage = e instanceof Error ? e.message : "Failed to load facilities.";
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <AppBreadcrumbs
        items={[
          { label: "Dashboard", href: "/dashboard" },
          { label: "Facilities" },
        ]}
      />
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">
          Facilities
        </h1>
        <p className="mt-1 text-sm text-zinc-500">
          Licensed sites and service lines connected to your tenant.
        </p>
      </div>

      {errorMessage ? (
        <Card className="border-amber-200 bg-amber-50/40">
          <CardHeader>
            <CardTitle className="text-amber-900">Could not load facilities</CardTitle>
            <CardDescription className="text-amber-900/80">
              {errorMessage}
            </CardDescription>
          </CardHeader>
        </Card>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>Directory</CardTitle>
          <CardDescription>
            {facilities.length} record{facilities.length === 1 ? "" : "s"} from{" "}
            <code className="text-xs">GET /facilities</code>
          </CardDescription>
        </CardHeader>
        <CardContent className="overflow-x-auto p-0">
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead>
              <tr className="border-b border-zinc-200 bg-zinc-50/80">
                <th className="px-5 py-3 font-medium text-zinc-600">Facility</th>
                <th className="px-5 py-3 font-medium text-zinc-600">Type</th>
                <th className="px-5 py-3 font-medium text-zinc-600">Location</th>
                <th className="px-5 py-3 font-medium text-zinc-600">Status</th>
                <th className="px-5 py-3 font-medium text-zinc-600" />
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100">
              {facilities.length === 0 && !errorMessage ? (
                <tr>
                  <td
                    colSpan={5}
                    className="px-5 py-10 text-center text-sm text-zinc-500"
                  >
                    No facilities returned from the API.
                  </td>
                </tr>
              ) : null}
              {facilities.map((f) => (
                <tr key={f.facility_id} className="hover:bg-zinc-50/80">
                  <td className="px-5 py-4">
                    <p className="font-medium text-zinc-900">{f.facility_name}</p>
                    <p className="text-xs text-zinc-400">{f.tenant_name}</p>
                  </td>
                  <td className="px-5 py-4 text-zinc-600">
                    {f.facility_type ?? "—"}
                  </td>
                  <td className="px-5 py-4 text-zinc-600">
                    {[f.city, f.state].filter(Boolean).join(", ") || "—"}
                  </td>
                  <td className="px-5 py-4">
                    <Badge
                      variant={
                        String(f.status).toUpperCase() === "ACTIVE"
                          ? "success"
                          : "neutral"
                      }
                    >
                      {f.status}
                    </Badge>
                  </td>
                  <td className="px-5 py-4 text-right">
                    <Link
                      href={`/facilities/${f.facility_id}/census`}
                      className={cn(buttonVariants({ variant: "default", size: "sm" }), "bg-emerald-700 text-xs hover:bg-emerald-800")}
                    >
                      View Census
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
