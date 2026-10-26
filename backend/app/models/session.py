import secrets
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Session(Base):
    """
    Server-side session store. The cookie sent to the browser holds only
    this row's id (a random, unguessable token) — never the user id and
    never any claim about role or permissions. That distinction matters:
    with server-side sessions, logout or an admin-triggered "revoke all
    sessions" takes effect immediately, because the server is the source
    of truth. A pure client-side JWT can't be un-issued before it expires.
    """
    __tablename__ = "sessions"

    # secrets.token_urlsafe() is Python's purpose-built CSPRNG API for
    # exactly this — a security token an attacker must not be able to
    # guess or brute-force. 32 raw bytes = 256 bits of entropy.
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: secrets.token_urlsafe(32))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)  # IPv6-safe length
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    @property
    def is_valid(self) -> bool:
        now = datetime.now(timezone.utc)
        expires = self.expires_at if self.expires_at.tzinfo else self.expires_at.replace(tzinfo=timezone.utc)
        return self.revoked_at is None and expires > now
