"""Dev auth endpoint schemas (local development only)."""

from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserOut


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: UserOut


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    success: bool
    # Returned for local development only so the flow can be completed without
    # a real email delivery service.
    reset_code: str
    message: str


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    reset_code: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
