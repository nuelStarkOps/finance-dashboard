"use client";

import { useRouter } from "next/navigation";

import { useAuth } from "@/lib/auth/context";

/**
 * Minimal application shell for Phase 1. The full persistent sidebar + header
 * (per the product spec) arrives in Phase 3.
 */
export default function AppShell({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const router = useRouter();

  function handleLogout() {
    logout();
    router.replace("/login");
  }

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950">
      <header className="flex items-center justify-between border-b border-zinc-200 bg-white px-6 py-3 dark:border-zinc-800 dark:bg-zinc-900">
        <span className="text-sm font-semibold">Personal Finance OS</span>
        <div className="flex items-center gap-4">
          <span className="text-sm text-zinc-600 dark:text-zinc-300">
            {user?.display_name ?? user?.email}
          </span>
          <button
            type="button"
            onClick={handleLogout}
            className="text-sm text-zinc-500 transition hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100"
          >
            Log out
          </button>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-6 py-8">{children}</main>
    </div>
  );
}
