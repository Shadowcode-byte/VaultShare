import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import UserRole, UserStatus


class User(Base):
    __tablename__ = "users"

    # UUID primary keys instead of auto-increment integers: sequential
    # integer IDs let an attacker enumerate /files/1, /files/2, ... even
    # though the permission check would still deny them. This isn't the
    # security control (authz is) but it removes a cheap reconnaissance
    # tool and is worth a sentence in the threat-model section.
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)

    # NEVER store plaintext or reversibly-encrypted passwords here —
    # only an Argon2id hash produced by auth_service.hash_password().
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.STUDENT, nullable=False)
    status: Mapped[UserStatus] = mapped_column(Enum(UserStatus), default=UserStatus.ACTIVE, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    files = relationship("File", back_populates="owner", cascade="all, delete-orphan")

    # file_permissions has TWO foreign keys into users (user_id = the
    # recipient, granted_by = who granted it) so each relationship here
    # must say explicitly which column it follows — otherwise SQLAlchemy
    # can't tell "the permissions I HOLD" from "the permissions I GAVE OUT".
    permissions_granted = relationship(
        "FilePermission",
        back_populates="user",
        foreign_keys="FilePermission.user_id",
        cascade="all, delete-orphan",
    )
    permissions_issued = relationship(
        "FilePermission",
        foreign_keys="FilePermission.granted_by",
        viewonly=True,
    )
