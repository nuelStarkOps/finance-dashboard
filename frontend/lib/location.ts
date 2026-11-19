/** Location/currency options for onboarding and settings. */

export interface CountryOption {
  code: string;
  name: string;
  currency: string;
  locale: string;
  timezone: string;
}

export const COUNTRIES: CountryOption[] = [
  { code: "NG", name: "Nigeria", currency: "NGN", locale: "en-NG", timezone: "Africa/Lagos" },
  { code: "GH", name: "Ghana", currency: "GHS", locale: "en-GH", timezone: "Africa/Accra" },
  { code: "KE", name: "Kenya", currency: "KES", locale: "en-KE", timezone: "Africa/Nairobi" },
  {
    code: "ZA",
    name: "South Africa",
    currency: "ZAR",
    locale: "en-ZA",
    timezone: "Africa/Johannesburg",
  },
  {
    code: "US",
    name: "United States",
    currency: "USD",
    locale: "en-US",
    timezone: "America/New_York",
  },
  {
    code: "GB",
    name: "United Kingdom",
    currency: "GBP",
    locale: "en-GB",
    timezone: "Europe/London",
  },
];

export const CURRENCIES = ["NGN", "USD", "GBP", "EUR", "GHS", "KES", "ZAR"];

export function countryByCode(code: string): CountryOption {
  return COUNTRIES.find((c) => c.code === code) ?? COUNTRIES[0];
}
