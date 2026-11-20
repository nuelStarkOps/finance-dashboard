"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { CashflowPoint, SpendingCategory } from "@/lib/api/finance";
import { minorToMajor } from "@/lib/currency";

export function CashflowChart({ data }: { data: CashflowPoint[] }) {
  const chartData = data.map((d) => ({
    period: d.period,
    Income: minorToMajor(d.income_minor),
    Expenses: minorToMajor(d.expenses_minor),
  }));

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e4e4e7" vertical={false} />
          <XAxis dataKey="period" tick={{ fontSize: 12 }} tickLine={false} axisLine={false} />
          <YAxis tick={{ fontSize: 12 }} tickLine={false} axisLine={false} />
          <Tooltip />
          <Legend />
          <Bar dataKey="Income" fill="#34d399" radius={[3, 3, 0, 0]} />
          <Bar dataKey="Expenses" fill="#f87171" radius={[3, 3, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function SpendingChart({ data }: { data: SpendingCategory[] }) {
  const pieData = data.map((c) => ({
    ...c,
    value: minorToMajor(c.total_minor),
  }));

  return (
    <div className="flex flex-col items-center gap-6 sm:flex-row sm:items-center">
      <div className="h-48 w-48 shrink-0">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={pieData}
              dataKey="value"
              nameKey="name"
              innerRadius={48}
              outerRadius={80}
              paddingAngle={2}
              strokeWidth={0}
            >
              {pieData.map((c) => (
                <Cell key={c.category_id} fill={c.color ?? "#6366f1"} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>

      <ul className="w-full space-y-2">
        {pieData.map((c) => (
          <li key={c.category_id} className="flex items-center justify-between text-sm">
            <span className="flex items-center gap-2 text-zinc-700 dark:text-zinc-200">
              <span
                className="h-2.5 w-2.5 rounded-full"
                style={{ background: c.color ?? "#6366f1" }}
              />
              {c.name}
            </span>
            <span className="text-zinc-500 dark:text-zinc-400">{c.value.toFixed(2)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
