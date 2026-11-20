"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CalendarClock, Pause, Play, Plus } from "lucide-react";
import { useState } from "react";

import { EmptyState } from "@/components/ui/empty-state";
import {
  financeApi,
  type Bill,
  type BillOccurrence,
  type OccurrenceStatus,
} from "@/lib/api/finance";
import { formatMinor } from "@/lib/currency";

import { CreateBillDialog, RecordPaymentDialog } from "./dialogs";

const STATUS_STYLES: Record<OccurrenceStatus, string> = {
  upcoming: "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300",
  due: "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300",
  overdue: "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300",
  paid: "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300",
  skipped: "bg-zinc-100 text-zinc-400 dark:bg-zinc-800 dark:text-zinc-500",
};

function Badge({ status }: { status: OccurrenceStatus }) {
  return (
    <span
      className={`rounded-full px-2 py-0.5 text-xs font-medium capitalize ${STATUS_STYLES[status]}`}
    >
      {status}
    </span>
  );
}

function BillCard({ bill }: { bill: Bill }) {
  const queryClient = useQueryClient();
  const occurrences = useQuery({
    queryKey: ["bill-occurrences", bill.id],
    queryFn: () => financeApi.billOccurrences(bill.id),
  });
  const toggle = useMutation({
    mutationFn: () => financeApi.toggleBillPause(bill.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["bills"] }),
  });
  const skip = useMutation({
    mutationFn: (id: string) => financeApi.skipOccurrence(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["bill-occurrences", bill.id] }),
  });
  const [paying, setPaying] = useState<BillOccurrence | null>(null);

  const next = (occurrences.data ?? []).find((o) => o.status !== "paid" && o.status !== "skipped");

  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
      <div className="mb-3 flex items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold">{bill.name}</h3>
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            {formatMinor(bill.amount_minor, bill.currency_code)} · {bill.frequency.toLowerCase()}
            {bill.interval_value > 1 ? ` × ${bill.interval_value}` : ""}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => toggle.mutate()}
            aria-label={bill.status === "ACTIVE" ? "Pause" : "Resume"}
            className="rounded-lg p-1.5 text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800"
          >
            {bill.status === "ACTIVE" ? (
              <Pause className="h-4 w-4" />
            ) : (
              <Play className="h-4 w-4" />
            )}
          </button>
        </div>
      </div>

      {next && (
        <p className="mb-3 text-sm text-zinc-600 dark:text-zinc-300">
          Next due: <span className="font-medium">{next.due_date}</span>
        </p>
      )}

      {occurrences.data && occurrences.data.length > 0 && (
        <ul className="divide-y divide-zinc-100 dark:divide-zinc-800">
          {occurrences.data.slice(0, 5).map((occ) => (
            <li key={occ.id} className="flex items-center justify-between gap-3 py-2 text-sm">
              <span className="text-zinc-700 dark:text-zinc-200">{occ.due_date}</span>
              <div className="flex items-center gap-2">
                <Badge status={occ.status} />
                {occ.status !== "paid" && occ.status !== "skipped" && (
                  <>
                    <button
                      type="button"
                      onClick={() => setPaying(occ)}
                      className="rounded-lg px-2 py-1 text-xs font-medium text-indigo-600 hover:bg-indigo-50 dark:text-indigo-400 dark:hover:bg-indigo-950"
                    >
                      Record payment
                    </button>
                    <button
                      type="button"
                      onClick={() => skip.mutate(occ.id)}
                      className="rounded-lg px-2 py-1 text-xs font-medium text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-800"
                    >
                      Skip
                    </button>
                  </>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}

      <RecordPaymentDialog bill={bill} occurrence={paying!} onClose={() => setPaying(null)} />
    </div>
  );
}

export default function BillsPage() {
  const [createOpen, setCreateOpen] = useState(false);
  const bills = useQuery({ queryKey: ["bills"], queryFn: financeApi.bills });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Recurring Bills</h1>
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            Track scheduled obligations — no money is ever moved.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setCreateOpen(true)}
          className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white transition hover:bg-indigo-500"
        >
          <Plus className="h-4 w-4" /> New bill
        </button>
      </div>

      {(bills.data ?? []).length === 0 ? (
        <EmptyState
          icon={CalendarClock}
          title="No recurring bills yet"
          description="Add scheduled obligations like rent or subscriptions to track them."
        />
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          {(bills.data ?? []).map((bill) => (
            <BillCard key={bill.id} bill={bill} />
          ))}
        </div>
      )}

      <CreateBillDialog open={createOpen} onClose={() => setCreateOpen(false)} />
    </div>
  );
}
