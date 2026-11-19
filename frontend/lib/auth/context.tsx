"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { apiRequest } from "@/lib/api/client";
import { authProvider } from "@/lib/auth/providers";
import { clearTokens, getAccessToken, setTokens } from "@/lib/auth/tokens";
import type {
  ForgotPasswordResult,
  LoginInput,
  Preferences,
  RegisterInput,
  ResetPasswordInput,
  User,
} from "@/lib/auth/types";

type AuthStatus = "loading" | "authenticated" | "unauthenticated";

interface AuthContextValue {
  status: AuthStatus;
  user: User | null;
  preferences: Preferences | null;
  /** Returns onboardingCompleted so callers can route after auth. */
  register: (input: RegisterInput) => Promise<boolean>;
  login: (input: LoginInput) => Promise<boolean>;
  logout: () => void;
  forgotPassword: (email: string) => Promise<ForgotPasswordResult>;
  resetPassword: (input: ResetPasswordInput) => Promise<void>;
  refreshPreferences: () => Promise<Preferences | null>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [user, setUser] = useState<User | null>(null);
  const [preferences, setPreferences] = useState<Preferences | null>(null);

  const loadSession = useCallback(async (): Promise<Preferences | null> => {
    if (!getAccessToken()) {
      return null;
    }
    try {
      const [me, prefs] = await Promise.all([
        apiRequest<User>("/api/v1/users/me"),
        apiRequest<Preferences>("/api/v1/users/me/preferences"),
      ]);
      setUser(me);
      setPreferences(prefs);
      setStatus("authenticated");
      return prefs;
    } catch {
      clearTokens();
      setUser(null);
      setPreferences(null);
      setStatus("unauthenticated");
      return null;
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      // Defer past the effect body so state updates are not synchronous.
      await Promise.resolve();
      if (cancelled) return;
      if (!getAccessToken()) {
        setUser(null);
        setPreferences(null);
        setStatus("unauthenticated");
        return;
      }
      await loadSession();
    })();
    return () => {
      cancelled = true;
    };
  }, [loadSession]);

  const register = useCallback(
    async (input: RegisterInput): Promise<boolean> => {
      const result = await authProvider.register(input);
      setTokens(result.accessToken, result.refreshToken);
      return (await loadSession())?.onboarding_completed ?? false;
    },
    [loadSession],
  );

  const login = useCallback(
    async (input: LoginInput): Promise<boolean> => {
      const result = await authProvider.login(input);
      setTokens(result.accessToken, result.refreshToken);
      return (await loadSession())?.onboarding_completed ?? false;
    },
    [loadSession],
  );

  const logout = useCallback(() => {
    clearTokens();
    setUser(null);
    setPreferences(null);
    setStatus("unauthenticated");
  }, []);

  const forgotPassword = useCallback((email: string) => authProvider.forgotPassword(email), []);

  const resetPassword = useCallback(
    (input: ResetPasswordInput) => authProvider.resetPassword(input),
    [],
  );

  const refreshPreferences = useCallback(async (): Promise<Preferences | null> => {
    try {
      const prefs = await apiRequest<Preferences>("/api/v1/users/me/preferences");
      setPreferences(prefs);
      return prefs;
    } catch {
      return null;
    }
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      status,
      user,
      preferences,
      register,
      login,
      logout,
      forgotPassword,
      resetPassword,
      refreshPreferences,
    }),
    [
      status,
      user,
      preferences,
      register,
      login,
      logout,
      forgotPassword,
      resetPassword,
      refreshPreferences,
    ],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
