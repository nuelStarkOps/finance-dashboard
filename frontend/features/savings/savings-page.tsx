"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Minus, Plus, Target } from "lucide-react";
import { useState } from "react";

import { EmptyState } from "@/components/ui/empty-state";
import { financeApi, type SavingsGoal } from "@/lib/api/finance";
import { formatMinor } from "@/lib/currency";

import { ContributeDialog, CreateGoalDialog } from "./dialogs";

function ProgressBar({ percent }: { percent: number }) {
  const width = Math.min(Math.max(percent, 0), 100);
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-700">
      <div className="h-full rounded-full bg-indigo-500" style={{ width: `${width}%` }} />
    </div>
  );
}

export default function SavingsPage() {
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [activeGoal, setActiveGoal] = useState<SavingsGoal | null>(null);
  const [withdrawMode, setWithdrawMode] = useState(false);

  const goals = useQuery({ queryKey: ["savings-goals"], queryFn: financeApi.savingsGoals });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Savings Goals</h1>
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            Track progress toward your financial targets.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setCreateOpen(true)}
          className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white transition hover:bg-indigo-500"
        >
          <Plus className="h-4 w-4" /> New goal
        </button>
      </div>

      {(goals.data ?? []).length === 0 ? (
        <EmptyState
          icon={Target}
          title="No savings goals yet"
          description="Create a goal to start measuring your progress."
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {(goals.data ?? []).map((goal) => (
            <div
              key={goal.id}
              className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900"
            >
              <div className="mb-3 flex items-start justify-between">
                <div>
                  <h3 className="text-sm font-semibold">{goal.name}</h3>
                  <p className="text-xs text-zinc-500 dark:text-zinc-400">
                    {goal.priority.toLowerCase()} · {goal.currency_code}
                  </p>
                </div>
                <span className="text-sm font-semibold tabular-nums">{goal.progress_percent}%</span>
              </div>
              <ProgressBar percent={goal.progress_percent} />
              <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-300">
                {formatMinor(goal.allocated_minor, goal.currency_code)} of{" "}
                {formatMinor(goal.target_minor, goal.currency_code)}
              </p>
              <div className="mt-4 flex gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setWithdrawMode(false);
                    setActiveGoal(goal);
                  }}
                  className="inline-flex flex-1 items-center justify-center gap-1 rounded-lg bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-500"
                >
                  <Plus className="h-3.5 w-3.5" /> Add
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setWithdrawMode(true);
                    setActiveGoal(goal);
                  }}
                  className="inline-flex items-center justify-center rounded-lg border border-zinc-300 px-3 py-1.5 text-sm font-medium text-zinc-600 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
                >
                  <Minus className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <CreateGoalDialog open={createOpen} onClose={() => setCreateOpen(false)} />
      <ContributeDialog
        goal={activeGoal}
        withdrawMode={withdrawMode}
        onClose={() => setActiveGoal(null)}
        onSaved={() => queryClient.invalidateQueries({ queryKey: ["savings-goals"] })}
      />
    </div>
  );
}
