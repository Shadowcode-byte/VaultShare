"""
Everything that touches a password or a session token lives here, and
nowhere else. Keeping it centralized means there is exactly one place
that knows how a password is hashed and exactly one place that knows
how a session is minted — routers just call these functions.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from argon2 import PasswordHasher
from argon2.exceptions import Argon2Error
from sqlalchemy.orm import Session as OrmSession

from app.core.config import settings
from app.models.session import Session as SessionModel

# Argon2id (the library's default "Type.ID") — chosen over bcrypt because
# it's memory-hard: cracking it at scale requires large amounts of RAM
# per guess, not just CPU time, which is what makes GPU/ASIC-based
# brute-forcing of bcrypt hashes comparatively cheap today. Defaults here
# (time_cost=3, memory_cost=64MB, parallelism=4) follow the library's
# OWASP-aligned recommended baseline for an interactive login endpoint.
_hasher = PasswordHasher()


def hash_password(plain_password: str) -> str:
    """Never store plain_password anywhere else — this is the only
    representation of it that touches the database."""
    return _hasher.hash(plain_password)


def verify_password(password_hash: str, plain_password: str) -> bool:
    """
    Returns False on ANY mismatch or malformed-hash condition rather
    than letting an exception bubble up — a router that forgets to
    catch a specific exception type must not accidentally treat a
    verification error as "logged in". Argon2Error is the base class
    for every exception this library can raise (wrong password,
    corrupt/foreign hash format, etc.) so catching it here — rather
    than only its VerifyMismatchError subclass — is deliberate: a
    malformed dummy_hash (used below for timing-safety) must fail
    closed exactly the same way a genuine wrong password does.
    """
    try:
        _hasher.verify(password_hash, plain_password)
        return True
    except Argon2Error:
        return False


# Precomputed once at import time so every "user not found" login still
# pays the same Argon2 verification cost as a real "wrong password"
# check — see login()'s use of this constant for why that matters.
DUMMY_PASSWORD_HASH = hash_password("dummy-fixed-value-never-used-as-a-real-password")


def needs_rehash(password_hash: str) -> bool:
    """
    If Argon2 parameters are strengthened later (e.g. bumping memory_cost
    as hardware gets cheaper), existing hashes made with the old, weaker
    parameters won't automatically upgrade. Calling this after a
    successful login lets the router silently re-hash and save the
    stronger version — the user never notices.
    """
    return _hasher.check_needs_rehash(password_hash)


# ---------------------------------------------------------------------
# Session management
# ---------------------------------------------------------------------

def create_session(
    db: OrmSession, user_id: str, ip_address: Optional[str] = None, user_agent: Optional[str] = None
) -> SessionModel:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.session_lifetime_minutes)
    session = SessionModel(
        user_id=user_id, expires_at=expires_at, ip_address=ip_address, user_agent=user_agent,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_valid_session(db: OrmSession, session_token: str) -> Optional[SessionModel]:
    session = db.get(SessionModel, session_token)
    if session is None or not session.is_valid:
        return None
    return session


def revoke_session(db: OrmSession, session: SessionModel) -> None:
    session.revoked_at = datetime.now(timezone.utc)
    db.commit()
