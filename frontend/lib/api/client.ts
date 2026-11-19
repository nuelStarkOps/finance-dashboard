import { getAccessToken, clearTokens } from "@/lib/auth/tokens";
import { refreshAccessToken } from "@/lib/auth/providers";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export class UnauthorizedError extends ApiError {}

interface Envelope<T> {
  success: boolean;
  data?: T;
  error?: { code: string; message: string; details?: unknown };
}

async function rawFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const token = getAccessToken();
  const headers = new Headers(init.headers);
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  return fetch(`${API_URL}${path}`, { ...init, headers });
}

/**
 * Perform an API request against the FastAPI backend.
 *
 * - Attaches the Bearer token.
 * - On a 401, attempts a single token refresh and retries once.
 * - Unwraps the `{ success, data, error }` envelope.
 */
export async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response = await rawFetch(path, init);

  if (response.status === 401) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      response = await rawFetch(path, init);
    } else {
      clearTokens();
      throw new UnauthorizedError("Your session has expired.", 401, "UNAUTHENTICATED");
    }
  }

  const body = (await response.json().catch(() => null)) as Envelope<T> | null;

  if (!response.ok) {
    throw new ApiError(
      body?.error?.message ?? `Request failed (${response.status})`,
      response.status,
      body?.error?.code,
    );
  }

  return body?.data as T;
}
