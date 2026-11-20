import { FeaturePreview } from "@/components/ui/feature-preview";
import { Target } from "lucide-react";

export default function SavingsPage() {
  return (
    <FeaturePreview
      icon={Target}
      title="Savings Goals"
      description="Savings goals and contribution tracking arrive in Phase 5."
    />
  );
}
