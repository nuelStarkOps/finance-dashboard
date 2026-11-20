import { FeaturePreview } from "@/components/ui/feature-preview";
import { FileText } from "lucide-react";

export default function ReportsPage() {
  return (
    <FeaturePreview
      icon={FileText}
      title="Reports"
      description="Financial reports, trends and exports arrive in Phase 6."
    />
  );
}
