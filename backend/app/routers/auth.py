from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as OrmSession

from app.core.config import settings
from app.db.session import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.models.enums import AuditAction, AuditResult
from app.schemas.auth import RegisterRequest, LoginRequest, UserPublic
from app.services import auth_service, audit_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _cookie_kwargs() -> dict:
    """
    HttpOnly:  JavaScript can never read this cookie, which blocks the
               most common way a stolen XSS payload steals a session.
    Secure:    only sent over HTTPS. Disabled automatically in local dev
               (env=development) because a plain http://localhost
               connection would otherwise silently never receive the
               cookie at all — this must be True in any real deployment.
    SameSite:  "strict" means the browser will not attach this cookie to
               any cross-site request, which is the primary defense this
               app relies on against CSRF for cookie-authenticated
               state-changing requests (upload/share/revoke/delete).
    """
    return {
        "httponly": True,
        "secure": settings.env != "development",
        "samesite": "strict",
        "max_age": settings.session_lifetime_minutes * 60,
    }


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: OrmSession = Depends(get_db)):
    user = User(
        name=payload.name,
        email=payload.email.lower(),  # normalize so "A@x.com" and "a@x.com" can't both register
        password_hash=auth_service.hash_password(payload.password),
        # role is intentionally NOT taken from payload — see schema comment
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists")

    db.refresh(user)
    audit_service.log_event(db, AuditAction.USER_REGISTERED, AuditResult.SUCCESS, user_id=user.id)
    return user


@router.post("/login", response_model=UserPublic)
def login(payload: LoginRequest, request: Request, response: Response, db: OrmSession = Depends(get_db)):
    email = payload.email.lower()
    user = db.query(User).filter(User.email == email).first()

    # Deliberately generic failure path: whether the email doesn't exist
    # OR the password is wrong, we (a) return the exact same error
    # message and (b) still run verify_password against a real Argon2
    # hash in the "unknown email" case, using a precomputed dummy hash.
    # Skipping the verify step for unknown emails would make login
    # measurably faster for "email not found" than for "wrong password"
    # — a timing side-channel that lets an attacker enumerate valid emails.
    password_ok = auth_service.verify_password(
        user.password_hash if user else auth_service.DUMMY_PASSWORD_HASH, payload.password
    )

    if not user or not password_ok:
        audit_service.log_event(
            db, AuditAction.USER_LOGIN_FAILED, AuditResult.FAILURE,
            user_id=user.id if user else None,
            metadata={"attempted_email": email},
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if user.status.value != "active":
        audit_service.log_event(db, AuditAction.USER_LOGIN_FAILED, AuditResult.DENIED, user_id=user.id)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    if auth_service.needs_rehash(user.password_hash):
        user.password_hash = auth_service.hash_password(payload.password)
        db.commit()

    session = auth_service.create_session(
        db, user.id, ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    response.set_cookie(settings.session_cookie_name, session.id, **_cookie_kwargs())

    audit_service.log_event(db, AuditAction.USER_LOGIN, AuditResult.SUCCESS, user_id=user.id)
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request, response: Response,
    db: OrmSession = Depends(get_db), user: User = Depends(get_current_user),
):
    token = request.cookies.get(settings.session_cookie_name)
    session = auth_service.get_valid_session(db, token) if token else None
    if session:
        # Server-side revocation is what actually ends the session — clearing
        # the cookie alone would only stop THIS browser from presenting it;
        # a copied cookie value would still work until natural expiry.
        auth_service.revoke_session(db, session)
    response.delete_cookie(settings.session_cookie_name)
    audit_service.log_event(db, AuditAction.USER_LOGOUT, AuditResult.SUCCESS, user_id=user.id)
    return None


@router.get("/me", response_model=UserPublic)
def get_me(user: User = Depends(get_current_user)):
    return user
