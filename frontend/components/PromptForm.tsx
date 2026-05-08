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
    if (!promptText.trim()) return;
    await onAnalyze(promptText.trim());
  };

  return (
    <form onSubmit={handleSubmit} className="metric-card space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-700 pb-3">
        <label htmlFor="prompt-input" className="block text-xs font-bold uppercase tracking-widest text-slate-300">
          Inference Input Console
        </label>
        <span className="rounded bg-slate-900 border border-slate-700 px-2 py-0.5 text-[10px] font-mono text-slate-400">
          BYTES: {promptText.trim().length}
        </span>
      </div>

      <div className="flex flex-wrap gap-2">
        {templates.map((template, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => setPromptText(template)}
            className="rounded bg-slate-800 border border-slate-700 px-3 py-1.5 text-[11px] font-medium uppercase tracking-wider text-slate-400 transition hover:text-blue-400 hover:border-blue-500/50"
          >
            Load Case {idx + 1}
          </button>
        ))}
      </div>

      <textarea
        id="prompt-input"
        className="min-h-32 w-full rounded border border-slate-700 bg-slate-900 p-4 text-sm font-mono leading-relaxed text-slate-200 outline-none transition focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
        value={promptText}
        onChange={(event) => setPromptText(event.target.value)}
        placeholder="> Enter raw prompt string for model execution..."
      />

      <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
        <p className="text-[11px] uppercase tracking-widest text-slate-500">
          System expects UTF-8 string encoding.
        </p>
        <button
          type="submit"
          disabled={loading || !promptText.trim()}
          className="inline-flex items-center gap-2 rounded bg-blue-600 px-6 py-2 text-xs font-bold uppercase tracking-wider text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading && (
            <span className="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent" />
          )}
          {loading ? "Executing..." : "Run Extraction"}
        </button>
      </div>
    </form>
  );
}
