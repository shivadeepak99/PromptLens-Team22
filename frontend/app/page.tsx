"use client";

import { useEffect, useMemo, useState } from "react";
import ChartCard from "@/components/ChartCard";
import TimelineChart from "@/components/TimelineChart";
import { 
  getModelPerformance, 
  getLanguagePerformance, 
  getPromptFeatures,
  getTopPrompts,
  getTimeline,
  getModelEfficiency
} from "@/lib/api";

type ApiEnvelope<T> = {
  timestamp?: string;
  status: string;
  data: T;
};

type ModelItem = {
  model_name: string;
  attempts: number;
  avg_success: number;
  success_rate_pct: number;
};

type LanguageItem = {
  programming_language: string;
  total_prompts: number;
  success_rate: number;
};

type FeatureItem = {
  features: { contains_examples: boolean; contains_code: boolean; contains_constraints: boolean };
  sample_count: number;
  avg_success: number;
  feature_combination_id: string;
};

type PromptFeatureInsights = {
  best_combination?: string | null;
  worst_combination?: string | null;
  confidence?: string | null;
};

type TopPromptItem = {
  prompt_hash: string;
  prompt_preview: string;
  usage_count: number;
  success_rate_pct: number;
  rank: number;
};

type TimelineSeriesPoint = {
  model_name: string;
  attempts: number;
  avg_success: number;
  median_success: number;
};

type TimelineDay = {
  date: string;
  series: TimelineSeriesPoint[];
};

type EfficiencyItem = {
  model_name: string;
  avg_latency: number | null;
  avg_tokens: number | null;
  avg_success_score: number | null;
  execution_count: number;
};

export default function DashboardPage() {
  const [modelData, setModelData] = useState<ModelItem[]>([]);
  const [languageData, setLanguageData] = useState<LanguageItem[]>([]);
  const [featureData, setFeatureData] = useState<FeatureItem[]>([]);
  const [featureInsights, setFeatureInsights] = useState<PromptFeatureInsights | null>(null);
  const [topPrompts, setTopPrompts] = useState<TopPromptItem[]>([]);
  const [efficiencyData, setEfficiencyData] = useState<EfficiencyItem[]>([]);
  const [timelineData, setTimelineData] = useState<any[]>([]);
  const [confusionMatrixText, setConfusionMatrixText] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      setLoading(true);
      setError(null);
      try {
        const [modelsRes, langsRes, featsRes, promptsRes, timelineRes, efficiencyRes] = await Promise.all([
          getModelPerformance<ApiEnvelope<{ total_count: number; data: ModelItem[] }>>(),
          getLanguagePerformance<ApiEnvelope<{ total_languages: number; data: LanguageItem[] }>>(),
          getPromptFeatures<ApiEnvelope<{ data: FeatureItem[]; insights: PromptFeatureInsights }>>(),
          getTopPrompts<ApiEnvelope<{ total_templates: number; top_templates: TopPromptItem[] }>>(),
          getTimeline<ApiEnvelope<{ models: string[]; date_range: { start: string | null; end: string | null }; data: TimelineDay[] }>>(),
          getModelEfficiency<any>()
        ]);

        setModelData(modelsRes?.data?.data ?? []);
        setLanguageData(langsRes?.data?.data ?? []);
        setFeatureData(featsRes?.data?.data ?? []);
        setFeatureInsights(featsRes?.data?.insights ?? null);
        setTopPrompts(promptsRes?.data?.top_templates ?? []);

        const timelineRows = timelineRes?.data?.data ?? [];
        if (Array.isArray(timelineRows) && timelineRows.length > 0) {
          const chartReadyData = timelineRows.map((row) => {
            const dayPoint: any = { day: row.date };
            (row.series ?? []).forEach((seriesPoint) => {
              dayPoint[seriesPoint.model_name] = (seriesPoint.avg_success ?? 0) * 100;
            });
            return dayPoint;
          });
          setTimelineData(chartReadyData);
        } else {
          setTimelineData([]);
        }

        // `/analytics/model-efficiency` is currently a lightweight endpoint (not the same envelope).
        // Support both shapes to keep the dashboard resilient.
        const efficiencyPayload = efficiencyRes as any;
        const efficiencyRows: EfficiencyItem[] = Array.isArray(efficiencyPayload?.data)
          ? efficiencyPayload.data
          : Array.isArray(efficiencyPayload?.data?.data)
            ? efficiencyPayload.data.data
            : [];
        setEfficiencyData(efficiencyRows);

      } catch (err) {
        setError(err instanceof Error ? err.message : "Data warehouse sync failed.");
      } finally {
        setLoading(false);
      }
    };
    fetchDashboardData();
  }, []);

  useEffect(() => {
    const fetchConfusionMatrix = async () => {
      try {
        const response = await fetch("/results/tables/eval_confusion_matrix.txt", { cache: "no-store" });
        if (!response.ok) return;
        const text = await response.text();
        setConfusionMatrixText(text);
      } catch {
        // optional artifact; ignore failures
      }
    };

    fetchConfusionMatrix();
  }, []);

  const modelChartData = useMemo(() => modelData.map((item) => ({ name: item.model_name, value: item.success_rate_pct })), [modelData]);
  const languageChartData = useMemo(() => languageData.map((item) => ({ name: item.programming_language, value: parseFloat((item.success_rate * 100).toFixed(2)) })), [languageData]);
  const totalAttempts = useMemo(() => modelData.reduce((total, item) => total + item.attempts, 0), [modelData]);
  const topModelInsight = useMemo(() => {
    if (!modelData.length) return null;
    return modelData.reduce((best, current) => (current.success_rate_pct > best.success_rate_pct ? current : best), modelData[0]);
  }, [modelData]);

  const hardestLanguageInsight = useMemo(() => {
    if (!languageData.length) return null;
    return languageData.reduce((worst, current) => (current.success_rate < worst.success_rate ? current : worst), languageData[0]);
  }, [languageData]);

  const sortedEfficiency = useMemo(() => {
    if (!efficiencyData.length) return [];
    return [...efficiencyData].sort((a, b) => {
      const aSuccess = a.avg_success_score ?? 0;
      const bSuccess = b.avg_success_score ?? 0;
      if (bSuccess !== aSuccess) return bSuccess - aSuccess;
      const aLatency = a.avg_latency ?? Number.POSITIVE_INFINITY;
      const bLatency = b.avg_latency ?? Number.POSITIVE_INFINITY;
      return aLatency - bLatency;
    });
  }, [efficiencyData]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-900">
        <div className="text-center text-slate-400">
          <div className="mb-4 h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent mx-auto"></div>
          <p className="text-sm font-medium tracking-wide uppercase">Connecting to PostgreSQL Warehouse...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 mx-auto max-w-[1400px]">
        <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded text-sm font-mono">
          [CRITICAL EXCEPTION] {error}
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-[1400px] p-4 xl:p-8 space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-2">
        <div>
           <h1 className="text-2xl font-bold text-slate-100 tracking-tight">ETL Executive Summary</h1>
           <p className="text-sm text-slate-400 mt-1">Materialized view metrics synchronized from production datamart.</p>
        </div>
        <div className="flex gap-2">
           <button onClick={() => window.location.reload()} className="bg-slate-800 hover:bg-slate-700 text-slate-300 px-4 py-2 text-xs uppercase tracking-wider font-semibold rounded border border-slate-700 transition">
             Refresh Views
           </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="metric-card">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-1">Global Query Volume</div>
          <div className="text-3xl font-bold text-slate-100">{totalAttempts.toLocaleString()}</div>
        </div>
        <div className="metric-card">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-1">Tracked Models</div>
          <div className="text-3xl font-bold text-blue-400">{modelData.length}</div>
        </div>
        <div className="metric-card">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-1">System Wide Success Rate</div>
          <div className="text-3xl font-bold text-emerald-400">
            {modelData.length ? (modelData.reduce((acc, m) => acc + m.success_rate_pct, 0) / modelData.length).toFixed(1) : 0}%
          </div>
        </div>
        <div className="metric-card">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-1">Feature Ablation Tests</div>
          <div className="text-3xl font-bold text-purple-400">{featureData.length} Combos</div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="metric-card">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-1">Top Model</div>
          <div className="text-lg font-semibold text-slate-100 truncate">
            {topModelInsight?.model_name ?? "—"}
          </div>
          <div className="text-sm text-blue-400 font-mono mt-1">
            {topModelInsight ? `${topModelInsight.success_rate_pct.toFixed(2)}%` : ""}
          </div>
        </div>
        <div className="metric-card">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-1">Hardest Language</div>
          <div className="text-lg font-semibold text-slate-100 truncate">
            {hardestLanguageInsight?.programming_language ?? "—"}
          </div>
          <div className="text-sm text-amber-400 font-mono mt-1">
            {hardestLanguageInsight ? `${(hardestLanguageInsight.success_rate * 100).toFixed(2)}%` : ""}
          </div>
        </div>
        <div className="metric-card">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-1">Best Prompt Structure</div>
          <div className="text-sm font-semibold text-emerald-400 mt-1">
            {featureInsights?.best_combination ?? "—"}
          </div>
          <div className="text-[11px] text-slate-500 uppercase tracking-wider mt-2">
            Confidence: {featureInsights?.confidence ?? "—"}
          </div>
        </div>
        <div className="metric-card">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-1">Worst Prompt Structure</div>
          <div className="text-sm font-semibold text-rose-400 mt-1">
            {featureInsights?.worst_combination ?? "—"}
          </div>
          <div className="text-[11px] text-slate-500 uppercase tracking-wider mt-2">
            Confidence: {featureInsights?.confidence ?? "—"}
          </div>
        </div>
      </div>

      {timelineData.length > 0 && (
         <div className="metric-card w-full h-[320px]">
            <h2 className="text-sm font-semibold text-slate-300 mb-4 uppercase tracking-widest">30-Day Sub-model Success Tolerance</h2>
            <TimelineChart data={timelineData} />
         </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard title="Inference Viability by Model" subtitle="Aggregated execution success mapped via datamart" data={modelChartData} colorClass="#3b82f6" />
        <ChartCard title="Language Compilation Success" subtitle="Syntactical success rate sorted alphabetically" data={languageChartData} colorClass="#10b981" />
      </div>

      <div className="data-table-container">
        <div className="bg-slate-800 px-4 py-3 border-b border-slate-700 flex justify-between items-center">
          <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-widest">Model Efficiency Tradeoff</h3>
          <span className="text-xs text-slate-400">Latency + Tokens vs Success</span>
        </div>
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Model</th>
                <th className="w-32 text-right">Avg Success</th>
                <th className="w-32 text-right">Avg Latency</th>
                <th className="w-32 text-right">Avg Tokens</th>
                <th className="w-28 text-right">Executions</th>
              </tr>
            </thead>
            <tbody>
              {sortedEfficiency.length > 0 ? (
                sortedEfficiency.slice(0, 12).map((row) => {
                  const successPct = ((row.avg_success_score ?? 0) * 100);
                  const latency = row.avg_latency;
                  const tokens = row.avg_tokens;
                  return (
                    <tr key={row.model_name}>
                      <td className="text-slate-200 font-medium">{row.model_name}</td>
                      <td className="text-right font-semibold text-emerald-400 font-mono text-xs">
                        {successPct.toFixed(2)}%
                      </td>
                      <td className="text-right text-slate-300 font-mono text-xs">
                        {latency == null ? "—" : latency.toFixed(2)}
                      </td>
                      <td className="text-right text-slate-300 font-mono text-xs">
                        {tokens == null ? "—" : Math.round(tokens).toLocaleString()}
                      </td>
                      <td className="text-right text-slate-400 font-mono text-xs">
                        {row.execution_count.toLocaleString()}
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={5} className="text-center text-slate-500 text-xs py-10">
                    Awaiting efficiency metrics...
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 data-table-container">
           <div className="bg-slate-800 px-4 py-3 border-b border-slate-700 flex justify-between items-center">
              <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-widest">Highest Yielding Templates</h3>
              <span className="text-xs text-slate-400">Top {topPrompts.length} ranked by output determinism</span>
           </div>
           <div className="overflow-x-auto">
             <table className="data-table">
               <thead>
                 <tr>
                   <th className="w-16">Rank</th>
                   <th>Template Snippet</th>
                   <th className="w-24 text-right">Uses</th>
                   <th className="w-24 text-right">Yield</th>
                 </tr>
               </thead>
               <tbody>
                 {topPrompts.map((p, i) => (
                   <tr key={p.prompt_hash}>
                     <td className="text-slate-500 font-mono text-xs">#{i + 1}</td>
                     <td className="max-w-[300px] truncate text-slate-300 text-xs italic">
                       "{p.prompt_preview}"
                     </td>
                     <td className="text-right text-slate-400 font-mono text-xs">{p.usage_count.toLocaleString()}</td>
                     <td className="text-right font-semibold text-emerald-400 text-xs">{Math.round(p.success_rate_pct)}%</td>
                   </tr>
                 ))}
               </tbody>
             </table>
           </div>
        </div>

        <div className="data-table-container">
           <div className="bg-slate-800 px-4 py-3 border-b border-slate-700">
              <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-widest">Ablation Heat Matrix</h3>
           </div>
           <div className="p-4 space-y-3">
             {featureData.slice(0, 6).map((f) => {
                const active = Object.values(f.features).filter(Boolean).length;
                return (
                  <div key={f.feature_combination_id} className="flex justify-between items-center pb-3 border-b border-slate-800 last:border-0 last:pb-0">
                     <div className="flex gap-1">
                        <span className={`w-3 h-3 rounded-sm ${f.features.contains_examples ? 'bg-emerald-500' : 'bg-slate-700'}`} title="Examples" />
                        <span className={`w-3 h-3 rounded-sm ${f.features.contains_code ? 'bg-blue-500' : 'bg-slate-700'}`} title="Code Blocks" />
                        <span className={`w-3 h-3 rounded-sm ${f.features.contains_constraints ? 'bg-purple-500' : 'bg-slate-700'}`} title="Constraints" />
                        <span className="text-[10px] text-slate-500 ml-2 font-mono uppercase">
                          {active === 0 ? "BASELINE" : `${active} FEAT`}
                        </span>
                     </div>
                     <span className="text-xs font-semibold text-slate-300">
                        {Math.round(f.avg_success * 100)}%
                     </span>
                  </div>
                );
             })}
             <div className="mt-4 pt-1 flex gap-4 justify-center">
               <div className="flex items-center gap-1.5"><span className="w-2 h-2 bg-emerald-500 rounded-sm"></span><span className="text-[10px] text-slate-500 uppercase">Ex</span></div>
               <div className="flex items-center gap-1.5"><span className="w-2 h-2 bg-blue-500 rounded-sm"></span><span className="text-[10px] text-slate-500 uppercase">Code</span></div>
               <div className="flex items-center gap-1.5"><span className="w-2 h-2 bg-purple-500 rounded-sm"></span><span className="text-[10px] text-slate-500 uppercase">Constraint</span></div>
             </div>
           </div>
        </div>
      </div>

      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-widest">R Analytics Outputs</h2>
            <p className="text-xs text-slate-500 mt-1">Figures and evaluation artifacts generated by the R pipeline.</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="metric-card p-4">
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-3">Feature Correlation Matrix</div>
            <img
              src="/results/figures/correlation_matrix.png"
              alt="Feature Correlation Matrix"
              className="w-full rounded border border-slate-700 bg-slate-900"
            />
            <p className="text-xs text-slate-500 mt-3 leading-relaxed">
              Interprets linear relationships between engineered prompt features, tokens, and success score.
            </p>
          </div>

          <div className="metric-card p-4">
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-3">Success Density (Code Inclusion)</div>
            <img
              src="/results/figures/success_density.png"
              alt="Success Density"
              className="w-full rounded border border-slate-700 bg-slate-900"
            />
            <p className="text-xs text-slate-500 mt-3 leading-relaxed">
              Compares success-score distributions for prompts that include code vs those that do not.
            </p>
          </div>

          <div className="metric-card p-4">
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-3">K-Means Cluster Space</div>
            <img
              src="/results/figures/cluster_plot.png"
              alt="K-Means Cluster Plot"
              className="w-full rounded border border-slate-700 bg-slate-900"
            />
            <p className="text-xs text-slate-500 mt-3 leading-relaxed">
              Segments prompts into behavioral clusters using numeric features (complexity, length, tokens).
            </p>
          </div>

          <div className="metric-card p-4">
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-3">Classification ROC Curve</div>
            <img
              src="/results/figures/roc_curve.png"
              alt="ROC Curve"
              className="w-full rounded border border-slate-700 bg-slate-900"
            />
            <p className="text-xs text-slate-500 mt-3 leading-relaxed">
              Evaluates the binary classifier used for success prediction (AUC summary).
            </p>
          </div>

          <div className="metric-card p-4">
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-3">Association Rules Network</div>
            <img
              src="/results/figures/association_rules.png"
              alt="Association Rules"
              className="w-full rounded border border-slate-700 bg-slate-900"
            />
            <p className="text-xs text-slate-500 mt-3 leading-relaxed">
              Visualizes discovered rule patterns linking prompt structure flags to success/failure outcomes.
            </p>
          </div>

          <div className="metric-card p-4">
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-3">Success by Programming Language</div>
            <img
              src="/results/figures/language_difficulty.png"
              alt="Language Difficulty"
              className="w-full rounded border border-slate-700 bg-slate-900"
            />
            <p className="text-xs text-slate-500 mt-3 leading-relaxed">
              Shows which target programming languages have higher/lower success scores (domain difficulty).
            </p>
          </div>
        </div>

        <div className="metric-card p-4">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-3">Evaluation Table: Confusion Matrix</div>
          {confusionMatrixText ? (
            <pre className="whitespace-pre-wrap break-words text-[12px] bg-slate-950 border border-slate-700 rounded p-4 text-slate-200 overflow-x-auto">
              {confusionMatrixText}
            </pre>
          ) : (
            <div className="text-xs text-slate-500">Confusion matrix artifact not available.</div>
          )}
          <p className="text-xs text-slate-500 mt-3 leading-relaxed">
            model performance metrics (accuracy, sensitivity, specificity) from the R evaluation pipeline.
          </p>
        </div>
      </section>
    </div>
  );
}
