"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuth } from "@/lib/auth/context";

export default function RequireAuth({ children }: { children: React.ReactNode }) {
  const { status, preferences } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (status === "unauthenticated") {
      router.replace("/login");
    } else if (
      status === "authenticated" &&
      preferences &&
      !preferences.onboarding_completed &&
      pathname !== "/onboarding"
    ) {
      router.replace("/onboarding");
    }
  }, [status, preferences, router, pathname]);

  if (status === "loading" || status === "unauthenticated") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-50 text-sm text-zinc-500 dark:bg-zinc-950">
        Loading…
      </div>
    );
  }

  if (status === "authenticated" && preferences && !preferences.onboarding_completed) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-50 text-sm text-zinc-500 dark:bg-zinc-950">
        Loading…
      </div>
    );
  }

  return <>{children}</>;
}
