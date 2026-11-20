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

export interface BudgetItem {
  id: string;
  category_id: string;
  limit_minor: number;
  category: Category;
}

export interface Budget {
  id: string;
  name: string;
  currency_code: string;
  start_date: string;
  end_date: string;
  total_limit_minor: number | null;
  status: string;
  created_at: string;
  updated_at: string;
  items: BudgetItem[];
}

export type BudgetStatus = "ok" | "warning" | "over";

export interface BudgetItemPerformance {
  category_id: string;
  name: string;
  color: string | null;
  limit_minor: number;
  spent_minor: number;
  remaining_minor: number;
  usage_percent: number | null;
  status: BudgetStatus;
}

export interface BudgetPerformance {
  budget_id: string;
  name: string;
  currency_code: string;
  start_date: string;
  end_date: string;
  total_limit_minor: number | null;
  total_spent_minor: number;
  total_remaining_minor: number | null;
  total_usage_percent: number | null;
  status: BudgetStatus;
  items: BudgetItemPerformance[];
}

export interface BudgetOverviewItem {
  budget_id: string;
  name: string;
  currency_code: string;
  limit_minor: number;
  spent_minor: number;
  usage_percent: number | null;
  status: BudgetStatus;
}

export interface BudgetInput {
  name: string;
  currency_code: string;
  start_date: string;
  end_date: string;
  total_limit_minor?: number | null;
  items?: { category_id: string; limit_minor: number }[];
}

export interface SavingsGoal {
  id: string;
  name: string;
  currency_code: string;
  target_minor: number;
  target_date: string | null;
  priority: string;
  status: string;
  created_at: string;
  updated_at: string;
  allocated_minor: number;
  progress_percent: number;
}

export interface GoalContribution {
  id: string;
  amount_minor: number;
  contribution_type: "CONTRIBUTION" | "WITHDRAWAL" | "ADJUSTMENT";
  contribution_date: string;
  notes: string | null;
  created_at: string;
}

export interface Bill {
  id: string;
  name: string;
  amount_minor: number;
  currency_code: string;
  category: Category | null;
  frequency: string;
  interval_value: number;
  next_due_date: string;
  reminder_days: number;
  status: string;
  created_at: string;
  updated_at: string;
}

export type OccurrenceStatus = "upcoming" | "due" | "overdue" | "paid" | "skipped";

export interface BillOccurrence {
  id: string;
  due_date: string;
  amount_minor: number;
  status: OccurrenceStatus;
  paid_at: string | null;
  settled_transaction_id: string | null;
}

export interface AppNotification {
  id: string;
  type: string;
  title: string;
  message: string;
  read_at: string | null;
  created_at: string;
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
  budgetOverview: () => apiRequest<BudgetOverviewItem[]>("/api/v1/dashboard/budget-overview"),

  budgets: () => apiRequest<Budget[]>("/api/v1/budgets"),
  createBudget: (input: BudgetInput) =>
    apiRequest<Budget>("/api/v1/budgets", {
      method: "POST",
      body: JSON.stringify(input),
    }),
  archiveBudget: (id: string) => apiRequest<Budget>(`/api/v1/budgets/${id}`, { method: "DELETE" }),
  budgetPerformance: (id: string) =>
    apiRequest<BudgetPerformance>(`/api/v1/budgets/${id}/performance`),

  savingsGoals: () => apiRequest<SavingsGoal[]>("/api/v1/savings/goals"),
  createSavingsGoal: (input: {
    name: string;
    currency_code: string;
    target_minor: number;
    target_date?: string | null;
    priority?: string;
  }) =>
    apiRequest<SavingsGoal>("/api/v1/savings/goals", {
      method: "POST",
      body: JSON.stringify(input),
    }),
  addGoalContribution: (
    goalId: string,
    input: {
      amount_minor: number;
      contribution_type: string;
      contribution_date: string;
      notes?: string;
    },
  ) =>
    apiRequest<GoalContribution>(`/api/v1/savings/goals/${goalId}/contributions`, {
      method: "POST",
      body: JSON.stringify(input),
    }),

  bills: () => apiRequest<Bill[]>("/api/v1/bills"),
  createBill: (input: {
    name: string;
    amount_minor: number;
    currency_code: string;
    category_id?: string | null;
    frequency: string;
    interval_value: number;
    next_due_date: string;
    reminder_days?: number;
  }) => apiRequest<Bill>("/api/v1/bills", { method: "POST", body: JSON.stringify(input) }),
  toggleBillPause: (id: string) =>
    apiRequest<Bill>(`/api/v1/bills/${id}/pause`, { method: "POST" }),
  billOccurrences: (id: string) => apiRequest<BillOccurrence[]>(`/api/v1/bills/${id}/occurrences`),
  markOccurrencePaid: (id: string, transactionId: string) =>
    apiRequest<BillOccurrence>(`/api/v1/bill-occurrences/${id}/mark-paid`, {
      method: "POST",
      body: JSON.stringify({ transaction_id: transactionId }),
    }),
  skipOccurrence: (id: string) =>
    apiRequest<BillOccurrence>(`/api/v1/bill-occurrences/${id}/skip`, { method: "POST" }),

  notifications: () => apiRequest<AppNotification[]>("/api/v1/notifications"),
  unreadCount: () => apiRequest<{ count: number }>("/api/v1/notifications/unread-count"),
  markNotificationRead: (id: string) =>
    apiRequest<AppNotification>(`/api/v1/notifications/${id}/read`, { method: "POST" }),
  markAllNotificationsRead: () =>
    apiRequest<{ message: string }>("/api/v1/notifications/read-all", { method: "POST" }),

  accounts: () => apiRequest<Account[]>("/api/v1/accounts"),
  categories: (type?: "INCOME" | "EXPENSE") =>
    apiRequest<Category[]>(`/api/v1/categories${qs({ type })}`),
  createTransaction: (input: TransactionInput) =>
    apiRequest<Transaction>("/api/v1/transactions", {
      method: "POST",
      body: JSON.stringify(input),
    }),
};
