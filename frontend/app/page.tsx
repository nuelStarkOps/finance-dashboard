"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuth } from "@/lib/auth/context";

export default function HomePage() {
  const { status } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (status === "authenticated") {
      router.replace("/dashboard");
    }
  }, [status, router]);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 p-8 text-center">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Personal Finance OS</h1>
        <p className="mt-2 max-w-md text-zinc-600 dark:text-zinc-400">
          Know your money. Understand your habits. Make better financial decisions.
        </p>
      </div>
      <div className="flex items-center gap-3">
        <Link
          href="/register"
          className="rounded-lg bg-indigo-600 px-5 py-2 text-sm font-medium text-white transition hover:bg-indigo-500"
        >
          Get started
        </Link>
        <Link
          href="/login"
          className="rounded-lg border border-zinc-300 px-5 py-2 text-sm font-medium text-zinc-700 transition hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-800"
        >
          Sign in
        </Link>
      </div>
    </main>
  );
}
