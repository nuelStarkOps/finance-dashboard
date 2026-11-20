"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, X } from "lucide-react";
import { useState } from "react";

import { financeApi, type BudgetInput } from "@/lib/api/finance";
import { useAuth } from "@/lib/auth/context";
import { toMinorUnits } from "@/lib/currency";

const inputClass =
  "w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/30 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100";

function pad(n: number): string {
  return String(n).padStart(2, "0");
}

function monthDefaults(): { first: string; last: string } {
  const now = new Date();
  const y = now.getFullYear();
  const m = now.getMonth();
  const first = `${y}-${pad(m + 1)}-01`;
  const last = `${y}-${pad(m + 1)}-${pad(new Date(y, m + 1, 0).getDate())}`;
  return { first, last };
}

interface ItemDraft {
  category_id: string;
  limit_minor: string;
}

export function CreateBudgetDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const queryClient = useQueryClient();
  const { preferences } = useAuth();

  const [name, setName] = useState("");
  const [currency, setCurrency] = useState(preferences?.preferred_currency ?? "NGN");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [totalLimit, setTotalLimit] = useState("");
  const [items, setItems] = useState<ItemDraft[]>([]);
  const [error, setError] = useState<string | null>(null);

  const { data: categories = [] } = useQuery({
    queryKey: ["categories", "EXPENSE"],
    queryFn: () => financeApi.categories("EXPENSE"),
    enabled: open,
  });

  const mutation = useMutation({
    mutationFn: financeApi.createBudget,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["budgets"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      reset();
      onClose();
    },
    onError: (err) => setError(err instanceof Error ? err.message : "Failed to create budget"),
  });

  function reset() {
    setName("");
    setStartDate("");
    setEndDate("");
    setTotalLimit("");
    setItems([]);
    setError(null);
  }

  function addItem() {
    setItems((prev) => [...prev, { category_id: "", limit_minor: "" }]);
  }

  function updateItem(index: number, patch: Partial<ItemDraft>) {
    setItems((prev) => prev.map((it, i) => (i === index ? { ...it, ...patch } : it)));
  }

  function removeItem(index: number) {
    setItems((prev) => prev.filter((_, i) => i !== index));
  }

  function availableFor(index: number) {
    return categories.filter((c) => !items.some((it, i) => i !== index && it.category_id === c.id));
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    const { first, last } = monthDefaults();
    const payload: BudgetInput = {
      name,
      currency_code: currency,
      start_date: startDate || first,
      end_date: endDate || last,
      total_limit_minor: totalLimit ? toMinorUnits(Number(totalLimit)) : null,
      items: items
        .filter((i) => i.category_id)
        .map((i) => ({
          category_id: i.category_id,
          limit_minor: toMinorUnits(Number(i.limit_minor) || 0),
        })),
    };
    mutation.mutate(payload);
  }

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-2xl bg-white p-6 shadow-xl dark:bg-zinc-900">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">New budget</h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="rounded-lg p-1 text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-800"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {error && (
          <p className="mb-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-950/50 dark:text-red-300">
            {error}
          </p>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium">Name</label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. November budget"
              className={inputClass}
            />
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium">Currency</label>
              <select
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                className={inputClass}
              >
                {["NGN", "USD", "GBP", "EUR", "GHS", "KES", "ZAR"].map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">From</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className={inputClass}
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">To</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className={inputClass}
              />
            </div>
          </div>
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            Dates default to this month if left blank.
          </p>

          <div>
            <label className="mb-1 block text-sm font-medium">
              Overall limit ({currency}) — optional
            </label>
            <input
              type="number"
              min="0"
              step="0.01"
              value={totalLimit}
              onChange={(e) => setTotalLimit(e.target.value)}
              placeholder="0.00"
              className={inputClass}
            />
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">Category limits (optional)</label>
              <button
                type="button"
                onClick={addItem}
                className="inline-flex items-center gap-1 text-sm font-medium text-indigo-600 hover:underline dark:text-indigo-400"
              >
                <Plus className="h-3.5 w-3.5" /> Add category
              </button>
            </div>
            {items.map((item, index) => (
              <div key={index} className="flex items-center gap-2">
                <select
                  value={item.category_id}
                  onChange={(e) => updateItem(index, { category_id: e.target.value })}
                  className={inputClass}
                >
                  <option value="">Select category…</option>
                  {availableFor(index).map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={item.limit_minor}
                  onChange={(e) => updateItem(index, { limit_minor: e.target.value })}
                  placeholder="Limit"
                  className={`${inputClass} w-32`}
                />
                <button
                  type="button"
                  onClick={() => removeItem(index)}
                  aria-label="Remove"
                  className="rounded-lg p-1.5 text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg px-4 py-2 text-sm font-medium text-zinc-600 hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-zinc-800"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!name.trim() || mutation.isPending}
              className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {mutation.isPending ? "Saving…" : "Create budget"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
