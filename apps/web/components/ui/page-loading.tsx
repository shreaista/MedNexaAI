import { Card, CardContent } from "@/components/ui/card";

/** Enterprise-style list/detail page skeleton */
export function PageLoading({ label }: { label?: string }) {
  return (
    <div className="mx-auto max-w-5xl space-y-6 animate-pulse">
      <div className="h-4 w-48 rounded bg-zinc-200" />
      <div className="h-8 w-64 rounded bg-zinc-200" />
      <Card>
        <CardContent className="space-y-4 py-8">
          {label ? (
            <p className="text-sm text-zinc-500">{label}</p>
          ) : null}
          <div className="h-24 rounded-lg bg-zinc-100" />
          <div className="h-32 rounded-lg bg-zinc-100" />
        </CardContent>
      </Card>
    </div>
  );
}
