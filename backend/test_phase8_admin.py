"""
Run with: python test_phase8_admin.py
"""
import os
import shutil

TEST_STORAGE_DIR = "./test_phase8_storage"
os.environ["DATABASE_URL"] = "sqlite:///./test_phase8_http.db"
os.environ["SECURE_STORAGE_DIR"] = TEST_STORAGE_DIR

if os.path.exists("test_phase8_http.db"):
    os.remove("test_phase8_http.db")
if os.path.exists(TEST_STORAGE_DIR):
    shutil.rmtree(TEST_STORAGE_DIR)

from fastapi.testclient import TestClient  # noqa: E402

from app.db.base import Base  # noqa: E402
from app.db.session import engine, SessionLocal  # noqa: E402
import app.models  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.enums import UserRole  # noqa: E402
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

    r = rahul.get("/admin/users")
    assert r.status_code == 403, r.text
    print("[PASS] ordinary student gets 403 on admin routes (authenticated but not authorized)")

    r = rahul.get("/admin/stats")
    assert r.status_code == 403
    print("[PASS] ordinary student also denied /admin/stats")

    with SessionLocal() as db:
        user = db.query(User).filter(User.email == "kamal@upes.ac.in").first()
        user.role = UserRole.ADMIN
        db.commit()
    r = kamal.get("/admin/users")
    assert r.status_code == 200, r.text
    print("[PASS] promoting a user to admin (in DB) takes effect immediately on their existing session")

    emails = {u["email"] for u in r.json()}
    assert emails == {"kamal@upes.ac.in", "rahul@upes.ac.in"}
    print("[PASS] admin sees all registered users")

    kamal.post("/files/upload", files={"file": ("Report.pdf", b"%PDF-1.4\n" + b"x" * 200, "application/pdf")})
    file_id = kamal.get("/files/mine").json()[0]["id"]
    kamal.post(f"/files/{file_id}/share", json={"email": "rahul@upes.ac.in", "permission": "view"})

    bad_client = TestClient(app)
    bad_client.post("/auth/login", json={"email": "kamal@upes.ac.in", "password": "totally-wrong-password"})

    priya = new_client("Priya", "priya@upes.ac.in", "yet-another-long-pw")
    priya.get(f"/files/{file_id}/download")

    r = kamal.get("/admin/stats")
    assert r.status_code == 200, r.text
    stats = r.json()
    assert stats["total_users"] == 3
    assert stats["total_files"] == 1
    assert stats["total_active_shares"] == 1
    assert stats["failed_login_attempts"] >= 1
    assert stats["unauthorized_access_attempts"] >= 1
    assert len(stats["recent_events"]) > 0
    print(f"[PASS] /admin/stats reflects real counts: {stats['total_users']} users, "
          f"{stats['total_files']} files, {stats['total_active_shares']} active shares, "
          f"{stats['failed_login_attempts']} failed logins, {stats['unauthorized_access_attempts']} unauthorized attempts")

    r = kamal.get("/admin/audit-logs", params={"action": "FILE_SHARED"})
    assert r.status_code == 200
    assert all(e["action"] == "FILE_SHARED" for e in r.json())
    assert len(r.json()) == 1
    print("[PASS] audit log filter by action returns only matching entries")

    entry = r.json()[0]
    assert entry["user_email"] == "kamal@upes.ac.in"
    print("[PASS] audit log entries include resolved user_email")

    r = kamal.get("/admin/audit-logs", params={"limit": 99999})
    assert r.status_code == 422
    print("[PASS] requesting a limit above the hard cap (200) is rejected, not silently clamped or honored")

    priya_id = priya.get("/auth/me").json()["id"]
    r = kamal.patch(f"/admin/users/{priya_id}/status", json={"status": "disabled"})
    assert r.status_code == 200, r.text

    r = priya.get("/auth/me")
    assert r.status_code == 401
    print("[PASS] disabling a user's account immediately invalidates their existing session")

    kamal_id = kamal.get("/auth/me").json()["id"]
    r = kamal.patch(f"/admin/users/{kamal_id}/status", json={"status": "disabled"})
    assert r.status_code == 400
    print("[PASS] admin is blocked from disabling their own account")

    with SessionLocal() as db:
        target = db.get(User, priya_id)
        assert target.status.value == "disabled"
    kamal.patch(f"/admin/users/{priya_id}/status", json={"status": "active"})
    r = TestClient(app).post("/auth/login", json={"email": "priya@upes.ac.in", "password": "yet-another-long-pw"})
    assert r.status_code == 200
    print("[PASS] re-enabling a disabled account allows login again")

    print("\nALL PHASE 8 ADMIN CHECKS PASSED")
    shutil.rmtree(TEST_STORAGE_DIR, ignore_errors=True)


if __name__ == "__main__":
    run()
