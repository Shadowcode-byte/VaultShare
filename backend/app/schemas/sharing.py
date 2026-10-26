from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models.enums import PermissionLevel
from app.schemas.file import FileMetadata


class ShareRequest(BaseModel):
    email: EmailStr
    permission: PermissionLevel


class ShareInfo(BaseModel):
    """One active grant, from the OWNER's point of view — used by the
    'who has access to this file' listing."""
    user_id: str
    name: str
    email: EmailStr
    permission: PermissionLevel
    granted_at: datetime

    class Config:
        from_attributes = True


class SharedFileMetadata(FileMetadata):
    """A file that's been shared WITH the current user — adds their
    permission level and who owns it, since 'Shared With Me' needs both."""
    permission: PermissionLevel
    owner_name: str
