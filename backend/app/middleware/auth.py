"""
FastAPI dependencies that stand in front of every protected route.

get_current_user is the AUTHENTICATION gate: "who are you, and is your
session still valid?" It deliberately does NOT know anything about
files or permissions — that's a separate, later gate
(permission_service) so the two concerns never get tangled together.
"""
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session as OrmSession

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.models.enums import UserStatus
from app.services.auth_service import get_valid_session


def get_current_user(request: Request, db: OrmSession = Depends(get_db)) -> User:
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    session = get_valid_session(db, token)
    if session is None:
        # Covers: no such session, expired, or explicitly revoked (logged out).
        # Same error message for all three — no reason to tell a caller WHY
        # their session is invalid.
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired or invalid")

    user = db.get(User, session.user_id)
    if user is None or user.status != UserStatus.ACTIVE:
        # Handles the case where an admin disables an account mid-session —
        # the session row might still be technically unexpired, but the
        # user itself is no longer allowed in.
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is not active")

    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    """Second gate for admin-only routes. Layered on top of
    get_current_user rather than duplicating its logic."""
    if user.role.value != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return user
