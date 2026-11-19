"use client";

import { useAuth } from "@/lib/auth/context";
import { formatMinor } from "@/lib/currency";

export default function DashboardPage() {
  const { user, preferences } = useAuth();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">
          Welcome{user ? `, ${user.display_name}` : ""}
        </h1>
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          Your financial overview arrives in Phase 3. Authentication and onboarding are working.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
          <p className="text-sm text-zinc-500 dark:text-zinc-400">Preferred currency</p>
          <p className="mt-1 text-lg font-semibold">{preferences?.preferred_currency ?? "—"}</p>
        </div>
        <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
          <p className="text-sm text-zinc-500 dark:text-zinc-400">Timezone</p>
          <p className="mt-1 text-lg font-semibold">{preferences?.timezone ?? "—"}</p>
        </div>
      </div>

      <p className="text-xs text-zinc-400 dark:text-zinc-500">
        Example balance formatting:{" "}
        {formatMinor(15000000, preferences?.preferred_currency ?? "NGN")}
      </p>
    </div>
  );
}
