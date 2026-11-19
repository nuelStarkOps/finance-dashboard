"use client";

import Link from "next/link";
import { useState } from "react";

import { useAuth } from "@/lib/auth/context";

const inputClass =
  "w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/30 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100";

const buttonClass =
  "w-full rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-60";

export default function ForgotPasswordPage() {
  const { forgotPassword, resetPassword } = useAuth();
  const [email, setEmail] = useState("");
  const [resetCode, setResetCode] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [step, setStep] = useState<"request" | "reset">("request");
  const [loading, setLoading] = useState(false);

  async function handleRequest(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setMessage(null);
    setLoading(true);
    try {
      const result = await forgotPassword(email);
      setMessage(
        result.resetCode
          ? `Reset code: ${result.resetCode} (shown because no email service is configured in dev).`
          : result.message,
      );
      setStep("reset");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed.");
    } finally {
      setLoading(false);
    }
  }

  async function handleReset(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await resetPassword({ email, resetCode, newPassword });
      setMessage("Password reset. You can now sign in.");
      setStep("request");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Reset failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">Reset your password</h2>

      {error && (
        <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-950/50 dark:text-red-300">
          {error}
        </p>
      )}
      {message && (
        <p className="rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300">
          {message}
        </p>
      )}

      {step === "request" ? (
        <form onSubmit={handleRequest} className="space-y-4">
          <div>
            <label htmlFor="email" className="mb-1 block text-sm font-medium">
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={inputClass}
            />
          </div>
          <button type="submit" disabled={loading} className={buttonClass}>
            {loading ? "Sending…" : "Send reset code"}
          </button>
        </form>
      ) : (
        <form onSubmit={handleReset} className="space-y-4">
          <div>
            <label htmlFor="code" className="mb-1 block text-sm font-medium">
              Reset code
            </label>
            <input
              id="code"
              required
              value={resetCode}
              onChange={(e) => setResetCode(e.target.value)}
              className={inputClass}
            />
          </div>
          <div>
            <label htmlFor="new-password" className="mb-1 block text-sm font-medium">
              New password
            </label>
            <input
              id="new-password"
              type="password"
              required
              minLength={8}
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className={inputClass}
            />
          </div>
          <button type="submit" disabled={loading} className={buttonClass}>
            {loading ? "Resetting…" : "Reset password"}
          </button>
        </form>
      )}

      <p className="text-center text-sm text-zinc-500 dark:text-zinc-400">
        <Link href="/login" className="text-indigo-600 hover:underline dark:text-indigo-400">
          Back to sign in
        </Link>
      </p>
    </div>
  );
}
