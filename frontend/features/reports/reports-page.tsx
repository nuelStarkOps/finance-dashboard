"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Download, FileText, PiggyBank, Scale, TrendingDown, TrendingUp } from "lucide-react";
import { useState } from "react";

import { CurrencyDisplay } from "@/components/ui/currency-display";
import { EmptyState } from "@/components/ui/empty-state";
import { StatCard } from "@/components/ui/stat-card";
import { financeApi, type Insight } from "@/lib/api/finance";
import { useAuth } from "@/lib/auth/context";
import { formatMinor, minorToMajor } from "@/lib/currency";

const inputClass =
  "rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 outline-none focus:border-indigo-500 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100";

function thisYear(): { from: string; to: string } {
  const now = new Date();
  return { from: `${now.getFullYear()}-01-01`, to: now.toISOString().slice(0, 10) };
}

const INSIGHT_STYLES: Record<Insight["severity"], string> = {
  info: "border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900",
  warning: "border-amber-200 bg-amber-50 dark:border-amber-900 dark:bg-amber-950/40",
  positive: "border-emerald-200 bg-emerald-50 dark:border-emerald-900 dark:bg-emerald-950/40",
};

export default function ReportsPage() {
  const { preferences } = useAuth();
  const currency = preferences?.preferred_currency ?? "NGN";
  const [range, setRange] = useState(thisYear);

  const cashflow = useQuery({
    queryKey: ["reports", "cashflow", range],
    queryFn: () => financeApi.reportsCashflow({ ...range, currency, group: "month" }),
  });
  const spending = useQuery({
    queryKey: ["reports", "spending", range],
    queryFn: () => financeApi.reportsSpending({ ...range, currency }),
  });
  const savingsRate = useQuery({
    queryKey: ["reports", "savings-rate", range],
    queryFn: () => financeApi.reportsSavingsRate({ ...range, currency }),
  });
  const insights = useQuery({
    queryKey: ["reports", "insights", range],
    queryFn: () => financeApi.reportsInsights({ ...range, currency }),
  });
  const budgets = useQuery({
    queryKey: ["reports", "budgets"],
    queryFn: financeApi.reportsBudgets,
  });

  const chartData = (cashflow.data ?? []).map((d) => ({
    period: d.period,
    Income: minorToMajor(d.income_minor),
    Expenses: minorToMajor(d.expenses_minor),
  }));

  const hasData = (cashflow.data?.length ?? 0) > 0 || (spending.data?.length ?? 0) > 0;
  const s = savingsRate.data;

  async function handleExport() {
    const csv = await financeApi.exportReportCsv({
      from: range.from || null,
      to: range.to || null,
      currency,
    });
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "pfos-report.csv";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Reports</h1>
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            Understand your income, spending and savings.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <input
            type="date"
            value={range.from}
            onChange={(e) => setRange((r) => ({ ...r, from: e.target.value }))}
            className={inputClass}
            aria-label="From"
          />
          <span className="text-zinc-500">→</span>
          <input
            type="date"
            value={range.to}
            onChange={(e) => setRange((r) => ({ ...r, to: e.target.value }))}
            className={inputClass}
            aria-label="To"
          />
          <button
            type="button"
            onClick={handleExport}
            className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white transition hover:bg-indigo-500"
          >
            <Download className="h-4 w-4" /> Export CSV
          </button>
        </div>
      </div>

      {!hasData ? (
        <EmptyState
          icon={FileText}
          title="No data to report"
          description="Record transactions to see financial reports here."
        />
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard
              label="Income"
              icon={TrendingUp}
              tone="positive"
              value={<CurrencyDisplay minor={s?.income_minor ?? 0} currency={currency} />}
            />
            <StatCard
              label="Expenses"
              icon={TrendingDown}
              tone="negative"
              value={<CurrencyDisplay minor={s?.expenses_minor ?? 0} currency={currency} />}
            />
            <StatCard
              label="Net cash flow"
              icon={Scale}
              value={<CurrencyDisplay minor={s?.net_minor ?? 0} currency={currency} />}
            />
            <StatCard
              label="Savings rate"
              icon={PiggyBank}
              value={s?.savings_rate_percent != null ? `${s.savings_rate_percent}%` : "—"}
            />
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <section className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
              <h2 className="mb-4 text-sm font-semibold">Income vs expenses</h2>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e4e4e7" vertical={false} />
                    <XAxis
                      dataKey="period"
                      tick={{ fontSize: 12 }}
                      tickLine={false}
                      axisLine={false}
                    />
                    <YAxis tick={{ fontSize: 12 }} tickLine={false} axisLine={false} />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="Income" fill="#34d399" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="Expenses" fill="#f87171" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </section>

            <section className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
              <h2 className="mb-4 text-sm font-semibold">Spending by category</h2>
              {spending.data?.length ? (
                <ul className="space-y-3">
                  {spending.data.map((c) => (
                    <li key={c.name} className="text-sm">
                      <div className="mb-1 flex items-center justify-between">
                        <span className="flex items-center gap-2 text-zinc-700 dark:text-zinc-200">
                          <span
                            className="h-2 w-2 rounded-full"
                            style={{ background: c.color ?? "#6366f1" }}
                          />
                          {c.name}
                        </span>
                        <span className="tabular-nums text-zinc-500 dark:text-zinc-400">
                          {formatMinor(c.total_minor, currency)} · {c.percent}%
                        </span>
                      </div>
                      <div className="h-2 w-full overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-700">
                        <div
                          className="h-full rounded-full bg-indigo-500"
                          style={{ width: `${c.percent}%` }}
                        />
                      </div>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="py-10 text-center text-sm text-zinc-500">
                  No spending in this period.
                </p>
              )}
            </section>
          </div>

          {insights.data && insights.data.length > 0 && (
            <section>
              <h2 className="mb-3 text-sm font-semibold">Insights</h2>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {insights.data.map((insight) => (
                  <div
                    key={`${insight.type}-${insight.title}`}
                    className={`rounded-xl border p-4 ${INSIGHT_STYLES[insight.severity]}`}
                  >
                    <p className="text-sm font-medium">{insight.title}</p>
                    <p className="mt-1 text-xs text-zinc-600 dark:text-zinc-400">
                      {insight.message}
                    </p>
                  </div>
                ))}
              </div>
            </section>
          )}

          {budgets.data && budgets.data.length > 0 && (
            <section className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
              <h2 className="mb-3 text-sm font-semibold">Budget performance</h2>
              <ul className="space-y-3">
                {budgets.data.map((b) => (
                  <li key={b.budget_id} className="text-sm">
                    <div className="mb-1 flex items-center justify-between">
                      <span className="text-zinc-700 dark:text-zinc-200">{b.name}</span>
                      <span className="tabular-nums text-zinc-500 dark:text-zinc-400">
                        {formatMinor(b.spent_minor, b.currency_code)} /{" "}
                        {formatMinor(b.limit_minor, b.currency_code)}
                      </span>
                    </div>
                    <div className="h-2 w-full overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-700">
                      <div
                        className={`h-full rounded-full ${b.status === "over" ? "bg-red-500" : b.status === "warning" ? "bg-amber-500" : "bg-indigo-500"}`}
                        style={{ width: `${Math.min(b.usage_percent ?? 0, 100)}%` }}
                      />
                    </div>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </>
      )}
    </div>
  );
}
