"use client";

import { useState } from "react";
import PromptForm from "@/components/PromptForm";
import { analyzePrompt } from "@/lib/api";

type AnalyzerResult = {
  score?: number;
  suggestions?: string[] | string;
  [key: string]: unknown;
};

export default function AnalyzerPage() {
  const [result, setResult] = useState<AnalyzerResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async (promptText: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await analyzePrompt<AnalyzerResult>(promptText);
      setResult(response);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to analyze prompt.";
      setError(message);
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const suggestionList =
    typeof result?.suggestions === "string"
      ? [result.suggestions]
      : Array.isArray(result?.suggestions)
      ? result.suggestions
      : [];

  return (
    <section className="mx-auto w-full max-w-5xl space-y-6 px-4 py-8 sm:px-6">
      <header className="card-glow rounded-3xl p-6 sm:p-8">
        <span className="rounded-full border border-emerald-300/30 bg-emerald-400/10 px-3 py-1 text-xs uppercase tracking-[0.2em] text-emerald-100">
          Prompt Quality Lab
        </span>
        <h1 className="headline-gradient mt-4 text-3xl font-semibold tracking-tight sm:text-4xl">Prompt Analyzer</h1>
        <p className="mt-2 text-slate-300">Get a quality score and practical suggestions to improve your prompt.</p>
      </header>

      <PromptForm onAnalyze={handleAnalyze} loading={loading} />

      {error && <p className="rounded-xl border border-rose-400/20 bg-rose-400/10 p-3 text-rose-200">{error}</p>}

      {result && (
        <article className="card-glow rounded-3xl p-5 sm:p-6">
          <h2 className="text-xl font-medium text-cyan-100">Analysis Result</h2>

          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <div className="rounded-2xl border border-slate-700 bg-slate-950/70 p-4">
              <p className="text-sm text-slate-400">Score</p>
              <p className="mt-1 text-3xl font-semibold text-emerald-300">
                {typeof result.score === "number" ? result.score : "N/A"}
              </p>
              {typeof result.score === "number" && (
                <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-800">
                  <div
                    className="h-full rounded-full bg-linear-to-r from-emerald-300 to-cyan-300"
                    style={{ width: `${Math.min(Math.max(result.score, 0), 100)}%` }}
                  />
                </div>
              )}
            </div>

            <div className="rounded-2xl border border-slate-700 bg-slate-950/70 p-4">
              <p className="text-sm text-slate-400">Suggestions</p>
              {suggestionList.length > 0 ? (
                <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-200">
                  {suggestionList.map((item, index) => (
                    <li key={`${item}-${index}`}>{item}</li>
                  ))}
                </ul>
              ) : (
                <p className="mt-1 text-sm text-slate-300">No suggestions were returned.</p>
              )}
            </div>
          </div>

          <details className="mt-4 rounded-2xl border border-slate-700 bg-slate-950/70 p-4">
            <summary className="cursor-pointer text-sm text-slate-300">Raw response</summary>
            <pre className="mt-3 overflow-x-auto text-xs text-slate-200">
              {JSON.stringify(result, null, 2)}
            </pre>
          </details>
        </article>
      )}
    </section>
  );
}
