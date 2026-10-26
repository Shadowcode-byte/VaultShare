import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, ForeignKey, Enum, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import PermissionLevel


class FilePermission(Base):
    """
    One row = one grant of access to one file for one user.

    Revocation is modeled as a soft-delete (revoked_at timestamp) rather
    than deleting the row outright. This matters for two reasons:
      1. Accountability — we keep a record that access WAS granted and
         later removed, which the audit trail and viva both rely on.
      2. Correctness — permission_service treats any row with
         revoked_at IS NOT NULL as inactive, so a revoked user is denied
         even though history is preserved.
    """
    __tablename__ = "file_permissions"
    __table_args__ = (
        # ONE row per (file, user) — re-sharing with a different level
        # (e.g. upgrading someone from VIEW to DOWNLOAD) updates this
        # row's `permission` column rather than creating a second,
        # parallel grant. That keeps "what can this user currently do
        # with this file" a single lookup instead of a set to reconcile.
        UniqueConstraint("file_id", "user_id", name="uq_file_user"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    file_id: Mapped[str] = mapped_column(String(36), ForeignKey("files.id"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)

    permission: Mapped[PermissionLevel] = mapped_column(Enum(PermissionLevel), nullable=False)

    granted_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    file = relationship("File", back_populates="permissions", foreign_keys=[file_id])
    user = relationship("User", back_populates="permissions_granted", foreign_keys=[user_id])

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None
