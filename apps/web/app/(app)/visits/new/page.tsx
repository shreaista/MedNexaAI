import Link from "next/link";

import { VisitNoteForm } from "./visit-note-form";

export default function NewVisitPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">
            New visit
          </h1>
          <p className="mt-1 text-sm text-zinc-500">
            Capture a SOAP-style note for executive demos. Submission is local-only until the
            visit API is available.
          </p>
        </div>
        <Link
          href="/dashboard"
          className="text-sm font-medium text-emerald-800 hover:underline"
        >
          ← Dashboard
        </Link>
      </div>

      <VisitNoteForm />
    </div>
  );
}
