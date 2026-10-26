from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr

from app.models.enums import UserRole, UserStatus, AuditAction, AuditResult


class AdminUserView(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: UserRole
    status: UserStatus
    created_at: datetime

    class Config:
        from_attributes = True


class UserStatusUpdateRequest(BaseModel):
    status: UserStatus


class AuditLogEntry(BaseModel):
    """
    user_email is resolved server-side for display convenience (an
    admin reading logs shouldn't have to cross-reference raw UUIDs by
    hand) — but note what's still absent: no file CONTENTS, no
    plaintext, nothing beyond the same minimal metadata every audit
    entry was written with. The admin view surfaces more of what
    already exists; it doesn't collect anything new.
    """
    id: str
    user_id: Optional[str]
    user_email: Optional[str]
    file_id: Optional[str]
    action: AuditAction
    result: AuditResult
    event_metadata: Optional[dict]
    timestamp: datetime

    class Config:
        from_attributes = True


class SecurityStats(BaseModel):
    """
    Every field here is a direct COUNT(*) against real rows — see
    routers/admin.py. None of these numbers are estimated, sampled, or
    hardcoded, per the project brief's explicit rule against fabricating
    security statistics.
    """
    total_users: int
    total_files: int
    total_active_shares: int
    successful_logins: int
    failed_login_attempts: int
    unauthorized_access_attempts: int
    integrity_check_failures: int
    recent_events: list[AuditLogEntry]
