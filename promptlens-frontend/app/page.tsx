"use client";

import { useEffect, useMemo, useState } from "react";
import ChartCard from "@/components/ChartCard";
import TimelineChart from "@/components/TimelineChart";
import { 
  getModelPerformance, 
  getLanguagePerformance, 
  getPromptFeatures,
  getTopPrompts,
  getTimeline
} from "@/lib/api";

type BackendResponse<T> = {
  status: string;
  data: {
    data: T[];
    total_count?: number;
    insights?: Record<string, unknown>;
  };
};

type ModelItem = { model_name: string; attempts: number; avg_success: number; success_rate_pct: number; };
type LanguageItem = { programming_language: string; total_prompts: number; success_rate: number; };
type FeatureItem = { features: Record<string, boolean>; sample_count: number; avg_success: number; feature_combination_id: string; };
type TopPromptItem = { prompt_hash: string; prompt_preview: string; usage_count: number; success_rate_pct: number; rank: number; };

export default function DashboardPage() {
  const [modelData, setModelData] = useState<ModelItem[]>([]);
  const [languageData, setLanguageData] = useState<LanguageItem[]>([]);
  const [featureData, setFeatureData] = useState<FeatureItem[]>([]);
  const [topPrompts, setTopPrompts] = useState<TopPromptItem[]>([]);
  const [timelineData, setTimelineData] = useState<any[]>([]); // will parse
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      setLoading(true);
      setError(null);
      try {
        const [modelsRes, langsRes, featsRes, promptsRes, timelineRes] = await Promise.all([
          getModelPerformance<BackendResponse<ModelItem>>(),
          getLanguagePerformance<BackendResponse<LanguageItem>>(),
          getPromptFeatures<BackendResponse<FeatureItem>>(),
          getTopPrompts<BackendResponse<TopPromptItem>>(),
          getTimeline<any>()
        ]);

        setModelData(modelsRes?.data?.data || []);
        setLanguageData(langsRes?.data?.data || []);
        setFeatureData(featsRes?.data?.data || []);
        setTopPrompts(promptsRes?.data?.data || []);
        
        // Parse timeline dictionary to array for recharts
        if (timelineRes?.data?.data) {
           const seriesMap = timelineRes.data.data;
           const rawLineData = [];
           // we need to flatmap or construct days properly 
           // actually looking at the backend, it returns dict keys by model
           const allDays = new Set<string>();
           Object.keys(seriesMap).forEach(model => {
              seriesMap[model].forEach((pt: any) => allDays.add(pt.day));
           });
           
           const sortedDays = Array.from(allDays).sort();
           const chartReadyData = sortedDays.map(day => {
              const dayPoint: any = { day };
              Object.keys(seriesMap).forEach(model => {
                 const match = seriesMap[model].find((pt: any) => pt.day === day);
                 if (match) {
                    dayPoint[model] = match.avg_success * 100;
                 }
              });
              return dayPoint;
           });
           setTimelineData(chartReadyData);
        }

      } catch (err) {
        setError(err instanceof Error ? err.message : "Data warehouse sync failed.");
      } finally {
        setLoading(false);
      }
    };
    fetchDashboardData();
  }, []);

  const modelChartData = useMemo(() => modelData.map((item) => ({ name: item.model_name, value: item.success_rate_pct })), [modelData]);
  const languageChartData = useMemo(() => languageData.map((item) => ({ name: item.programming_language, value: parseFloat((item.success_rate * 100).toFixed(2)) })), [languageData]);
  const totalAttempts = useMemo(() => modelData.reduce((total, item) => total + item.attempts, 0), [modelData]);

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
    </div>
  );
}
