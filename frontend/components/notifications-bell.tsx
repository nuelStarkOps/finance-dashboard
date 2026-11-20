"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell } from "lucide-react";
import { useState } from "react";

import { financeApi } from "@/lib/api/finance";

export function NotificationsBell() {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);

  const unread = useQuery({
    queryKey: ["notifications", "unread"],
    queryFn: financeApi.unreadCount,
  });
  const notifications = useQuery({
    queryKey: ["notifications"],
    queryFn: financeApi.notifications,
    enabled: open,
  });
  const markAll = useMutation({
    mutationFn: financeApi.markAllNotificationsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      queryClient.invalidateQueries({ queryKey: ["notifications", "unread"] });
    },
  });

  const count = unread.data?.count ?? 0;

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-label="Notifications"
        className="relative rounded-lg p-2 text-zinc-500 transition hover:bg-zinc-100 hover:text-zinc-900 dark:hover:bg-zinc-800 dark:hover:text-zinc-100"
      >
        <Bell className="h-4 w-4" />
        {count > 0 && (
          <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-semibold text-white">
            {count}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-full z-50 mt-2 w-80 rounded-xl border border-zinc-200 bg-white p-2 shadow-lg dark:border-zinc-800 dark:bg-zinc-900">
          <div className="flex items-center justify-between px-2 py-1.5">
            <span className="text-sm font-semibold">Notifications</span>
            {count > 0 && (
              <button
                type="button"
                onClick={() => markAll.mutate()}
                className="text-xs font-medium text-indigo-600 hover:underline dark:text-indigo-400"
              >
                Mark all read
              </button>
            )}
          </div>
          <ul className="max-h-80 overflow-y-auto">
            {(notifications.data ?? []).length === 0 ? (
              <li className="px-2 py-4 text-center text-sm text-zinc-500 dark:text-zinc-400">
                No notifications.
              </li>
            ) : (
              (notifications.data ?? []).map((n) => (
                <li
                  key={n.id}
                  className={`rounded-lg px-2 py-2.5 ${n.read_at ? "" : "bg-indigo-50/60 dark:bg-indigo-950/40"}`}
                >
                  <p className="text-sm font-medium">{n.title}</p>
                  <p className="text-xs text-zinc-500 dark:text-zinc-400">{n.message}</p>
                </li>
              ))
            )}
          </ul>
        </div>
      )}
    </div>
  );
}
