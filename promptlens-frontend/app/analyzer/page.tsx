"use client";

import { useState } from "react";
import PromptForm from "@/components/PromptForm";
import { analyzePrompt } from "@/lib/api";

type BackendAnalysisResponse = {
  baseline_score: number;
  cluster_group: string;
  extracted_features: Record<string, unknown>;
  recommendations: Array<{
    variant: string;
    predicted_score: number;
  }>;
};

export default function AnalyzerPage() {
  const [result, setResult] = useState<BackendAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async (promptText: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await analyzePrompt<BackendAnalysisResponse>(promptText);
      setResult(response);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to analyze prompt.";
      setError(message);
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="mx-auto w-full max-w-6xl space-y-6 px-4 py-8 xl:px-8">
      <header className="metric-card bg-slate-800/80 p-6 sm:p-8 rounded-lg">
        <span className="rounded border border-blue-500/30 bg-blue-500/10 px-2.5 py-1 text-xs font-bold uppercase tracking-wider text-blue-400">
          ML Inference Endpoint
        </span>
        <h1 className="mt-4 text-2xl font-bold tracking-tight text-slate-100">Predictive Quality Analysis</h1>
        <p className="mt-2 text-sm text-slate-400 max-w-3xl leading-relaxed">
          Evaluate a prompt's statistical likelihood of execution success. This tool runs feature extraction dynamically and evaluates structural complexity through our Random Forest and XGBoost classifiers against the datamart baseline.
        </p>
      </header>

      <PromptForm onAnalyze={handleAnalyze} loading={loading} />

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded text-sm font-mono mt-4">
          [INFERENCE EXPERIENCED EXCEPTION] {error}
        </div>
      )}

      {result && (
        <article className="metric-card p-6 sm:p-8 fade-in relative overflow-hidden">
          <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/5 rounded-full blur-3xl -mr-10 -mt-10" />
          
          <div className="flex justify-between items-end border-b border-slate-700 pb-4 mb-6 relative z-10">
            <h2 className="text-lg font-semibold text-slate-100 uppercase tracking-widest">Inference Results</h2>
            <div className="text-right">
               <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-1">K-Means Segment</p>
               <span className="bg-slate-900 border border-slate-700 px-3 py-1 rounded text-xs font-mono text-slate-300">
                 {result.cluster_group}
               </span>
            </div>
          </div>

          <div className="grid gap-6 sm:grid-cols-[1fr_2fr] relative z-10">
            <div className="rounded-lg border border-slate-700 bg-slate-900 p-6 flex flex-col justify-center items-center text-center shadow-inner">
              <p className="text-[11px] text-slate-400 uppercase tracking-widest font-semibold mb-3">Ensemble Predictor</p>
              <p className="text-5xl font-bold text-blue-400">
                {Math.round(result.baseline_score * 100)}%
              </p>
              <p className="text-xs text-slate-500 mt-3 font-medium uppercase tracking-wider">Success Probability</p>
            </div>

            <div className="rounded-lg border border-slate-700 bg-slate-900 p-6 shadow-inner">
              <p className="text-[11px] text-slate-400 uppercase tracking-widest font-semibold mb-4">Ablation Recommendations</p>
              {result.recommendations?.length > 0 ? (
                <ul className="space-y-3 text-sm text-slate-200">
                  {result.recommendations.map((rec, index) => {
                     const uplift = (rec.predicted_score - result.baseline_score) * 100;
                     return (
                        <li key={index} className="flex justify-between items-center bg-slate-800 p-3 rounded border border-slate-700 hover:border-blue-500/50 transition-colors">
                          <span className="font-medium text-slate-300 text-sm">{rec.variant}</span>
                          <div className="flex flex-col text-right">
                             <span className="text-blue-400 font-semibold text-sm">{Math.round(rec.predicted_score * 100)}% projected</span>
                             <span className="text-[11px] text-emerald-400 font-medium">+{uplift.toFixed(1)}% lift</span>
                          </div>
                        </li>
                     );
                  })}
                </ul>
              ) : (
                <div className="h-full flex items-center bg-slate-800/50 border border-slate-700 p-4 rounded text-center rounded-lg mt-2">
                  <p className="text-xs text-slate-400 w-full uppercase tracking-wider">Target prompt operates at Pareto optimal baseline.</p>
                </div>
              )}
            </div>
          </div>

          <details className="mt-6 rounded-lg border border-slate-700 bg-slate-900 p-4 relative z-10 group">
            <summary className="cursor-pointer text-xs font-semibold uppercase tracking-widest text-slate-400 hover:text-blue-300 transition-colors outline-none list-none flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path></svg>
              View Extracted Sub-Features
            </summary>
            <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-2 pt-4 border-t border-slate-800">
               {Object.entries(result.extracted_features).map(([key, value]) => {
                  return (
                    <div key={key} className="bg-slate-800 p-2.5 rounded border border-slate-700 hover:bg-slate-700 transition">
                       <p className="text-[10px] text-slate-500 uppercase tracking-wider truncate mb-1" title={key}>{key.replace(/_/g, ' ')}</p>
                       <p className="text-xs text-slate-200 font-mono">
                         {typeof value === 'number' && !Number.isInteger(value) ? value.toFixed(3) : String(value)}
                       </p>
                    </div>
                  );
               })}
            </div>
          </details>
        </article>
      )}
    </section>
  );
}
