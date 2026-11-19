/**
 * Token storage (localStorage).
 *
 * NOTE: for a production SPA, an httpOnly cookie managed by a BFF (or Cognito's
 * hosted UI session) is more secure than localStorage. The spec's production
 * path delegates session handling to Cognito; this localStorage approach is the
 * local-development client.
 */

const ACCESS_KEY = "pfos.access_token";
const REFRESH_KEY = "pfos.refresh_token";

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(ACCESS_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(REFRESH_KEY);
}

export function setAccessToken(token: string): void {
  window.localStorage.setItem(ACCESS_KEY, token);
}

export function setTokens(accessToken: string, refreshToken: string): void {
  window.localStorage.setItem(ACCESS_KEY, accessToken);
  window.localStorage.setItem(REFRESH_KEY, refreshToken);
}

export function clearTokens(): void {
  window.localStorage.removeItem(ACCESS_KEY);
  window.localStorage.removeItem(REFRESH_KEY);
}
