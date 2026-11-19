import {
  AuthResult,
  ForgotPasswordResult,
  LoginInput,
  RegisterInput,
  ResetPasswordInput,
  User,
} from "./types";
import { getRefreshToken, setAccessToken } from "./tokens";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface AuthProvider {
  register(input: RegisterInput): Promise<AuthResult>;
  login(input: LoginInput): Promise<AuthResult>;
  forgotPassword(email: string): Promise<ForgotPasswordResult>;
  resetPassword(input: ResetPasswordInput): Promise<void>;
  refresh(refreshToken: string): Promise<{ accessToken: string }>;
}

interface Envelope<T> {
  success: boolean;
  data?: T;
  error?: { code: string; message: string };
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const payload = (await res.json().catch(() => null)) as Envelope<T> | null;
  if (!res.ok) {
    throw new Error(payload?.error?.message ?? `Request failed (${res.status})`);
  }
  return payload?.data as T;
}

/** Local development provider (talks to the backend dev-auth endpoints). */
const devProvider: AuthProvider = {
  async register(input) {
    const data = await post<{
      access_token: string;
      refresh_token: string;
      expires_in: number;
      user: User;
    }>("/api/v1/dev-auth/register", {
      email: input.email,
      password: input.password,
      display_name: input.displayName,
    });
    return {
      accessToken: data.access_token,
      refreshToken: data.refresh_token,
      expiresIn: data.expires_in,
      user: data.user,
    };
  },

  async login(input) {
    const data = await post<{
      access_token: string;
      refresh_token: string;
      expires_in: number;
      user: User;
    }>("/api/v1/dev-auth/login", {
      email: input.email,
      password: input.password,
    });
    return {
      accessToken: data.access_token,
      refreshToken: data.refresh_token,
      expiresIn: data.expires_in,
      user: data.user,
    };
  },

  async forgotPassword(email) {
    return post<ForgotPasswordResult>("/api/v1/dev-auth/forgot-password", { email });
  },

  async resetPassword(input) {
    await post<{ message: string }>("/api/v1/dev-auth/reset-password", {
      email: input.email,
      reset_code: input.resetCode,
      new_password: input.newPassword,
    });
  },

  async refresh(refreshToken) {
    const data = await post<{ access_token: string }>("/api/v1/dev-auth/refresh", {
      refresh_token: refreshToken,
    });
    return { accessToken: data.access_token };
  },
};

/**
 * Amazon Cognito provider (production).
 *
 * When a user pool is provisioned, set NEXT_PUBLIC_AUTH_PROVIDER=cognito and
 * implement the OIDC Authorization Code + PKCE flow against the pool's
 * Hosted UI, or use `amazon-cognito-identity-js` / Amplify. The backend already
 * verifies Cognito JWTs (issuer/audience/signature via JWKS), so only this thin
 * client layer needs the exchange logic.
 */
const cognitoProvider: AuthProvider = {
  async register() {
    throw new Error(
      "Cognito is not configured yet. Set NEXT_PUBLIC_AUTH_PROVIDER=dev for local development.",
    );
  },
  async login() {
    throw new Error(
      "Cognito is not configured yet. Set NEXT_PUBLIC_AUTH_PROVIDER=dev for local development.",
    );
  },
  async forgotPassword() {
    throw new Error(
      "Cognito is not configured yet. Set NEXT_PUBLIC_AUTH_PROVIDER=dev for local development.",
    );
  },
  async resetPassword() {
    throw new Error(
      "Cognito is not configured yet. Set NEXT_PUBLIC_AUTH_PROVIDER=dev for local development.",
    );
  },
  async refresh() {
    throw new Error(
      "Cognito is not configured yet. Set NEXT_PUBLIC_AUTH_PROVIDER=dev for local development.",
    );
  },
};

export const authProvider: AuthProvider =
  process.env.NEXT_PUBLIC_AUTH_PROVIDER === "cognito" ? cognitoProvider : devProvider;

/** Attempt a refresh and persist the new access token. */
export async function refreshAccessToken(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;
  try {
    const { accessToken } = await authProvider.refresh(refreshToken);
    setAccessToken(accessToken);
    return true;
  } catch {
    return false;
  }
}
