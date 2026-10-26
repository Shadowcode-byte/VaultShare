"""
Where "is this user allowed to do THIS to THIS file" gets decided.
Kept entirely separate from get_current_user (Phase 3) on purpose —
that function only answers "who is this?", never "what can they touch?".
Conflating the two is exactly the mistake the project brief calls out:
checking auth but not authz.

Access-control model (mirrors the project brief's Section 11):

    OWNER         -> full control: view, download, share, revoke, delete
    SHARED USER    -> whatever level they were granted: VIEW or DOWNLOAD
    ANYONE ELSE    -> denied

DOWNLOAD is treated as a superset of VIEW: anyone who can download can
also view, but not the reverse. That hierarchy lives in has_access()
below and nowhere else — every route asks this module, never compares
permission strings itself.
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session as OrmSession

from app.models.file import File
from app.models.permission import FilePermission
from app.models.user import User
from app.models.enums import PermissionLevel


def get_active_permission(db: OrmSession, file_id: str, user_id: str) -> Optional[FilePermission]:
    return (
        db.query(FilePermission)
        .filter(
            FilePermission.file_id == file_id,
            FilePermission.user_id == user_id,
            FilePermission.revoked_at.is_(None),
        )
        .first()
    )


def has_access(db: OrmSession, file: File, user: User, required: PermissionLevel) -> bool:
    if file.owner_id == user.id:
        return True

    grant = get_active_permission(db, file.id, user.id)
    if grant is None:
        return False

    if required == PermissionLevel.VIEW:
        return True  # any active grant, VIEW or DOWNLOAD, satisfies a VIEW requirement
    if required == PermissionLevel.DOWNLOAD:
        return grant.permission == PermissionLevel.DOWNLOAD
    return False


def grant_permission(
    db: OrmSession, file: File, grantee: User, level: PermissionLevel, granted_by: User
) -> FilePermission:
    """
    Re-sharing the same file with the same person UPDATES their existing
    row in place (including un-revoking them if they'd been revoked)
    rather than inserting a second row — see the schema comment in
    models/permission.py for why the unique constraint enforces this.
    """
    existing = (
        db.query(FilePermission)
        .filter(FilePermission.file_id == file.id, FilePermission.user_id == grantee.id)
        .first()
    )
    if existing:
        existing.permission = level
        existing.revoked_at = None
        existing.granted_by = granted_by.id
        existing.granted_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(existing)
        return existing

    new_grant = FilePermission(
        file_id=file.id, user_id=grantee.id, permission=level, granted_by=granted_by.id,
    )
    db.add(new_grant)
    db.commit()
    db.refresh(new_grant)
    return new_grant


def revoke_permission(db: OrmSession, file: File, user_id: str) -> bool:
    """Returns False if there was no active grant to revoke (caller
    turns that into a 404), True if revocation succeeded."""
    grant = get_active_permission(db, file.id, user_id)
    if grant is None:
        return False
    grant.revoked_at = datetime.now(timezone.utc)
    db.commit()
    return True


def list_active_shares(db: OrmSession, file_id: str) -> list[FilePermission]:
    return (
        db.query(FilePermission)
        .filter(FilePermission.file_id == file_id, FilePermission.revoked_at.is_(None))
        .all()
    )


def list_files_shared_with(db: OrmSession, user_id: str) -> list[File]:
    return (
        db.query(File)
        .join(FilePermission, FilePermission.file_id == File.id)
        .filter(FilePermission.user_id == user_id, FilePermission.revoked_at.is_(None))
        .order_by(File.created_at.desc())
        .all()
    )
