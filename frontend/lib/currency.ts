/**
 * Money formatting helpers.
 *
 * Phase 1 assumes 2-decimal minor units for the supported currencies. Phase 2
 * will read each currency's precision from ISO 4217 (the spec forbids assuming
 * two decimals for every currency).
 */

export function toMinorUnits(amount: number): number {
  return Math.round(amount * 100);
}

export function minorToMajor(minor: number): number {
  return minor / 100;
}

export function formatMinor(minor: number, currency: string): string {
  try {
    return new Intl.NumberFormat(undefined, {
      style: "currency",
      currency,
    }).format(minor / 100);
  } catch {
    return `${currency} ${minor / 100}`;
  }
}
