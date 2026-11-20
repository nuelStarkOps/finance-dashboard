import { FeaturePreview } from "@/components/ui/feature-preview";
import { CalendarClock } from "lucide-react";

export default function BillsPage() {
  return (
    <FeaturePreview
      icon={CalendarClock}
      title="Recurring Bills"
      description="Recurring bills and due-date reminders arrive in Phase 5."
    />
  );
}
