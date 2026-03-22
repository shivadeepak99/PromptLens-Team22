"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type ChartPoint = {
  name: string;
  value: number;
};

type ChartCardProps = {
  title: string;
  subtitle: string;
  data: ChartPoint[];
  colorClass?: string;
  accent?: "cyan" | "emerald";
};

export default function ChartCard({
  title,
  subtitle,
  data,
  colorClass = "#22d3ee",
  accent = "cyan",
}: ChartCardProps) {
  const hasData = data.length > 0;
  const average = hasData
    ? (data.reduce((sum, item) => sum + item.value, 0) / data.length).toFixed(1)
    : "0.0";

  const glowClass = accent === "cyan" ? "shadow-cyan-500/20" : "shadow-emerald-500/20";

  return (
    <article className={`card-glow rounded-3xl p-5 shadow-2xl ${glowClass}`}>
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-slate-100">{title}</h2>
          <p className="mt-1 text-sm text-slate-400">{subtitle}</p>
        </div>
        <div className="rounded-xl border border-slate-700/60 bg-slate-900/60 px-3 py-2 text-right">
          <p className="text-[11px] uppercase tracking-[0.18em] text-slate-500">Avg</p>
          <p className="text-base font-semibold text-slate-100">{average}%</p>
        </div>
      </div>

      <div className="h-72 w-full">
        {hasData ? (
          <ResponsiveContainer>
            <BarChart data={data} margin={{ top: 18, right: 6, left: -24, bottom: 2 }}>
              <defs>
                <linearGradient id={`bar-${accent}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={colorClass} stopOpacity={1} />
                  <stop offset="100%" stopColor={colorClass} stopOpacity={0.45} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="4 4" stroke="#1e293b" />
              <XAxis dataKey="name" stroke="#94a3b8" tick={{ fontSize: 12 }} />
              <YAxis stroke="#94a3b8" tick={{ fontSize: 12 }} />
              <Tooltip
                cursor={{ fill: "rgba(34, 211, 238, 0.08)" }}
                contentStyle={{
                  background: "#0b1220",
                  border: "1px solid rgba(34, 211, 238, 0.25)",
                  borderRadius: "12px",
                  color: "#e2e8f0",
                }}
                formatter={(value) => {
                  const numericValue =
                    typeof value === "number"
                      ? value
                      : typeof value === "string"
                        ? Number(value)
                        : 0;
                  const safeValue = Number.isFinite(numericValue) ? numericValue : 0;

                  return [`${safeValue}%`, "Success"];
                }}
              />
              <Bar dataKey="value" fill={`url(#bar-${accent})`} radius={[10, 10, 2, 2]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="grid h-full place-items-center rounded-2xl border border-dashed border-slate-700/70 bg-slate-950/35 p-4 text-center">
            <div>
              <p className="text-sm font-medium text-slate-300">No chart data available</p>
              <p className="mt-1 text-xs text-slate-500">Data will appear after backend analytics responds.</p>
            </div>
          </div>
        )}
      </div>
    </article>
  );
}
