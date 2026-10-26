"""
Run with: python test_phase6_integrity.py
"""
import os
import shutil

TEST_STORAGE_DIR = "./test_phase6_storage"
os.environ["DATABASE_URL"] = "sqlite:///./test_phase6_http.db"
os.environ["SECURE_STORAGE_DIR"] = TEST_STORAGE_DIR

if os.path.exists("test_phase6_http.db"):
    os.remove("test_phase6_http.db")
if os.path.exists(TEST_STORAGE_DIR):
    shutil.rmtree(TEST_STORAGE_DIR)

from fastapi.testclient import TestClient  # noqa: E402

from app.db.base import Base  # noqa: E402
from app.db.session import engine, SessionLocal  # noqa: E402
import app.models  # noqa: E402
from app.models.file import File  # noqa: E402
from app.models.audit_log import AuditLog  # noqa: E402
from app.models.enums import AuditAction  # noqa: E402
from app.main import app  # noqa: E402
from app.services import hash_service  # noqa: E402

Base.metadata.create_all(engine)
client = TestClient(app)

CONTENT = b"%PDF-1.4\nOriginal, untampered VaultShare content.\n" + b"y" * 300


def run():
    client.post("/auth/register", json={"name": "Kamal", "email": "kamal@upes.ac.in", "password": "a-long-enough-password"})
    client.post("/auth/login", json={"email": "kamal@upes.ac.in", "password": "a-long-enough-password"})

    r = client.post("/files/upload", files={"file": ("Report.pdf", CONTENT, "application/pdf")})
    file_id = r.json()["id"]

    # 1. Happy path: fresh upload passes integrity verification
    r = client.get(f"/files/{file_id}/verify-integrity")
    assert r.status_code == 200, r.text
    assert r.json()["integrity"] == "ok"
    print("[PASS] freshly uploaded file passes integrity verification")

    # 2. THE KEY TEST: tamper with the sha256_hash column directly in the
    # DB, leaving the encrypted blob on disk completely untouched. GCM's
    # auth tag will verify fine (ciphertext is genuinely unmodified) --
    # only the independent SHA-256 recompute-and-compare catches this.
    with SessionLocal() as db:
        record = db.get(File, file_id)
        record.sha256_hash = "0" * 64  # obviously wrong hash
        db.commit()

    r = client.get(f"/files/{file_id}/verify-integrity")
    assert r.status_code == 500, r.text
    assert "integrity check failed" in r.json()["detail"].lower()
    hash_mismatch_message = r.json()["detail"]
    print("[PASS] DB-level hash tampering (ciphertext untouched) is caught by SHA-256 recompute")

    r = client.get(f"/files/{file_id}/download")
    assert r.status_code == 500
    assert r.json()["detail"] == hash_mismatch_message
    print("[PASS] download endpoint independently blocks the same tampered file, same message")

    # 3. Confirm the audit log recorded the CORRECT reason (sha256_mismatch,
    # not ciphertext_authentication_failed) -- proves the two checks are
    # genuinely distinguishable in the logs, not just in code comments.
    with SessionLocal() as db:
        entries = (
            db.query(AuditLog)
            .filter(AuditLog.file_id == file_id, AuditLog.action == AuditAction.INTEGRITY_CHECK_FAILED)
            .all()
        )
        reasons = {e.event_metadata.get("reason") for e in entries if e.event_metadata}
    assert "sha256_mismatch" in reasons
    assert "ciphertext_authentication_failed" not in reasons
    print(f"[PASS] audit log correctly attributes the failure to 'sha256_mismatch', logged {len(entries)} time(s)")

    # 4. Restore the correct hash -- proves this is a live comparison
    # each time, not a one-time flag stuck on the record.
    correct_hash = hash_service.compute_sha256(CONTENT)
    with SessionLocal() as db:
        record = db.get(File, file_id)
        record.sha256_hash = correct_hash
        db.commit()

    r = client.get(f"/files/{file_id}/verify-integrity")
    assert r.status_code == 200
    print("[PASS] restoring the correct hash makes the file pass verification again")

    # 5. verify-integrity is auth-gated and ownership-checked exactly like download
    rahul_client = TestClient(app)
    rahul_client.post("/auth/register", json={"name": "Rahul", "email": "rahul@upes.ac.in", "password": "another-long-password"})
    rahul_client.post("/auth/login", json={"email": "rahul@upes.ac.in", "password": "another-long-password"})
    r = rahul_client.get(f"/files/{file_id}/verify-integrity")
    assert r.status_code == 404
    print("[PASS] non-owner gets 404 on verify-integrity too, consistent with download")

    print("\nALL PHASE 6 INTEGRITY CHECKS PASSED")
    shutil.rmtree(TEST_STORAGE_DIR, ignore_errors=True)


if __name__ == "__main__":
    run()
