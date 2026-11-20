import { FeaturePreview } from "@/components/ui/feature-preview";
import { TrendingUp } from "lucide-react";

export default function TransactionsPage() {
  return (
    <FeaturePreview
      icon={TrendingUp}
      title="Transactions"
      description="Full transaction management — search, filters and bulk actions — arrives in an upcoming phase. For now, use “Add transaction” in the header."
    />
  );
}
