"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function VisitNoteForm() {
  const [subjective, setSubjective] = useState("");
  const [objective, setObjective] = useState("");
  const [assessment, setAssessment] = useState("");
  const [plan, setPlan] = useState("");
  const [aiHint, setAiHint] = useState<string | null>(null);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Visit note (SOAP)</CardTitle>
          <CardDescription>
            Draft documentation locally · Submit endpoint not wired until API is available.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <label className="block space-y-2">
            <span className="text-xs font-medium uppercase text-zinc-500">Subjective</span>
            <textarea
              value={subjective}
              onChange={(e) => setSubjective(e.target.value)}
              rows={4}
              className="w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-900 shadow-sm focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
              placeholder="Chief complaint, history, patient narrative…"
            />
          </label>
          <label className="block space-y-2">
            <span className="text-xs font-medium uppercase text-zinc-500">Objective</span>
            <textarea
              value={objective}
              onChange={(e) => setObjective(e.target.value)}
              rows={4}
              className="w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-900 shadow-sm focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
              placeholder="Vitals, exam, labs, imaging…"
            />
          </label>
          <label className="block space-y-2">
            <span className="text-xs font-medium uppercase text-zinc-500">Assessment</span>
            <textarea
              value={assessment}
              onChange={(e) => setAssessment(e.target.value)}
              rows={3}
              className="w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-900 shadow-sm focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
              placeholder="Clinical impression, differential…"
            />
          </label>
          <label className="block space-y-2">
            <span className="text-xs font-medium uppercase text-zinc-500">Plan</span>
            <textarea
              value={plan}
              onChange={(e) => setPlan(e.target.value)}
              rows={3}
              className="w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-900 shadow-sm focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
              placeholder="Orders, medications, follow-up…"
            />
          </label>

          {aiHint ? (
            <p className="rounded-lg border border-emerald-100 bg-emerald-50/80 px-4 py-3 text-sm text-emerald-900">
              {aiHint}
            </p>
          ) : null}

          <div className="flex flex-wrap gap-3 pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={() =>
                setAiHint(
                  "AI draft (placeholder): Structured note generation will call MedNexa AI services when the visit API is live.",
                )
              }
            >
              Generate AI note placeholder
            </Button>
            <Button
              type="button"
              onClick={() =>
                setAiHint(
                  "Submit (placeholder): No POST endpoint is configured yet — your note stays in the browser until APIs ship.",
                )
              }
            >
              Submit visit placeholder
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
