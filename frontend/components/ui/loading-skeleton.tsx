export function LoadingSkeleton({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse rounded-xl bg-zinc-200 dark:bg-zinc-800 ${className}`} />;
}

export function SkeletonCard({ className = "" }: { className?: string }) {
  return <LoadingSkeleton className={`h-28 ${className}`} />;
}
