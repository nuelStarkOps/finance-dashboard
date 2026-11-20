import { FeaturePreview } from "@/components/ui/feature-preview";
import { PieChart } from "lucide-react";

export default function BudgetsPage() {
  return (
    <FeaturePreview
      icon={PieChart}
      title="Budgets"
      description="Budget planning and progress tracking arrives in Phase 4."
    />
  );
}
