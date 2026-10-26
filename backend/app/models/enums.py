"""
Enums are used instead of free-text strings for role, permission level,
and account status. This isn't just style — it's a security control:
it makes privilege values a closed set validated at the DB and
application layer, so a bug or bad input can't silently create a role
like 'admin ' (trailing space) or 'Admin' that string-comparison checks
miss.
"""
import enum


class UserRole(str, enum.Enum):
    STUDENT = "student"
    ADMIN = "admin"


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    DISABLED = "disabled"


class PermissionLevel(str, enum.Enum):
    VIEW = "view"          # can see metadata + preview, not download
    DOWNLOAD = "download"  # can view and download the decrypted file


class AuditAction(str, enum.Enum):
    USER_REGISTERED = "USER_REGISTERED"
    USER_LOGIN = "USER_LOGIN"
    USER_LOGIN_FAILED = "USER_LOGIN_FAILED"
    USER_LOGOUT = "USER_LOGOUT"
    FILE_UPLOADED = "FILE_UPLOADED"
    FILE_ACCESSED = "FILE_ACCESSED"
    FILE_DOWNLOADED = "FILE_DOWNLOADED"
    FILE_SHARED = "FILE_SHARED"
    FILE_ACCESS_REVOKED = "FILE_ACCESS_REVOKED"
    FILE_DELETED = "FILE_DELETED"
    UNAUTHORIZED_ACCESS_ATTEMPT = "UNAUTHORIZED_ACCESS_ATTEMPT"
    INTEGRITY_CHECK_FAILED = "INTEGRITY_CHECK_FAILED"
    ACCOUNT_STATUS_CHANGED = "ACCOUNT_STATUS_CHANGED"


class AuditResult(str, enum.Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    DENIED = "denied"
