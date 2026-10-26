from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session as OrmSession

from app.db.session import get_db
from app.middleware.auth import require_admin
from app.models.user import User
from app.models.file import File
from app.models.permission import FilePermission
from app.models.audit_log import AuditLog
from app.models.enums import AuditAction, AuditResult
from app.schemas.admin import AdminUserView, UserStatusUpdateRequest, AuditLogEntry, SecurityStats
from app.services import audit_service

router = APIRouter(prefix="/admin", tags=["admin"])

MAX_PAGE_SIZE = 200


def _enrich_audit_entries(db: OrmSession, entries: list[AuditLog]) -> list[AuditLogEntry]:
    user_ids = {e.user_id for e in entries if e.user_id}
    emails_by_id = {}
    if user_ids:
        for u in db.query(User).filter(User.id.in_(user_ids)).all():
            emails_by_id[u.id] = u.email

    return [
        AuditLogEntry(
            id=e.id, user_id=e.user_id, user_email=emails_by_id.get(e.user_id),
            file_id=e.file_id, action=e.action, result=e.result,
            event_metadata=e.event_metadata, timestamp=e.timestamp,
        )
        for e in entries
    ]


@router.get("/users", response_model=list[AdminUserView])
def list_users(db: OrmSession = Depends(get_db), admin: User = Depends(require_admin)):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.patch("/users/{user_id}/status", response_model=AdminUserView)
def update_user_status(
    user_id: str, payload: UserStatusUpdateRequest,
    db: OrmSession = Depends(get_db), admin: User = Depends(require_admin),
):
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if target.id == admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot change your own account status.")

    old_status = target.status
    target.status = payload.status
    db.commit()
    db.refresh(target)

    audit_service.log_event(
        db, AuditAction.ACCOUNT_STATUS_CHANGED, AuditResult.SUCCESS, user_id=admin.id,
        metadata={"target_user": target.id, "old_status": old_status.value, "new_status": target.status.value},
    )
    return target


@router.get("/audit-logs", response_model=list[AuditLogEntry])
def list_audit_logs(
    db: OrmSession = Depends(get_db), admin: User = Depends(require_admin),
    action: Optional[AuditAction] = None,
    result: Optional[AuditResult] = None,
    user_id: Optional[str] = None,
    file_id: Optional[str] = None,
    limit: int = Query(default=50, le=MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
):
    query = db.query(AuditLog)
    if action is not None:
        query = query.filter(AuditLog.action == action)
    if result is not None:
        query = query.filter(AuditLog.result == result)
    if user_id is not None:
        query = query.filter(AuditLog.user_id == user_id)
    if file_id is not None:
        query = query.filter(AuditLog.file_id == file_id)

    entries = query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit).all()
    return _enrich_audit_entries(db, entries)


@router.get("/stats", response_model=SecurityStats)
def security_stats(db: OrmSession = Depends(get_db), admin: User = Depends(require_admin)):
    recent = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(10).all()

    return SecurityStats(
        total_users=db.query(User).count(),
        total_files=db.query(File).count(),
        total_active_shares=db.query(FilePermission).filter(FilePermission.revoked_at.is_(None)).count(),
        successful_logins=db.query(AuditLog).filter(
            AuditLog.action == AuditAction.USER_LOGIN, AuditLog.result == AuditResult.SUCCESS
        ).count(),
        failed_login_attempts=db.query(AuditLog).filter(
            AuditLog.action == AuditAction.USER_LOGIN_FAILED
        ).count(),
        unauthorized_access_attempts=db.query(AuditLog).filter(
            AuditLog.action == AuditAction.UNAUTHORIZED_ACCESS_ATTEMPT
        ).count(),
        integrity_check_failures=db.query(AuditLog).filter(
            AuditLog.action == AuditAction.INTEGRITY_CHECK_FAILED
        ).count(),
        recent_events=_enrich_audit_entries(db, recent),
    )
