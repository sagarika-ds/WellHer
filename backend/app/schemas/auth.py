import uuid
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.schemas.common import ORMModel

Purpose = Literal["health_tracking", "ml_processing", "llm_external", "analytics"]


class ConsentChoice(BaseModel):
    purpose: Purpose
    granted: bool


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    display_name: str = Field(min_length=1, max_length=100)
    consents: list[ConsentChoice] = Field(default_factory=list, max_length=4)

    @field_validator("display_name")
    @classmethod
    def _strip(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("must not be blank")
        return v

    @model_validator(mode="after")
    def _password_quality(self) -> "RegisterRequest":
        local = str(self.email).split("@")[0].lower()
        if len(local) >= 4 and local in self.password.lower():
            raise ValueError("password must not contain your email name")
        if len(set(self.password)) < 5:
            raise ValueError("password is too repetitive")
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)
    device: str | None = Field(default=None, max_length=100)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=20, max_length=200)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=20, max_length=200)
    new_password: str = Field(min_length=12, max_length=128)


class UserOut(ORMModel):
    id: uuid.UUID
    email: EmailStr
    display_name: str
    role: str
