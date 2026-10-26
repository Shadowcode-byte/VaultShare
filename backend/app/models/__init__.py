"""
Import every model here so that Base.metadata is fully populated
whenever `app.models` is imported. Alembic's autogenerate and our
test bootstrap (Base.metadata.create_all) both depend on this.
"""
from app.models.user import User
from app.models.file import File
from app.models.permission import FilePermission
from app.models.audit_log import AuditLog
from app.models.session import Session

__all__ = ["User", "File", "FilePermission", "AuditLog", "Session"]
