export interface User {
  id: string;
  email: string;
  display_name: string;
  country_code: string;
  status: string;
  created_at: string;
}

export interface Preferences {
  preferred_currency: string;
  timezone: string;
  locale: string;
  theme: string;
  date_format: string;
  onboarding_completed: boolean;
}

export interface AuthResult {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
  user: User;
}

export interface RegisterInput {
  email: string;
  password: string;
  displayName: string;
}

export interface LoginInput {
  email: string;
  password: string;
}

export interface ForgotPasswordResult {
  resetCode: string;
  message: string;
}

export interface ResetPasswordInput {
  email: string;
  resetCode: string;
  newPassword: string;
}
