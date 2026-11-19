"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import { apiRequest } from "@/lib/api/client";
import { useAuth } from "@/lib/auth/context";
import { toMinorUnits } from "@/lib/currency";
import { COUNTRIES, CURRENCIES, countryByCode } from "@/lib/location";

const inputClass =
  "w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/30 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100";

const buttonClass =
  "rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-60";

const STEPS = ["Profile", "Location", "Income", "Account", "Budget"];
const ACCOUNT_TYPES = [
  { value: "CURRENT", label: "Current / checking" },
  { value: "SAVINGS", label: "Savings" },
  { value: "CASH", label: "Cash" },
  { value: "OTHER", label: "Other" },
];

function todayString(): string {
  return new Date().toISOString().slice(0, 10);
}

export default function OnboardingPage() {
  const { refreshPreferences } = useAuth();
  const router = useRouter();

  const [step, setStep] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const [displayName, setDisplayName] = useState("");
  const [countryCode, setCountryCode] = useState("NG");
  const [currency, setCurrency] = useState("NGN");
  const [incomeFrequency, setIncomeFrequency] = useState("MONTHLY");
  const [accountName, setAccountName] = useState("");
  const [accountType, setAccountType] = useState("CURRENT");
  const [accountCurrency, setAccountCurrency] = useState("NGN");
  const [openingBalance, setOpeningBalance] = useState("");
  const [openingDate, setOpeningDate] = useState("");

  const selectedCountry = useMemo(() => countryByCode(countryCode), [countryCode]);

  function selectCountry(code: string) {
    setCountryCode(code);
    const c = countryByCode(code);
    setCurrency(c.currency);
    setAccountCurrency(c.currency);
  }

  function next() {
    setError(null);
    setStep((s) => Math.min(s + 1, STEPS.length - 1));
  }

  function back() {
    setError(null);
    setStep((s) => Math.max(s - 1, 0));
  }

  function canProceed(): boolean {
    if (step === 0) return displayName.trim().length > 0;
    if (step === 1) return currency.length === 3;
    if (step === 2) return true; // income frequency is optional
    if (step === 3) {
      return (
        accountName.trim().length > 0 &&
        Number(openingBalance) >= 0 &&
        openingBalance.trim().length > 0
      );
    }
    return true; // budget is optional (Phase 4)
  }

  async function finish() {
    setError(null);
    setLoading(true);
    try {
      await apiRequest("/api/v1/users/me/onboarding", {
        method: "POST",
        body: JSON.stringify({
          display_name: displayName.trim(),
          country_code: selectedCountry.code,
          preferred_currency: currency,
          timezone: selectedCountry.timezone,
          locale: selectedCountry.locale,
          account: {
            name: accountName.trim(),
            account_type: accountType,
            currency_code: accountCurrency,
            opening_balance_minor: toMinorUnits(Number(openingBalance) || 0),
            opening_date: openingDate || todayString(),
          },
        }),
      });
      await refreshPreferences();
      router.replace("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not complete onboarding.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Set up your account</h2>
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          Step {step + 1} of {STEPS.length} — {STEPS[step]}
        </p>
        <div className="mt-3 flex gap-1">
          {STEPS.map((label, i) => (
            <div
              key={label}
              className={`h-1 flex-1 rounded-full ${i <= step ? "bg-indigo-500" : "bg-zinc-200 dark:bg-zinc-700"}`}
            />
          ))}
        </div>
      </div>

      {error && (
        <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-950/50 dark:text-red-300">
          {error}
        </p>
      )}

      {step === 0 && (
        <div>
          <label htmlFor="display-name" className="mb-1 block text-sm font-medium">
            What should we call you?
          </label>
          <input
            id="display-name"
            type="text"
            autoFocus
            required
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            placeholder="e.g. Ada Lovelace"
            className={inputClass}
          />
        </div>
      )}

      {step === 1 && (
        <div className="space-y-4">
          <div>
            <label htmlFor="country" className="mb-1 block text-sm font-medium">
              Country
            </label>
            <select
              id="country"
              value={countryCode}
              onChange={(e) => selectCountry(e.target.value)}
              className={inputClass}
            >
              {COUNTRIES.map((c) => (
                <option key={c.code} value={c.code}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="currency" className="mb-1 block text-sm font-medium">
              Preferred currency
            </label>
            <select
              id="currency"
              value={currency}
              onChange={(e) => setCurrency(e.target.value)}
              className={inputClass}
            >
              {CURRENCIES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
            <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
              Locale {selectedCountry.locale} · {selectedCountry.timezone}
            </p>
          </div>
        </div>
      )}

      {step === 2 && (
        <div>
          <p className="mb-3 text-sm text-zinc-600 dark:text-zinc-300">
            How often do you receive income? (optional — used for cash-flow insights later)
          </p>
          <div className="space-y-2">
            {["MONTHLY", "WEEKLY", "BIWEEKLY", "YEARLY", "IRREGULAR"].map((freq) => (
              <label
                key={freq}
                className="flex cursor-pointer items-center gap-3 rounded-lg border border-zinc-200 px-3 py-2 text-sm dark:border-zinc-700"
              >
                <input
                  type="radio"
                  name="income-frequency"
                  checked={incomeFrequency === freq}
                  onChange={() => setIncomeFrequency(freq)}
                />
                <span className="capitalize">{freq.toLowerCase()}</span>
              </label>
            ))}
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="space-y-4">
          <div>
            <label htmlFor="account-name" className="mb-1 block text-sm font-medium">
              Account name
            </label>
            <input
              id="account-name"
              type="text"
              required
              value={accountName}
              onChange={(e) => setAccountName(e.target.value)}
              placeholder="e.g. Main Bank Account"
              className={inputClass}
            />
          </div>
          <div>
            <label htmlFor="account-type" className="mb-1 block text-sm font-medium">
              Account type
            </label>
            <select
              id="account-type"
              value={accountType}
              onChange={(e) => setAccountType(e.target.value)}
              className={inputClass}
            >
              {ACCOUNT_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="account-currency" className="mb-1 block text-sm font-medium">
                Currency
              </label>
              <select
                id="account-currency"
                value={accountCurrency}
                onChange={(e) => setAccountCurrency(e.target.value)}
                className={inputClass}
              >
                {CURRENCIES.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="opening-date" className="mb-1 block text-sm font-medium">
                Opening date
              </label>
              <input
                id="opening-date"
                type="date"
                value={openingDate}
                onChange={(e) => setOpeningDate(e.target.value)}
                className={inputClass}
              />
              <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
                Defaults to today if left blank.
              </p>
            </div>
          </div>
          <div>
            <label htmlFor="opening-balance" className="mb-1 block text-sm font-medium">
              Opening balance ({accountCurrency})
            </label>
            <input
              id="opening-balance"
              type="number"
              min="0"
              step="0.01"
              required
              value={openingBalance}
              onChange={(e) => setOpeningBalance(e.target.value)}
              placeholder="0.00"
              className={inputClass}
            />
          </div>
        </div>
      )}

      {step === 4 && (
        <div className="rounded-lg border border-dashed border-zinc-300 p-4 text-sm text-zinc-600 dark:border-zinc-700 dark:text-zinc-300">
          <p className="font-medium">Optional monthly budget</p>
          <p className="mt-1">
            Budgets arrive in a later phase. You can skip this and create budgets from the dashboard
            once they are available.
          </p>
        </div>
      )}

      <div className="flex items-center justify-between pt-2">
        <button
          type="button"
          onClick={back}
          disabled={step === 0}
          className="rounded-lg px-4 py-2 text-sm font-medium text-zinc-600 hover:bg-zinc-100 disabled:opacity-40 dark:text-zinc-300 dark:hover:bg-zinc-800"
        >
          Back
        </button>

        {step < STEPS.length - 1 ? (
          <button type="button" onClick={next} disabled={!canProceed()} className={buttonClass}>
            Continue
          </button>
        ) : (
          <button type="button" onClick={finish} disabled={loading} className={buttonClass}>
            {loading ? "Finishing…" : "Finish"}
          </button>
        )}
      </div>
    </div>
  );
}
