"""
Single write path for audit_logs. Routers call log_event() instead of
constructing AuditLog rows themselves — that way every log entry is
guaranteed to go through the same (minimal) metadata shape, and if we
ever need to change how logging works (e.g. also mirror to a file),
there's exactly one function to change.
"""
from typing import Optional

from sqlalchemy.orm import Session as OrmSession

from app.models.audit_log import AuditLog
from app.models.enums import AuditAction, AuditResult


def log_event(
    db: OrmSession,
    action: AuditAction,
    result: AuditResult,
    user_id: Optional[str] = None,
    file_id: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> None:
    entry = AuditLog(
        user_id=user_id, file_id=file_id, action=action, result=result, event_metadata=metadata,
    )
    db.add(entry)
    db.commit()
