"""
Run with: python test_phase11_delete.py
"""
import os
import shutil

TEST_STORAGE_DIR = "./test_phase11_storage"
os.environ["DATABASE_URL"] = "sqlite:///./test_phase11_http.db"
os.environ["SECURE_STORAGE_DIR"] = TEST_STORAGE_DIR

if os.path.exists("test_phase11_http.db"):
    os.remove("test_phase11_http.db")
if os.path.exists(TEST_STORAGE_DIR):
    shutil.rmtree(TEST_STORAGE_DIR)

from fastapi.testclient import TestClient  # noqa: E402

from app.db.base import Base  # noqa: E402
from app.db.session import engine, SessionLocal  # noqa: E402
import app.models  # noqa: E402
from app.models.file import File  # noqa: E402
from app.models.permission import FilePermission  # noqa: E402
from app.models.audit_log import AuditLog  # noqa: E402
from app.main import app  # noqa: E402

Base.metadata.create_all(engine)


def new_client(name, email, password):
    c = TestClient(app)
    c.post("/auth/register", json={"name": name, "email": email, "password": password})
    c.post("/auth/login", json={"email": email, "password": password})
    return c


def run():
    kamal = new_client("Kamal", "kamal@upes.ac.in", "a-long-enough-password")
    rahul = new_client("Rahul", "rahul@upes.ac.in", "another-long-password")

    r = kamal.post("/files/upload", files={"file": ("Report.pdf", b"%PDF-1.4\n" + b"x" * 200, "application/pdf")})
    file_id = r.json()["id"]
    with SessionLocal() as db:
        storage_path = db.get(File, file_id).encrypted_storage_path
    assert os.path.exists(storage_path)
    print("[PASS] file uploaded, encrypted blob exists on disk")

    kamal.post(f"/files/{file_id}/share", json={"email": "rahul@upes.ac.in", "permission": "download"})
    with SessionLocal() as db:
        assert db.query(FilePermission).filter_by(file_id=file_id).count() == 1
    print("[PASS] file shared with Rahul, one active permission row exists")

    r = rahul.delete(f"/files/{file_id}")
    assert r.status_code == 404, r.text
    print("[PASS] a shared (non-owner) user cannot delete the file (404, same as any other owner-only action)")

    # THE KEY TEST: owner deletes the file. Must succeed without a
    # foreign-key violation, even though audit_logs rows already
    # reference this file_id (upload + share events above). Before the
    # ON DELETE SET NULL fix, this would have passed on SQLite (which
    # doesn't enforce FKs by default) but thrown an IntegrityError on
    # Postgres. FK enforcement is now explicitly turned on for SQLite
    # too, so this test actually exercises the real constraint.
    r = kamal.delete(f"/files/{file_id}")
    assert r.status_code == 204, r.text
    print("[PASS] owner deletes the file successfully (no FK violation despite existing audit history)")

    assert not os.path.exists(storage_path)
    print("[PASS] encrypted file removed from disk storage")

    with SessionLocal() as db:
        assert db.query(FilePermission).filter_by(file_id=file_id).count() == 0
    print("[PASS] file_permissions row cascaded away with the file")

    with SessionLocal() as db:
        all_logs = db.query(AuditLog).all()
        linked_to_deleted_file = [l for l in all_logs if l.file_id == file_id]
        assert len(linked_to_deleted_file) == 0, "no audit row should still reference the deleted file_id"
        upload_events = [l for l in all_logs if l.action.value == "FILE_UPLOADED"]
        assert len(upload_events) == 1
        assert upload_events[0].file_id is None
    print("[PASS] audit log entries for the deleted file survive, with file_id correctly set to NULL")

    assert kamal.get(f"/files/{file_id}").status_code == 404
    assert kamal.get(f"/files/{file_id}/download").status_code == 404
    print("[PASS] deleted file returns 404 on metadata and download routes")

    print("\nALL PHASE 11 DELETION CHECKS PASSED")
    shutil.rmtree(TEST_STORAGE_DIR, ignore_errors=True)


if __name__ == "__main__":
    run()
