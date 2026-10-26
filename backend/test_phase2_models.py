"""
Phase 2 smoke test — NOT the full security test suite (that comes in
Phase 11). This just proves the schema behaves the way the design
claims: unique email is enforced, revoked permissions read as inactive,
and cascade delete doesn't silently orphan rows.

Run with: python test_phase2_models.py
"""
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy.exc import IntegrityError

from app.db.base import Base
from app.models import User, File, FilePermission, AuditLog, Session
from app.models.enums import UserRole, PermissionLevel, AuditAction, AuditResult

engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(engine)


def run():
    with OrmSession(engine) as db:
        # 1. Create two users
        kamal = User(name="Kamal", email="kamal@example.com", password_hash="argon2$fake$hash")
        rahul = User(name="Rahul", email="rahul@example.com", password_hash="argon2$fake$hash")
        db.add_all([kamal, rahul])
        db.commit()
        assert kamal.role == UserRole.STUDENT, "default role should be student, not admin"
        print("[PASS] users created with default role=student")

        # 2. Unique email constraint
        try:
            dupe = User(name="Fake Kamal", email="kamal@example.com", password_hash="x")
            db.add(dupe)
            db.commit()
            raise AssertionError("duplicate email should have been rejected")
        except IntegrityError:
            db.rollback()
            print("[PASS] duplicate email rejected by unique constraint")

        # 3. File upload record
        report = File(
            owner_id=kamal.id,
            original_filename="Project_Report.pdf",
            stored_filename=uuid.uuid4().hex,
            file_type=".pdf",
            file_size=204800,
            encrypted_storage_path="./secure_storage/" + uuid.uuid4().hex,
            encryption_nonce="ZmFrZS1ub25jZQ==",
            sha256_hash="a" * 64,
        )
        db.add(report)
        db.commit()
        print("[PASS] file record created and linked to owner")

        # 4. Share with Rahul, then revoke, confirm is_active flips
        grant = FilePermission(
            file_id=report.id, user_id=rahul.id, permission=PermissionLevel.DOWNLOAD,
            granted_by=kamal.id,
        )
        db.add(grant)
        db.commit()
        assert grant.is_active is True
        print("[PASS] permission grant starts active")

        grant.revoked_at = datetime.now(timezone.utc)
        db.commit()
        assert grant.is_active is False
        print("[PASS] revoked permission correctly reads as inactive")

        # 5. A second grant for the SAME (file, user) pair should be rejected —
        # re-sharing now updates the existing row (see permission_service in
        # Phase 7) rather than inserting a parallel one.
        try:
            dupe_grant = FilePermission(
                file_id=report.id, user_id=rahul.id, permission=PermissionLevel.VIEW,
                granted_by=kamal.id,
            )
            db.add(dupe_grant)
            db.commit()
            raise AssertionError("a second (file, user) grant row should be rejected")
        except IntegrityError:
            db.rollback()
            print("[PASS] duplicate (file, user) permission row rejected by unique constraint")

        # 6. Audit log entries, including one with no user (failed login on unknown email)
        db.add(AuditLog(
            user_id=kamal.id, file_id=report.id, action=AuditAction.FILE_SHARED,
            result=AuditResult.SUCCESS, event_metadata={"shared_with": rahul.id},
        ))
        db.add(AuditLog(
            user_id=None, file_id=None, action=AuditAction.USER_LOGIN_FAILED,
            result=AuditResult.FAILURE, event_metadata={"attempted_email": "nobody@example.com"},
        ))
        db.commit()
        count = db.query(AuditLog).count()
        assert count == 2
        print(f"[PASS] audit log accepts both user-linked and anonymous events ({count} rows)")

        # 7. Session validity window
        sess = Session(
            user_id=kamal.id,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=60),
        )
        db.add(sess)
        db.commit()
        assert sess.is_valid is True
        sess.revoked_at = datetime.now(timezone.utc)
        db.commit()
        assert sess.is_valid is False
        print("[PASS] session is_valid correctly reflects revocation")

        # 8. Cascade: deleting the owner should NOT silently orphan their file
        # permission rows (cascade="all, delete-orphan" on User.files handles this)
        db.delete(kamal)
        db.commit()
        remaining_files = db.query(File).filter_by(owner_id=kamal.id).count()
        remaining_perms = db.query(FilePermission).filter_by(file_id=report.id).count()
        assert remaining_files == 0, "file should cascade-delete with owner"
        assert remaining_perms == 0, "permission should cascade-delete with its file"
        print("[PASS] deleting a user cascades to their files and those files' permissions")

    print("\nALL PHASE 2 MODEL CHECKS PASSED")


if __name__ == "__main__":
    run()
