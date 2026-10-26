import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, status
from sqlalchemy.orm import Session as OrmSession

from app.db.session import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.models.file import File
from app.models.enums import AuditAction, AuditResult, PermissionLevel
from app.schemas.file import FileMetadata
from app.schemas.sharing import ShareRequest, ShareInfo, SharedFileMetadata
from app.services import audit_service, crypto_service, hash_service, storage_service, permission_service
from app.services.file_validation_service import validate_upload, FileValidationError

router = APIRouter(prefix="/files", tags=["files"])


# ---------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------

def _get_owned_file_or_404(file_id: str, db: OrmSession, user: User) -> File:
    """
    STRICT ownership check — for actions the access-control model
    reserves to the owner alone (share, revoke, list-shares, delete).
    A user with an active DOWNLOAD grant on a file is NOT the owner and
    must not be able to re-share it onward or revoke someone else's
    access — that's the 'SHARED USER cannot re-share' rule from the
    project's access-control model.
    """
    file_record = db.get(File, file_id)
    if file_record is None or file_record.owner_id != user.id:
        if file_record is not None:
            audit_service.log_event(
                db, AuditAction.UNAUTHORIZED_ACCESS_ATTEMPT, AuditResult.DENIED,
                user_id=user.id, file_id=file_id, metadata={"required": "owner"},
            )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return file_record


def _get_accessible_file_or_404(
    file_id: str, db: OrmSession, user: User, required: PermissionLevel
) -> File:
    """
    Content-access check — owner OR a valid active share at the
    required level. This is the gate every read of a file's metadata
    or bytes goes through. 404 (not 403) for both 'doesn't exist' and
    'exists but you have no access', for the IDOR reasons discussed in
    Phase 5/6 — this is the single most important line to be able to
    defend in a viva: authentication alone ("are you logged in?") is
    NOT the same question as authorization ("are you allowed to touch
    THIS specific resource?"), and every route here asks both.
    """
    file_record = db.get(File, file_id)
    if file_record is None or not permission_service.has_access(db, file_record, user, required):
        if file_record is not None:
            audit_service.log_event(
                db, AuditAction.UNAUTHORIZED_ACCESS_ATTEMPT, AuditResult.DENIED,
                user_id=user.id, file_id=file_id, metadata={"required": required.value},
            )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return file_record


def _decrypt_and_verify(file_record: File, db: OrmSession, user: User) -> bytes:
    """Two independent integrity checks — see Phase 6 for why both exist:
    GCM's auth tag (ciphertext-at-rest) and a SHA-256 recompute (the DB
    metadata row). Unchanged from Phase 6, just relocated alongside the
    new access-control helpers above."""
    ciphertext = storage_service.load_encrypted(file_record.encrypted_storage_path)
    try:
        plaintext = crypto_service.decrypt_bytes(
            ciphertext, file_record.encryption_nonce, associated_data=file_record.stored_filename.encode()
        )
    except crypto_service.DecryptionError:
        audit_service.log_event(
            db, AuditAction.INTEGRITY_CHECK_FAILED, AuditResult.FAILURE, user_id=user.id, file_id=file_record.id,
            metadata={"reason": "ciphertext_authentication_failed"},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="This file could not be decrypted and may be corrupted. Contact support.",
        )

    recomputed_hash = hash_service.compute_sha256(plaintext)
    if recomputed_hash != file_record.sha256_hash:
        audit_service.log_event(
            db, AuditAction.INTEGRITY_CHECK_FAILED, AuditResult.FAILURE, user_id=user.id, file_id=file_record.id,
            metadata={"reason": "sha256_mismatch"},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Integrity check failed: this file's fingerprint no longer matches its stored record. Contact support.",
        )

    return plaintext


# ---------------------------------------------------------------------
# Upload / list / metadata
# ---------------------------------------------------------------------

@router.post("/validate")
async def validate_file(file: UploadFile, user: User = Depends(get_current_user)):
    raw_bytes = await file.read()
    try:
        result = validate_upload(file.filename or "", raw_bytes)
    except FileValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return {
        "status": "valid", "display_filename": result.display_filename,
        "extension": result.extension, "detected_mime": result.detected_mime,
        "size_bytes": result.size_bytes,
    }


@router.post("/upload", response_model=FileMetadata, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile, db: OrmSession = Depends(get_db), user: User = Depends(get_current_user),
):
    raw_bytes = await file.read()
    try:
        validated = validate_upload(file.filename or "", raw_bytes)
    except FileValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    sha256_hex = hash_service.compute_sha256(raw_bytes)
    stored_filename = uuid.uuid4().hex
    ciphertext, nonce_b64 = crypto_service.encrypt_bytes(raw_bytes, associated_data=stored_filename.encode())
    storage_path = storage_service.save_encrypted(stored_filename, ciphertext)

    file_record = File(
        owner_id=user.id, original_filename=validated.display_filename, stored_filename=stored_filename,
        file_type=validated.extension, file_size=validated.size_bytes,
        encrypted_storage_path=storage_path, encryption_nonce=nonce_b64, sha256_hash=sha256_hex,
    )
    db.add(file_record)
    db.commit()
    db.refresh(file_record)

    audit_service.log_event(db, AuditAction.FILE_UPLOADED, AuditResult.SUCCESS, user_id=user.id, file_id=file_record.id)
    return file_record


@router.get("/mine", response_model=list[FileMetadata])
def list_my_files(db: OrmSession = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(File).filter(File.owner_id == user.id).order_by(File.created_at.desc()).all()


@router.get("/shared-with-me", response_model=list[SharedFileMetadata])
def list_shared_with_me(db: OrmSession = Depends(get_db), user: User = Depends(get_current_user)):
    files = permission_service.list_files_shared_with(db, user.id)
    results = []
    for f in files:
        grant = permission_service.get_active_permission(db, f.id, user.id)
        results.append(SharedFileMetadata(
            id=f.id, owner_id=f.owner_id, original_filename=f.original_filename,
            file_type=f.file_type, file_size=f.file_size, sha256_hash=f.sha256_hash,
            created_at=f.created_at, permission=grant.permission, owner_name=f.owner.name,
        ))
    return results


@router.get("/{file_id}", response_model=FileMetadata)
def get_file_details(file_id: str, db: OrmSession = Depends(get_db), user: User = Depends(get_current_user)):
    file_record = _get_accessible_file_or_404(file_id, db, user, PermissionLevel.VIEW)
    return file_record


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(file_id: str, db: OrmSession = Depends(get_db), user: User = Depends(get_current_user)):
    """
    Owner-only, matching the access-control model from Phase 7 (a
    shared user — even with DOWNLOAD access — cannot delete a file any
    more than they can share or revoke it onward). Deleting the DB row
    cascades to file_permissions (configured in Phase 2's File model),
    so a deleted file doesn't leave orphaned share records behind.
    """
    file_record = _get_owned_file_or_404(file_id, db, user)

    # Log BEFORE deleting. Once the file row is gone, a brand-new
    # audit_logs row naming its file_id would itself violate the
    # foreign key — ON DELETE SET NULL only rescues rows that already
    # existed before the delete; it can't help an INSERT that names an
    # id which no longer exists at insert time.
    audit_service.log_event(
        db, AuditAction.FILE_DELETED, AuditResult.SUCCESS, user_id=user.id, file_id=file_id,
    )

    storage_service.delete_encrypted(file_record.encrypted_storage_path)
    db.delete(file_record)
    db.commit()

    return None


# ---------------------------------------------------------------------
# Download / integrity
# ---------------------------------------------------------------------

@router.get("/{file_id}/verify-integrity")
def verify_integrity(file_id: str, db: OrmSession = Depends(get_db), user: User = Depends(get_current_user)):
    file_record = _get_accessible_file_or_404(file_id, db, user, PermissionLevel.DOWNLOAD)
    _decrypt_and_verify(file_record, db, user)
    audit_service.log_event(
        db, AuditAction.FILE_ACCESSED, AuditResult.SUCCESS, user_id=user.id, file_id=file_id,
        metadata={"check": "integrity_verify"},
    )
    return {"integrity": "ok", "file_id": file_id, "sha256_hash": file_record.sha256_hash}


@router.get("/{file_id}/download")
def download_file(file_id: str, db: OrmSession = Depends(get_db), user: User = Depends(get_current_user)):
    file_record = _get_accessible_file_or_404(file_id, db, user, PermissionLevel.DOWNLOAD)
    plaintext = _decrypt_and_verify(file_record, db, user)

    audit_service.log_event(db, AuditAction.FILE_DOWNLOADED, AuditResult.SUCCESS, user_id=user.id, file_id=file_id)
    return Response(
        content=plaintext, media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{file_record.original_filename}"'},
    )


# ---------------------------------------------------------------------
# Sharing (owner-only)
# ---------------------------------------------------------------------

@router.post("/{file_id}/share", response_model=ShareInfo, status_code=status.HTTP_201_CREATED)
def share_file(
    file_id: str, payload: ShareRequest, db: OrmSession = Depends(get_db), user: User = Depends(get_current_user),
):
    file_record = _get_owned_file_or_404(file_id, db, user)

    email = payload.email.lower()
    if email == user.email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You already own this file.")

    grantee = db.query(User).filter(User.email == email).first()
    if grantee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No registered user found with that email.")

    grant = permission_service.grant_permission(db, file_record, grantee, payload.permission, granted_by=user)

    audit_service.log_event(
        db, AuditAction.FILE_SHARED, AuditResult.SUCCESS, user_id=user.id, file_id=file_id,
        metadata={"shared_with": grantee.id, "permission": payload.permission.value},
    )
    return ShareInfo(
        user_id=grantee.id, name=grantee.name, email=grantee.email,
        permission=grant.permission, granted_at=grant.granted_at,
    )


@router.get("/{file_id}/shares", response_model=list[ShareInfo])
def list_shares(file_id: str, db: OrmSession = Depends(get_db), user: User = Depends(get_current_user)):
    file_record = _get_owned_file_or_404(file_id, db, user)
    grants = permission_service.list_active_shares(db, file_record.id)
    return [
        ShareInfo(user_id=g.user.id, name=g.user.name, email=g.user.email, permission=g.permission, granted_at=g.granted_at)
        for g in grants
    ]


@router.delete("/{file_id}/share/{target_user_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_share(
    file_id: str, target_user_id: str, db: OrmSession = Depends(get_db), user: User = Depends(get_current_user),
):
    file_record = _get_owned_file_or_404(file_id, db, user)
    revoked = permission_service.revoke_permission(db, file_record, target_user_id)
    if not revoked:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active share found for that user.")

    audit_service.log_event(
        db, AuditAction.FILE_ACCESS_REVOKED, AuditResult.SUCCESS, user_id=user.id, file_id=file_id,
        metadata={"revoked_user": target_user_id},
    )
    return None
