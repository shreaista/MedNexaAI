import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <main className="mx-auto flex max-w-3xl flex-col gap-6 px-6 py-16">
      <p className="text-sm font-semibold uppercase tracking-[0.2em] text-emerald-700">
        mednexa-ai
      </p>
      <h1 className="text-balance text-4xl font-semibold leading-tight text-zinc-900">
        Evidence-forward clinical tooling, composed for regulated environments.
      </h1>
      <p className="text-lg text-zinc-600">
        Frontend bootstrap is wired with Tailwind CSS and composable primitives in
        shadcn style. Backend integration comes next alongside tenant-aware APIs.
      </p>
      <div className="flex flex-wrap gap-3">
        <Button>Primary action</Button>
        <Button variant="outline">Documentation</Button>
      </div>
    </main>
  );
}
