import { formatMinor } from "@/lib/currency";

export function CurrencyDisplay({
  minor,
  currency,
  className,
}: {
  minor: number;
  currency: string;
  className?: string;
}) {
  return <span className={className}>{formatMinor(minor, currency)}</span>;
}
