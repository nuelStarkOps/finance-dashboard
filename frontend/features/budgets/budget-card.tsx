"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Trash2 } from "lucide-react";

import { financeApi, type Budget, type BudgetStatus } from "@/lib/api/finance";
import { formatMinor } from "@/lib/currency";

function ProgressBar({ percent, status }: { percent: number | null; status: BudgetStatus }) {
  const width = Math.min(Math.max(percent ?? 0, 0), 100);
  const color =
    status === "over" ? "bg-red-500" : status === "warning" ? "bg-amber-500" : "bg-indigo-500";
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-700">
      <div className={`h-full rounded-full ${color}`} style={{ width: `${width}%` }} />
    </div>
  );
}

function StatusBadge({ status }: { status: BudgetStatus }) {
  if (status === "over") {
    return (
      <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700 dark:bg-red-950 dark:text-red-300">
        Over budget
      </span>
    );
  }
  if (status === "warning") {
    return (
      <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700 dark:bg-amber-950 dark:text-amber-300">
        Near limit
      </span>
    );
  }
  return (
    <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs font-medium text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300">
      On track
    </span>
  );
}

export function BudgetCard({ budget }: { budget: Budget }) {
  const queryClient = useQueryClient();
  const perf = useQuery({
    queryKey: ["budget-performance", budget.id],
    queryFn: () => financeApi.budgetPerformance(budget.id),
  });
  const archive = useMutation({
    mutationFn: () => financeApi.archiveBudget(budget.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["budgets"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  const p = perf.data;

  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold">{budget.name}</h3>
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            {budget.start_date} → {budget.end_date}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {p && <StatusBadge status={p.status} />}
          <button
            type="button"
            onClick={() => archive.mutate()}
            disabled={archive.isPending}
            aria-label="Archive budget"
            className="rounded-lg p-1.5 text-zinc-400 transition hover:bg-zinc-100 hover:text-red-600 dark:hover:bg-zinc-800"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>

      {p && (
        <div className="space-y-4">
          {p.total_limit_minor != null && (
            <div>
              <div className="mb-1 flex items-center justify-between text-sm">
                <span className="text-zinc-600 dark:text-zinc-300">Overall</span>
                <span className="tabular-nums text-zinc-500 dark:text-zinc-400">
                  {formatMinor(p.total_spent_minor, p.currency_code)} /{" "}
                  {formatMinor(p.total_limit_minor, p.currency_code)}
                </span>
              </div>
              <ProgressBar percent={p.total_usage_percent} status={p.status} />
            </div>
          )}

          {p.items.map((item) => (
            <div key={item.category_id}>
              <div className="mb-1 flex items-center justify-between text-sm">
                <span className="flex items-center gap-2 text-zinc-600 dark:text-zinc-300">
                  <span
                    className="h-2 w-2 rounded-full"
                    style={{ background: item.color ?? "#6366f1" }}
                  />
                  {item.name}
                </span>
                <span className="tabular-nums text-zinc-500 dark:text-zinc-400">
                  {formatMinor(item.spent_minor, p.currency_code)} /{" "}
                  {formatMinor(item.limit_minor, p.currency_code)}
                </span>
              </div>
              <ProgressBar percent={item.usage_percent} status={item.status} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
