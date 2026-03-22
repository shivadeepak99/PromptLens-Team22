"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import ChartCard from "@/components/ChartCard";
import { getLanguagePerformance, getModelPerformance } from "@/lib/api";

type RawItem = Record<string, unknown>;

type ChartPoint = {
  name: string;
  value: number;
};

function toNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;

  if (typeof value === "string") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }

  return null;
}

function itemLabel(item: RawItem, index: number): string {
  const candidate = item.model ?? item.language ?? item.name ?? item.label;
  return typeof candidate === "string" ? candidate : `Item ${index + 1}`;
}

function itemSuccessRate(item: RawItem): number {
  const value =
    toNumber(item.success_rate) ??
    toNumber(item.successRate) ??
    toNumber(item.score) ??
    toNumber(item.accuracy);
  return value ?? 0;
}

function itemAttempts(item: RawItem): number {
  const value =
    toNumber(item.attempts) ??
    toNumber(item.total_attempts) ??
    toNumber(item.total) ??
    toNumber(item.count);
  return value ?? 0;
}

function topPerformer(items: RawItem[]): { label: string; score: number } | null {
  if (items.length === 0) return null;

  const selected = items.reduce((best, current, index) => {
    const currentScore = itemSuccessRate(current);
    if (!best || currentScore > best.score) {
      return { label: itemLabel(current, index), score: currentScore };
    }
    return best;
  }, null as { label: string; score: number } | null);

  return selected;
}

export default function DashboardPage() {
  const [modelData, setModelData] = useState<RawItem[]>([]);
  const [languageData, setLanguageData] = useState<RawItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      setLoading(true);
      setError(null);

      try {
        const [models, languages] = await Promise.all([
          getModelPerformance<RawItem[] | { items?: RawItem[] }>(),
          getLanguagePerformance<RawItem[] | { items?: RawItem[] }>(),
        ]);

        const modelItems = Array.isArray(models) ? models : (models.items ?? []);
        const languageItems = Array.isArray(languages) ? languages : (languages.items ?? []);

        setModelData(modelItems);
        setLanguageData(languageItems);
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to load analytics.";
        setError(message);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  const modelChartData = useMemo<ChartPoint[]>(
    () => modelData.map((item, index) => ({ name: itemLabel(item, index), value: itemSuccessRate(item) })),
    [modelData],
  );

  const languageChartData = useMemo<ChartPoint[]>(
    () => languageData.map((item, index) => ({ name: itemLabel(item, index), value: itemSuccessRate(item) })),
    [languageData],
  );

  const totalAttempts = useMemo(
    () => [...modelData, ...languageData].reduce((total, item) => total + itemAttempts(item), 0),
    [languageData, modelData],
  );

  const averageSuccessRate = useMemo(() => {
    const all = [...modelData, ...languageData];
    if (all.length === 0) return 0;

    const sum = all.reduce((total, item) => total + itemSuccessRate(item), 0);
    return sum / all.length;
  }, [languageData, modelData]);

  const topModel = useMemo(() => topPerformer(modelData), [modelData]);
  const topLanguage = useMemo(() => topPerformer(languageData), [languageData]);

  return (
    <section className="mx-auto grid-aurora w-full max-w-6xl space-y-6 px-4 py-8 sm:px-6">
      <header className="card-glow relative rounded-3xl p-6 sm:p-8">
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-full border border-cyan-300/35 bg-cyan-400/10 px-3 py-1 text-xs uppercase tracking-[0.18em] text-cyan-100">
            Analytics Center
          </span>
          <span className="rounded-full border border-emerald-300/35 bg-emerald-400/10 px-3 py-1 text-xs uppercase tracking-[0.18em] text-emerald-100">
            Real-time Insights
          </span>
        </div>

        <h1 className="headline-gradient mt-4 text-3xl font-semibold tracking-tight sm:text-4xl">
          Build better prompts with clear, visual feedback
        </h1>
        <p className="mt-3 max-w-2xl text-slate-300">
          Monitor quality trends, compare performance, and jump directly into analysis or guided chat.
        </p>

        <div className="mt-6 flex flex-wrap gap-3">
          <Link
            href="/analyzer"
            className="rounded-xl bg-linear-to-r from-emerald-300 to-cyan-300 px-4 py-2.5 text-sm font-semibold text-slate-900 transition hover:brightness-105"
          >
            Analyze Prompt
          </Link>
          <Link
            href="/chat"
            className="rounded-xl border border-cyan-300/30 bg-cyan-400/10 px-4 py-2.5 text-sm font-semibold text-cyan-100 transition hover:bg-cyan-400/15"
          >
            Open AI Chat
          </Link>
        </div>
      </header>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <article className="card-glow rounded-3xl p-4">
          <p className="text-sm text-slate-400">Average Success</p>
          <p className="mt-2 text-3xl font-semibold text-emerald-300">{averageSuccessRate.toFixed(2)}%</p>
          <p className="mt-2 text-xs text-slate-500">All model + language datapoints combined</p>
        </article>
        <article className="card-glow rounded-3xl p-4">
          <p className="text-sm text-slate-400">Total Attempts</p>
          <p className="mt-2 text-3xl font-semibold text-cyan-300">{totalAttempts}</p>
          <p className="mt-2 text-xs text-slate-500">Backend-reported execution attempts</p>
        </article>
        <article className="card-glow rounded-3xl p-4">
          <p className="text-sm text-slate-400">Data Points</p>
          <p className="mt-2 text-3xl font-semibold text-emerald-300">{modelData.length + languageData.length}</p>
          <p className="mt-2 text-xs text-slate-500">Rows consumed from analytics endpoints</p>
        </article>
        <article className="card-glow rounded-3xl p-4">
          <p className="text-sm text-slate-400">Top Performer</p>
          <p className="mt-2 line-clamp-1 text-lg font-semibold text-cyan-100">
            {topModel?.label ?? topLanguage?.label ?? "Not available"}
          </p>
          <p className="mt-2 text-xs text-slate-500">
            Score {(topModel?.score ?? topLanguage?.score ?? 0).toFixed(2)}%
          </p>
        </article>
      </div>

      {loading && (
        <div className="inline-flex items-center gap-2 rounded-lg border border-cyan-300/20 bg-slate-900/70 px-4 py-2 text-slate-200">
          <span className="h-4 w-4 animate-spin rounded-full border-2 border-cyan-300 border-t-transparent" />
          Loading dashboard data...
        </div>
      )}

      {error && <p className="rounded-xl border border-rose-400/20 bg-rose-400/10 p-3 text-rose-200">{error}</p>}

      {!loading && !error && (
        <div className="grid gap-4 lg:grid-cols-2">
          <ChartCard
            title="Model Performance"
            subtitle="Success rate by model"
            data={modelChartData}
            colorClass="#22d3ee"
            accent="cyan"
          />
          <ChartCard
            title="Language Performance"
            subtitle="Success rate by language"
            data={languageChartData}
            colorClass="#34d399"
            accent="emerald"
          />
        </div>
      )}

      {!loading && !error && (
        <section className="grid gap-4 lg:grid-cols-2">
          <article className="card-glow rounded-3xl p-5">
            <p className="text-sm uppercase tracking-[0.18em] text-emerald-200">Best Model</p>
            {topModel ? (
              <>
                <h2 className="mt-3 text-2xl font-semibold text-emerald-100">{topModel.label}</h2>
                <p className="mt-1 text-slate-300">Success score: {topModel.score.toFixed(2)}%</p>
              </>
            ) : (
              <p className="mt-3 text-slate-400">Model ranking will appear once data arrives.</p>
            )}
          </article>
          <article className="card-glow rounded-3xl p-5">
            <p className="text-sm uppercase tracking-[0.18em] text-cyan-200">Best Language</p>
            {topLanguage ? (
              <>
                <h2 className="mt-3 text-2xl font-semibold text-cyan-100">{topLanguage.label}</h2>
                <p className="mt-1 text-slate-300">Success score: {topLanguage.score.toFixed(2)}%</p>
              </>
            ) : (
              <p className="mt-3 text-slate-400">Language ranking will appear once data arrives.</p>
            )}
          </article>
        </section>
      )}
    </section>
  );
}
