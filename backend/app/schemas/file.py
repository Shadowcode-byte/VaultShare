from datetime import datetime

from pydantic import BaseModel


class FileMetadata(BaseModel):
    """
    Notice what's NOT here: encrypted_storage_path and encryption_nonce.
    Neither is secret on its own (the nonce doesn't need to be — GCM is
    designed for that), but the storage path is an internal server
    filesystem detail that has no reason to leave the backend, per the
    project's own rule against exposing internal implementation details
    to clients.
    """
    id: str
    owner_id: str
    original_filename: str
    file_type: str
    file_size: int
    sha256_hash: str
    created_at: datetime

    class Config:
        from_attributes = True
