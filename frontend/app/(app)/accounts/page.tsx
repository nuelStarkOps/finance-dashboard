import { FeaturePreview } from "@/components/ui/feature-preview";
import { Wallet } from "lucide-react";

export default function AccountsPage() {
  return (
    <FeaturePreview
      icon={Wallet}
      title="Accounts"
      description="Account management — balances, history and archiving — arrives in an upcoming phase."
    />
  );
}
