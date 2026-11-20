import type { LucideIcon } from "lucide-react";
import {
  CalendarClock,
  FileText,
  LayoutDashboard,
  PieChart,
  Settings,
  Target,
  TrendingUp,
  Wallet,
} from "lucide-react";

export interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
}

export const NAV_ITEMS: NavItem[] = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/transactions", label: "Transactions", icon: TrendingUp },
  { href: "/accounts", label: "Accounts", icon: Wallet },
  { href: "/budgets", label: "Budgets", icon: PieChart },
  { href: "/savings", label: "Savings Goals", icon: Target },
  { href: "/bills", label: "Recurring Bills", icon: CalendarClock },
  { href: "/reports", label: "Reports", icon: FileText },
  { href: "/settings", label: "Settings", icon: Settings },
];
