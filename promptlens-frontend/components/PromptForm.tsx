"use client";

import { FormEvent, useState } from "react";

type PromptFormProps = {
  onAnalyze: (promptText: string) => Promise<void>;
  loading: boolean;
};

export default function PromptForm({ onAnalyze, loading }: PromptFormProps) {
  const [promptText, setPromptText] = useState("");
  const templates = [
    "Summarize this support ticket thread and list the root causes.",
    "Rewrite this prompt to reduce hallucinations and improve specificity.",
    "Evaluate whether this prompt is measurable and easy to verify.",
  ];

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!promptText.trim()) {
      return;
    }

    await onAnalyze(promptText.trim());
  };

  return (
    <form onSubmit={handleSubmit} className="card-glow space-y-4 rounded-3xl p-5 sm:p-7">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <label htmlFor="prompt-input" className="block text-sm font-semibold uppercase tracking-[0.16em] text-emerald-200">
          Prompt Playground
        </label>
        <span className="rounded-full border border-slate-700/70 px-2.5 py-1 text-xs text-slate-400">
          {promptText.trim().length} characters
        </span>
      </div>

      <div className="flex flex-wrap gap-2">
        {templates.map((template) => (
          <button
            key={template}
            type="button"
            onClick={() => setPromptText(template)}
            className="rounded-full border border-emerald-300/20 bg-emerald-400/10 px-3 py-1.5 text-xs text-emerald-100 transition hover:border-emerald-300/35 hover:bg-emerald-400/15"
          >
            Use Example
          </button>
        ))}
      </div>

      <textarea
        id="prompt-input"
        className="min-h-44 w-full rounded-2xl border border-slate-700/85 bg-slate-950/85 p-4 text-sm leading-7 text-slate-100 outline-none transition focus:border-emerald-300 focus:ring-4 focus:ring-emerald-400/15"
        value={promptText}
        onChange={(event) => setPromptText(event.target.value)}
        placeholder="Example: Analyze customer feedback and produce top 3 trends with confidence levels."
      />

      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-xs text-slate-400">Tip: include context, constraints, and output format for better scores.</p>
        <button
          type="submit"
          disabled={loading || !promptText.trim()}
          className="inline-flex items-center gap-2 rounded-xl bg-linear-to-r from-emerald-300 to-cyan-300 px-5 py-2.5 font-semibold text-slate-900 transition hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading && (
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-900 border-t-transparent" />
          )}
          Analyze Prompt
        </button>
      </div>
    </form>
  );
}
