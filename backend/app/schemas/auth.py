from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator

from app.models.enums import UserRole


class RegisterRequest(BaseModel):
    """
    Deliberately has NO `role` field. If it did, a client could send
    {"role": "admin"} on the public registration endpoint and grant
    itself admin — a classic mass-assignment privilege escalation bug.
    Role is always assigned server-side (see auth router) and can only
    be changed later by an existing admin through a separate,
    authorization-checked route.
    """
    name: str
    email: EmailStr
    password: str

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Name must be at least 2 characters")
        return v

    @field_validator("password")
    @classmethod
    def password_policy(cls, v: str) -> str:
        # NIST SP 800-63B recommends prioritizing minimum LENGTH over
        # forced composition rules (mandatory symbols/digits push users
        # toward predictable patterns like "Password1!"). We enforce a
        # length floor and a tiny blocklist instead of composition rules.
        if len(v) < 10:
            raise ValueError("Password must be at least 10 characters")
        common = {"password123", "12345678910", "qwertyuiop", "letmein123"}
        if v.lower() in common:
            raise ValueError("This password is too common — choose another")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserPublic(BaseModel):
    """Response shape for a user — notably excludes password_hash."""
    id: str
    name: str
    email: EmailStr
    role: UserRole
    created_at: datetime

    class Config:
        from_attributes = True
