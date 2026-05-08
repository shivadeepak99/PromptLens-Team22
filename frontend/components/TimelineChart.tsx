"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';

type TimelineChartProps = {
  data: any[];
};

export default function TimelineChart({ data }: TimelineChartProps) {
  // Extract all model names from the first data point, excluding 'day'
  const models = data.length > 0 ? Object.keys(data[0]).filter(k => k !== 'day') : [];
  
  // A clean distinct palette suitable for enterprise dashboards
  const colors = ["#3b82f6", "#10b981", "#8b5cf6", "#f59e0b", "#ec4899", "#06b6d4"];

  const formatXAxis = (tickItem: string) => {
    // Expected format 'YYYY-MM-DD', displaying 'MM/DD'
    if (!tickItem) return '';
    const parts = tickItem.split('-');
    if (parts.length >= 3) {
      return `${parts[1]}/${parts[2]}`;
    }
    return tickItem;
  };

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
        <XAxis 
           dataKey="day" 
           stroke="#64748b" 
           tick={{ fill: "#64748b", fontSize: 11 }} 
           axisLine={false} 
           tickLine={false}
           minTickGap={20}
           tickFormatter={formatXAxis}
        />
        <YAxis 
           stroke="#64748b" 
           tick={{ fill: "#64748b", fontSize: 11 }} 
           axisLine={false} 
           tickLine={false} 
           tickFormatter={(val) => `${val}%`}
           domain={['dataMin - 5', 'dataMax + 5']}
        />
        <Tooltip
          contentStyle={{
            background: "#0f172a",
            border: "1px solid #334155",
            borderRadius: "6px",
            color: "#f8fafc",
            fontSize: "12px",
            boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.3)"
          }}
          itemStyle={{ fontSize: "12px", fontWeight: 500 }}
          labelStyle={{ color: "#94a3b8", marginBottom: "6px", fontSize: "11px", textTransform: "uppercase" }}
          formatter={(value: any) => [`${Number(value).toFixed(1)}%`, undefined]}
        />
        <Legend 
           wrapperStyle={{ fontSize: "11px", color: "#94a3b8", paddingTop: "10px" }}
           iconType="circle"
           iconSize={6}
        />
        {models.map((model, idx) => (
          <Line 
            key={model}
            type="monotone" 
            dataKey={model} 
            name={model}
            stroke={colors[idx % colors.length]} 
            strokeWidth={2}
            dot={{ r: 2, fill: colors[idx % colors.length], strokeWidth: 0 }}
            activeDot={{ r: 4, stroke: "#0f172a", strokeWidth: 2 }}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
