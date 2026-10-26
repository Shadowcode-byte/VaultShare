import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Integer, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class File(Base):
    __tablename__ = "files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)

    # Original filename is stored ONLY for display purposes (e.g. "Report.pdf"
    # shown in the UI). It is never used to build a filesystem path — that
    # would allow path traversal (e.g. "../../etc/passwd") or filename
    # collisions between users. The actual on-disk name is stored_filename.
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)

    # Random UUID-based name, no extension, no user input — this is what
    # the file is actually saved as under secure_storage/.
    stored_filename: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)

    file_type: Mapped[str] = mapped_column(String(20), nullable=False)  # validated extension, e.g. ".pdf"
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)      # bytes, post-validation

    encrypted_storage_path: Mapped[str] = mapped_column(String(500), nullable=False)

    # AES-256-GCM nonce (96-bit, base64) — must be unique per encryption
    # operation. Stored alongside the file since it's required (with the
    # server-held key) to decrypt; it is NOT secret on its own.
    encryption_nonce: Mapped[str] = mapped_column(String(64), nullable=False)

    # SHA-256 of the ORIGINAL plaintext file, computed at upload time.
    # Used to detect tampering on download — see hash_service.
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    owner = relationship("User", back_populates="files")
    permissions = relationship("FilePermission", back_populates="file", cascade="all, delete-orphan")
