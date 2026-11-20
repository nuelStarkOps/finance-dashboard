import type { LucideIcon } from "lucide-react";
import { Construction } from "lucide-react";

export function FeaturePreview({
  title,
  description,
  icon: Icon = Construction,
}: {
  title: string;
  description: string;
  icon?: LucideIcon;
}) {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center rounded-xl border border-dashed border-zinc-300 bg-white px-6 py-16 text-center dark:border-zinc-700 dark:bg-zinc-900/50">
      <Icon className="h-10 w-10 text-zinc-300 dark:text-zinc-600" />
      <h1 className="mt-4 text-xl font-semibold tracking-tight">{title}</h1>
      <p className="mt-2 max-w-md text-sm text-zinc-500 dark:text-zinc-400">{description}</p>
    </div>
  );
}
