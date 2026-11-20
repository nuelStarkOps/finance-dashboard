"use client";

import { LogOut, Menu, Plus, X } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { NavLinks } from "@/components/layout/nav-links";
import { NotificationsBell } from "@/components/notifications-bell";
import { AddTransactionDialog } from "@/features/transactions/add-transaction-dialog";
import { useAuth } from "@/lib/auth/context";

function Brand() {
  return (
    <div className="flex h-16 items-center border-b border-zinc-200 px-6 dark:border-zinc-800">
      <span className="text-sm font-semibold tracking-tight">Personal Finance OS</span>
    </div>
  );
}

export default function AppShell({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [addOpen, setAddOpen] = useState(false);

  function handleLogout() {
    logout();
    router.replace("/login");
  }

  return (
    <div className="flex min-h-screen bg-zinc-50 dark:bg-zinc-950">
      {/* Desktop sidebar */}
      <aside className="hidden w-64 shrink-0 flex-col border-r border-zinc-200 bg-white lg:flex dark:border-zinc-800 dark:bg-zinc-900">
        <Brand />
        <NavLinks />
      </aside>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-black/40" onClick={() => setMobileOpen(false)} />
          <div className="absolute left-0 top-0 flex h-full w-64 flex-col bg-white shadow-xl dark:bg-zinc-900">
            <div className="flex h-16 items-center justify-between border-b border-zinc-200 px-6 dark:border-zinc-800">
              <span className="text-sm font-semibold">Personal Finance OS</span>
              <button
                type="button"
                onClick={() => setMobileOpen(false)}
                aria-label="Close menu"
                className="rounded-lg p-1 text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-800"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <NavLinks onNavigate={() => setMobileOpen(false)} />
          </div>
        </div>
      )}

      {/* Main column */}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 items-center justify-between gap-3 border-b border-zinc-200 bg-white px-4 sm:px-6 dark:border-zinc-800 dark:bg-zinc-900">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setMobileOpen(true)}
              aria-label="Open menu"
              className="rounded-lg p-1.5 text-zinc-500 hover:bg-zinc-100 lg:hidden dark:hover:bg-zinc-800"
            >
              <Menu className="h-5 w-5" />
            </button>
            <span className="text-sm font-semibold lg:hidden">PFOS</span>
          </div>

          <div className="ml-auto flex items-center gap-2">
            <NotificationsBell />
            <button
              type="button"
              onClick={() => setAddOpen(true)}
              className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white transition hover:bg-indigo-500"
            >
              <Plus className="h-4 w-4" />
              <span className="hidden sm:inline">Add transaction</span>
              <span className="sm:hidden">Add</span>
            </button>
            <span className="hidden text-sm text-zinc-600 md:block dark:text-zinc-300">
              {user?.display_name ?? user?.email}
            </span>
            <button
              type="button"
              onClick={handleLogout}
              aria-label="Log out"
              className="rounded-lg p-2 text-zinc-500 transition hover:bg-zinc-100 hover:text-zinc-900 dark:hover:bg-zinc-800 dark:hover:text-zinc-100"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </header>

        <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 sm:px-6 lg:px-8">
          {children}
        </main>
      </div>

      <AddTransactionDialog open={addOpen} onClose={() => setAddOpen(false)} />
    </div>
  );
}
