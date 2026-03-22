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
};

export default function ChartCard({
  title,
  subtitle,
  data,
  colorClass = "#3b82f6",
}: ChartCardProps) {
  const hasData = data.length > 0;

  return (
    <article className="metric-card flex flex-col">
      <div className="mb-6">
         <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-widest">{title}</h2>
         <p className="mt-1 text-xs text-slate-500">{subtitle}</p>
      </div>

      <div className="h-64 w-full mt-auto">
        {hasData ? (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
              <XAxis dataKey="name" stroke="#64748b" tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis stroke="#64748b" tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={(val) => `${val}%`} />
              <Tooltip
                cursor={{ fill: "rgba(51, 65, 85, 0.4)" }}
                contentStyle={{
                  background: "#0f172a",
                  border: "1px solid #334155",
                  borderRadius: "6px",
                  color: "#f8fafc",
                  fontSize: "12px"
                }}
                formatter={(value) => [`${Number(value).toFixed(1)}%`, "Success Yield"]}
              />
              <Bar dataKey="value" fill={colorClass} radius={[2, 2, 0, 0]} maxBarSize={40} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-full flex items-center justify-center border border-dashed border-slate-700 rounded-md bg-slate-800/50">
            <p className="text-xs font-medium text-slate-500 uppercase">Awaiting Stream</p>
          </div>
        )}
      </div>
    </article>
  );
}
