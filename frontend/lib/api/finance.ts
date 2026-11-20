import { apiRequest } from "./client";

export type TransactionType = "INCOME" | "EXPENSE" | "TRANSFER";

export interface Category {
  id: string;
  name: string;
  type: "INCOME" | "EXPENSE";
  icon: string | null;
  color: string | null;
  is_system: boolean;
  status: string;
}

export interface LedgerEntry {
  id: string;
  account_id: string;
  amount_minor: number;
  created_at: string;
}

export interface Transaction {
  id: string;
  type: TransactionType;
  amount_minor: number;
  currency_code: string;
  category: Category | null;
  description: string;
  transaction_date: string;
  notes: string | null;
  status: "POSTED" | "VOIDED";
  idempotency_key: string | null;
  voided_at: string | null;
  created_at: string;
  updated_at: string;
  ledger_entries: LedgerEntry[];
}

export interface Account {
  id: string;
  name: string;
  account_type: string;
  currency_code: string;
  opening_balance_minor: number;
  opening_date: string;
  description: string | null;
  status: string;
  created_at: string;
}

export interface Summary {
  currency_code: string;
  total_balance_minor: number;
  income_minor: number;
  expenses_minor: number;
  net_cashflow_minor: number;
  period: { from: string | null; to: string | null };
}

export interface CashflowPoint {
  period: string;
  income_minor: number;
  expenses_minor: number;
}

export interface SpendingCategory {
  category_id: string;
  name: string;
  color: string | null;
  total_minor: number;
}

export interface AccountOverviewItem {
  id: string;
  name: string;
  account_type: string;
  currency_code: string;
  status: string;
  balance_minor: number;
}

export interface TransactionInput {
  type: TransactionType;
  amount_minor: number;
  currency_code: string;
  category_id?: string;
  account_id?: string;
  source_account_id?: string;
  destination_account_id?: string;
  description: string;
  transaction_date: string;
  notes?: string;
}

function qs(params: Record<string, string | number | undefined | null>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") {
      search.set(key, String(value));
    }
  }
  const s = search.toString();
  return s ? `?${s}` : "";
}

export const financeApi = {
  summary: (params: Record<string, string | undefined>) =>
    apiRequest<Summary>(`/api/v1/dashboard/summary${qs(params)}`),
  cashflow: (params: Record<string, string | undefined>) =>
    apiRequest<CashflowPoint[]>(`/api/v1/dashboard/cashflow${qs(params)}`),
  spending: (params: Record<string, string | undefined>) =>
    apiRequest<SpendingCategory[]>(`/api/v1/dashboard/spending${qs(params)}`),
  recentTransactions: (limit = 5) =>
    apiRequest<Transaction[]>(`/api/v1/dashboard/recent-transactions${qs({ limit })}`),
  accountOverview: () => apiRequest<AccountOverviewItem[]>("/api/v1/dashboard/account-overview"),

  accounts: () => apiRequest<Account[]>("/api/v1/accounts"),
  categories: (type?: "INCOME" | "EXPENSE") =>
    apiRequest<Category[]>(`/api/v1/categories${qs({ type })}`),
  createTransaction: (input: TransactionInput) =>
    apiRequest<Transaction>("/api/v1/transactions", {
      method: "POST",
      body: JSON.stringify(input),
    }),
};
