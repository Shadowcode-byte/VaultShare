import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, ForeignKey, Enum, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import AuditAction, AuditResult


class AuditLog(Base):
    """
    Append-only activity record. Rows here are never updated or deleted
    by application code (no update/delete route exists for this table) —
    that immutability is what makes it useful as evidence, e.g. for
    answering "who accessed this file and when".

    user_id is nullable because some events (e.g. a login attempt with
    an email that doesn't exist) happen before we can attach a real user.
    """
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # ondelete="SET NULL": deleting a user or file must NEVER be
    # blocked by their own audit trail, and the trail itself must
    # survive — "this file, now deleted, was downloaded 12 times
    # before that" is exactly the kind of record an audit log exists
    # to preserve. Without this, Postgres (unlike SQLite by default)
    # would reject the delete outright with a foreign-key violation.
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    file_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("files.id", ondelete="SET NULL"), nullable=True, index=True
    )

    action: Mapped[AuditAction] = mapped_column(Enum(AuditAction), nullable=False, index=True)
    result: Mapped[AuditResult] = mapped_column(Enum(AuditResult), nullable=False)

    # Deliberately minimal — e.g. {"ip": "..."} or {"reason": "wrong_password"}.
    # We do NOT log request bodies, file contents, or full headers here;
    # that would violate data minimization for no real investigative benefit.
    event_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
