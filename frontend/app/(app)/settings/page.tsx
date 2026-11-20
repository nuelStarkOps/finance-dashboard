import { FeaturePreview } from "@/components/ui/feature-preview";
import { Settings } from "lucide-react";

export default function SettingsPage() {
  return (
    <FeaturePreview
      icon={Settings}
      title="Settings"
      description="Profile, preferences, categories and privacy controls arrive in an upcoming phase."
    />
  );
}
