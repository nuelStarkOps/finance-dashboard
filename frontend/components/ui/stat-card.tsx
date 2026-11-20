import type { LucideIcon } from "lucide-react";

export function StatCard({
  label,
  value,
  icon: Icon,
  tone = "default",
  onClick,
}: {
  label: string;
  value: React.ReactNode;
  icon: LucideIcon;
  tone?: "default" | "positive" | "negative";
  onClick?: () => void;
}) {
  const toneClass =
    tone === "positive"
      ? "text-emerald-600 dark:text-emerald-400"
      : tone === "negative"
        ? "text-red-600 dark:text-red-400"
        : "text-zinc-900 dark:text-zinc-100";

  return (
    <button
      type="button"
      onClick={onClick}
      className="flex w-full items-start justify-between rounded-xl border border-zinc-200 bg-white p-5 text-left transition hover:border-zinc-300 dark:border-zinc-800 dark:bg-zinc-900 dark:hover:border-zinc-700"
    >
      <div>
        <p className="text-sm text-zinc-500 dark:text-zinc-400">{label}</p>
        <p className={`mt-1 text-2xl font-semibold tracking-tight ${toneClass}`}>{value}</p>
      </div>
      <Icon className="h-5 w-5 text-zinc-400 dark:text-zinc-500" />
    </button>
  );
}
