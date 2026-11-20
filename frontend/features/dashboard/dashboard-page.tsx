"use client";

import { useQuery } from "@tanstack/react-query";
import {
  ArrowDownToLine,
  ArrowUpFromLine,
  ArrowRightLeft,
  Receipt,
  Scale,
  Wallet,
} from "lucide-react";
import { useMemo, useState } from "react";

import Link from "next/link";

import { CurrencyDisplay } from "@/components/ui/currency-display";
import { EmptyState } from "@/components/ui/empty-state";
import { SkeletonCard } from "@/components/ui/loading-skeleton";
import { StatCard } from "@/components/ui/stat-card";
import {
  financeApi,
  type AccountOverviewItem,
  type BudgetOverviewItem,
  type Transaction,
} from "@/lib/api/finance";
import { useAuth } from "@/lib/auth/context";
import { formatMinor } from "@/lib/currency";

import { CashflowChart, SpendingChart } from "./charts";

const PERIODS = [
  { key: "this_month", label: "This month" },
  { key: "last_30", label: "Last 30 days" },
  { key: "last_3m", label: "Last 3 months" },
  { key: "this_year", label: "This year" },
  { key: "all", label: "All time" },
];

function periodRange(key: string): { from?: string; to?: string } {
  const now = new Date();
  const y = now.getFullYear();
  const m = now.getMonth();
  const d = now.getDate();
  const iso = (dt: Date) =>
    `${dt.getFullYear()}-${String(dt.getMonth() + 1).padStart(2, "0")}-${String(
      dt.getDate(),
    ).padStart(2, "0")}`;
  switch (key) {
    case "this_month":
      return { from: iso(new Date(y, m, 1)) };
    case "last_30":
      return { from: iso(new Date(y, m, d - 29)) };
    case "last_3m":
      return { from: iso(new Date(y, m - 2, d)) };
    case "this_year":
      return { from: iso(new Date(y, 0, 1)) };
    default:
      return {};
  }
}

function TransactionRow({ tx }: { tx: Transaction }) {
  const isTransfer = tx.type === "TRANSFER";
  const sign = tx.type === "INCOME" ? "+" : tx.type === "EXPENSE" ? "−" : "";
  const tone = isTransfer
    ? "text-zinc-600 dark:text-zinc-300"
    : tx.type === "INCOME"
      ? "text-emerald-600 dark:text-emerald-400"
      : "text-red-600 dark:text-red-400";
  const Icon = isTransfer
    ? ArrowRightLeft
    : tx.type === "INCOME"
      ? ArrowDownToLine
      : ArrowUpFromLine;

  return (
    <li className="flex items-center gap-3 py-2.5">
      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-zinc-100 dark:bg-zinc-800">
        <Icon className="h-4 w-4 text-zinc-500 dark:text-zinc-400" />
      </span>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium">{tx.description}</p>
        <p className="truncate text-xs text-zinc-500 dark:text-zinc-400">
          {tx.category?.name ?? "Transfer"} · {tx.transaction_date}
        </p>
      </div>
      <span className={`text-sm font-medium tabular-nums ${tone}`}>
        {sign}
        {formatMinor(tx.amount_minor, tx.currency_code)}
      </span>
    </li>
  );
}

function BudgetRow({ item }: { item: BudgetOverviewItem }) {
  const width = Math.min(item.usage_percent ?? 0, 100);
  const color =
    item.status === "over"
      ? "bg-red-500"
      : item.status === "warning"
        ? "bg-amber-500"
        : "bg-indigo-500";
  return (
    <li className="py-2.5">
      <div className="mb-1 flex items-center justify-between text-sm">
        <span className="text-zinc-700 dark:text-zinc-200">{item.name}</span>
        <span className="tabular-nums text-zinc-500 dark:text-zinc-400">
          {formatMinor(item.spent_minor, item.currency_code)} /{" "}
          {formatMinor(item.limit_minor, item.currency_code)}
        </span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-700">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${width}%` }} />
      </div>
    </li>
  );
}

export default function DashboardPage() {
  const { user, preferences } = useAuth();
  const [period, setPeriod] = useState("this_month");

  const range = useMemo(() => periodRange(period), [period]);
  const preferred = preferences?.preferred_currency ?? "NGN";

  const summary = useQuery({
    queryKey: ["dashboard", "summary", range],
    queryFn: () => financeApi.summary(range),
  });
  const cashflow = useQuery({
    queryKey: ["dashboard", "cashflow", range],
    queryFn: () => financeApi.cashflow({ ...range, group: "day" }),
  });
  const spending = useQuery({
    queryKey: ["dashboard", "spending", range],
    queryFn: () => financeApi.spending(range),
  });
  const recent = useQuery({
    queryKey: ["dashboard", "recent"],
    queryFn: () => financeApi.recentTransactions(6),
  });
  const accountOverview = useQuery({
    queryKey: ["dashboard", "accounts"],
    queryFn: financeApi.accountOverview,
  });
  const budgetOverview = useQuery({
    queryKey: ["dashboard", "budgets"],
    queryFn: financeApi.budgetOverview,
  });
  const savingsGoals = useQuery({
    queryKey: ["savings-goals"],
    queryFn: financeApi.savingsGoals,
  });
  const bills = useQuery({
    queryKey: ["bills"],
    queryFn: financeApi.bills,
  });

  const loading = summary.isLoading || cashflow.isLoading || spending.isLoading;
  const hasData = (recent.data?.length ?? 0) > 0 || (accountOverview.data?.length ?? 0) > 0;

  const accountsByCurrency: Record<string, AccountOverviewItem[] | undefined> = {};
  for (const account of accountOverview.data ?? []) {
    (accountsByCurrency[account.currency_code] ??= []).push(account);
  }

  const s = summary.data;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            Welcome{user ? `, ${user.display_name}` : ""}
          </h1>
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            Your financial overview at a glance.
          </p>
        </div>
        <select
          value={period}
          onChange={(e) => setPeriod(e.target.value)}
          aria-label="Period"
          className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 outline-none focus:border-indigo-500 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
        >
          {PERIODS.map((p) => (
            <option key={p.key} value={p.key}>
              {p.label}
            </option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[0, 1, 2, 3].map((i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            label="Total balance"
            icon={Wallet}
            value={<CurrencyDisplay minor={s?.total_balance_minor ?? 0} currency={preferred} />}
          />
          <StatCard
            label="Income"
            icon={ArrowDownToLine}
            tone="positive"
            value={<CurrencyDisplay minor={s?.income_minor ?? 0} currency={preferred} />}
          />
          <StatCard
            label="Expenses"
            icon={ArrowUpFromLine}
            tone="negative"
            value={<CurrencyDisplay minor={s?.expenses_minor ?? 0} currency={preferred} />}
          />
          <StatCard
            label="Net cash flow"
            icon={Scale}
            value={<CurrencyDisplay minor={s?.net_cashflow_minor ?? 0} currency={preferred} />}
          />
        </div>
      )}

      {!loading && !hasData ? (
        <EmptyState
          icon={Receipt}
          title="No transactions yet"
          description="Use “Add transaction” in the header to record your first income or expense."
        />
      ) : (
        <div className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-2">
            <section className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
              <h2 className="mb-4 text-sm font-semibold">Cash flow</h2>
              {cashflow.data?.length ? (
                <CashflowChart data={cashflow.data} />
              ) : (
                <p className="py-16 text-center text-sm text-zinc-500 dark:text-zinc-400">
                  No cash flow in this period.
                </p>
              )}
            </section>

            <section className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
              <h2 className="mb-4 text-sm font-semibold">Spending by category</h2>
              {spending.data?.length ? (
                <SpendingChart data={spending.data} />
              ) : (
                <p className="py-16 text-center text-sm text-zinc-500 dark:text-zinc-400">
                  No spending in this period.
                </p>
              )}
            </section>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <section className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
              <h2 className="mb-2 text-sm font-semibold">Recent transactions</h2>
              {recent.data?.length ? (
                <ul className="divide-y divide-zinc-100 dark:divide-zinc-800">
                  {recent.data.map((tx) => (
                    <TransactionRow key={tx.id} tx={tx} />
                  ))}
                </ul>
              ) : (
                <p className="py-10 text-center text-sm text-zinc-500 dark:text-zinc-400">
                  Nothing recorded yet.
                </p>
              )}
            </section>

            <section className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
              <h2 className="mb-2 text-sm font-semibold">Accounts</h2>
              {accountOverview.data?.length ? (
                <div className="space-y-4">
                  {Object.entries(accountsByCurrency).map(([currency, accounts]) => {
                    const total = accounts!.reduce((sum, a) => sum + a.balance_minor, 0);
                    return (
                      <div key={currency}>
                        <div className="mb-1 flex items-center justify-between text-xs font-medium text-zinc-500 dark:text-zinc-400">
                          <span>{currency}</span>
                          <span className="tabular-nums">{formatMinor(total, currency)}</span>
                        </div>
                        <ul className="divide-y divide-zinc-100 dark:divide-zinc-800">
                          {accounts!.map((a) => (
                            <li
                              key={a.id}
                              className="flex items-center justify-between py-2 text-sm"
                            >
                              <span className="text-zinc-700 dark:text-zinc-200">{a.name}</span>
                              <span className="font-medium tabular-nums text-zinc-900 dark:text-zinc-100">
                                {formatMinor(a.balance_minor, a.currency_code)}
                              </span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="py-10 text-center text-sm text-zinc-500 dark:text-zinc-400">
                  No accounts yet.
                </p>
              )}
            </section>
          </div>

          {budgetOverview.data && budgetOverview.data.length > 0 && (
            <section className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
              <div className="mb-2 flex items-center justify-between">
                <h2 className="text-sm font-semibold">Budgets</h2>
                <Link
                  href="/budgets"
                  className="text-sm text-indigo-600 hover:underline dark:text-indigo-400"
                >
                  View all
                </Link>
              </div>
              <ul className="divide-y divide-zinc-100 dark:divide-zinc-800">
                {budgetOverview.data.map((b) => (
                  <BudgetRow key={b.budget_id} item={b} />
                ))}
              </ul>
            </section>
          )}

          {(savingsGoals.data?.length ?? 0) > 0 || (bills.data?.length ?? 0) > 0 ? (
            <div className="grid gap-6 lg:grid-cols-2">
              {(savingsGoals.data ?? []).filter((g) => g.status === "ACTIVE").length > 0 && (
                <section className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
                  <div className="mb-2 flex items-center justify-between">
                    <h2 className="text-sm font-semibold">Savings goals</h2>
                    <Link
                      href="/savings"
                      className="text-sm text-indigo-600 hover:underline dark:text-indigo-400"
                    >
                      View all
                    </Link>
                  </div>
                  <ul className="space-y-3">
                    {(savingsGoals.data ?? [])
                      .filter((g) => g.status === "ACTIVE")
                      .slice(0, 3)
                      .map((goal) => (
                        <li key={goal.id}>
                          <div className="mb-1 flex justify-between text-sm">
                            <span className="text-zinc-700 dark:text-zinc-200">{goal.name}</span>
                            <span className="tabular-nums text-zinc-500 dark:text-zinc-400">
                              {goal.progress_percent}%
                            </span>
                          </div>
                          <div className="h-2 w-full overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-700">
                            <div
                              className="h-full rounded-full bg-indigo-500"
                              style={{ width: `${Math.min(goal.progress_percent, 100)}%` }}
                            />
                          </div>
                        </li>
                      ))}
                  </ul>
                </section>
              )}

              {(bills.data ?? []).filter((b) => b.status === "ACTIVE").length > 0 && (
                <section className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
                  <div className="mb-2 flex items-center justify-between">
                    <h2 className="text-sm font-semibold">Upcoming bills</h2>
                    <Link
                      href="/bills"
                      className="text-sm text-indigo-600 hover:underline dark:text-indigo-400"
                    >
                      View all
                    </Link>
                  </div>
                  <ul className="divide-y divide-zinc-100 dark:divide-zinc-800">
                    {(bills.data ?? [])
                      .filter((b) => b.status === "ACTIVE")
                      .slice(0, 3)
                      .map((b) => (
                        <li key={b.id} className="flex items-center justify-between py-2 text-sm">
                          <span className="text-zinc-700 dark:text-zinc-200">{b.name}</span>
                          <span className="tabular-nums text-zinc-500 dark:text-zinc-400">
                            {formatMinor(b.amount_minor, b.currency_code)} · {b.next_due_date}
                          </span>
                        </li>
                      ))}
                  </ul>
                </section>
              )}
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}
