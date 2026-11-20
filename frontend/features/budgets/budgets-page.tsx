"use client";

import { useQuery } from "@tanstack/react-query";
import { PieChart, Plus } from "lucide-react";
import { useState } from "react";

import { EmptyState } from "@/components/ui/empty-state";
import { financeApi } from "@/lib/api/finance";

import { BudgetCard } from "./budget-card";
import { CreateBudgetDialog } from "./create-budget-dialog";

export default function BudgetsPage() {
  const [open, setOpen] = useState(false);
  const budgets = useQuery({ queryKey: ["budgets"], queryFn: financeApi.budgets });
  const active = (budgets.data ?? []).filter((b) => b.status === "ACTIVE");

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Budgets</h1>
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            Track spending against your limits.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setOpen(true)}
          className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white transition hover:bg-indigo-500"
        >
          <Plus className="h-4 w-4" /> New budget
        </button>
      </div>

      {active.length === 0 ? (
        <EmptyState
          icon={PieChart}
          title="No budgets yet"
          description="Create a budget to start controlling your spending."
          action={
            <button
              type="button"
              onClick={() => setOpen(true)}
              className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-indigo-500"
            >
              Create budget
            </button>
          }
        />
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          {active.map((b) => (
            <BudgetCard key={b.id} budget={b} />
          ))}
        </div>
      )}

      <CreateBudgetDialog open={open} onClose={() => setOpen(false)} />
    </div>
  );
}
