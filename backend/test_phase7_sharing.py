"""
Run with: python test_phase7_sharing.py
"""
import os
import shutil

TEST_STORAGE_DIR = "./test_phase7_storage"
os.environ["DATABASE_URL"] = "sqlite:///./test_phase7_http.db"
os.environ["SECURE_STORAGE_DIR"] = TEST_STORAGE_DIR

if os.path.exists("test_phase7_http.db"):
    os.remove("test_phase7_http.db")
if os.path.exists(TEST_STORAGE_DIR):
    shutil.rmtree(TEST_STORAGE_DIR)

from fastapi.testclient import TestClient  # noqa: E402

from app.db.base import Base  # noqa: E402
from app.db.session import engine  # noqa: E402
import app.models  # noqa: E402
from app.main import app  # noqa: E402

Base.metadata.create_all(engine)

CONTENT = b"%PDF-1.4\nKamal's Project_Report content for sharing tests.\n" + b"z" * 300


def new_client(name, email, password):
    c = TestClient(app)
    c.post("/auth/register", json={"name": name, "email": email, "password": password})
    c.post("/auth/login", json={"email": email, "password": password})
    return c


def run():
    kamal = new_client("Kamal", "kamal@upes.ac.in", "a-long-enough-password")
    rahul = new_client("Rahul", "rahul@upes.ac.in", "another-long-password")
    priya = new_client("Priya", "priya@upes.ac.in", "yet-another-long-pw")

    r = kamal.post("/files/upload", files={"file": ("Project_Report.pdf", CONTENT, "application/pdf")})
    file_id = r.json()["id"]

    assert rahul.get(f"/files/{file_id}").status_code == 404
    assert rahul.get(f"/files/{file_id}/download").status_code == 404
    print("[PASS] before sharing, a non-owner gets 404 on both metadata and download")

    r = kamal.post(f"/files/{file_id}/share", json={"email": "rahul@upes.ac.in", "permission": "download"})
    assert r.status_code == 201, r.text
    print("[PASS] owner shares file with Rahul at 'download' level")

    r = rahul.get(f"/files/{file_id}")
    assert r.status_code == 200
    r = rahul.get(f"/files/{file_id}/download")
    assert r.status_code == 200
    assert r.content == CONTENT
    print("[PASS] Rahul (download-level share) can view metadata and download identical content")

    assert priya.get(f"/files/{file_id}").status_code == 404
    print("[PASS] Priya, who has no share at all, still gets 404")

    r = kamal.post(f"/files/{file_id}/share", json={"email": "priya@upes.ac.in", "permission": "view"})
    assert r.status_code == 201
    r = priya.get(f"/files/{file_id}")
    assert r.status_code == 200
    print("[PASS] Priya (view-level share) can now see file metadata")

    r = priya.get(f"/files/{file_id}/download")
    assert r.status_code == 404
    print("[PASS] Priya (view-only) is DENIED actual download -- VIEW does not imply DOWNLOAD")

    r = rahul.post(f"/files/{file_id}/share", json={"email": "priya@upes.ac.in", "permission": "download"})
    assert r.status_code == 404, r.text
    print("[PASS] a shared (non-owner) user cannot share the file onward (owner-only action)")

    r = rahul.delete(f"/files/{file_id}/share/does-not-matter")
    assert r.status_code == 404
    print("[PASS] a shared (non-owner) user cannot revoke anyone's access")

    r = kamal.get(f"/files/{file_id}/shares")
    assert r.status_code == 200
    emails = {s["email"] for s in r.json()}
    assert emails == {"rahul@upes.ac.in", "priya@upes.ac.in"}
    print("[PASS] owner's share list shows both active recipients")

    r = rahul.get("/files/shared-with-me")
    assert r.status_code == 200
    shared = r.json()
    assert len(shared) == 1 and shared[0]["id"] == file_id and shared[0]["permission"] == "download"
    print("[PASS] Rahul's 'shared with me' list shows the file with correct permission level")

    rahul_id = rahul.get("/auth/me").json()["id"]
    r = kamal.delete(f"/files/{file_id}/share/{rahul_id}")
    assert r.status_code == 204
    r = rahul.get(f"/files/{file_id}/download")
    assert r.status_code == 404
    r = rahul.get("/files/shared-with-me")
    assert len(r.json()) == 0
    print("[PASS] revoked user is denied immediately -- both direct download and 'shared with me' listing")

    r = priya.get(f"/files/{file_id}")
    assert r.status_code == 200
    print("[PASS] revoking one user's access does not affect another user's separate share")

    r = kamal.post(f"/files/{file_id}/share", json={"email": "rahul@upes.ac.in", "permission": "view"})
    assert r.status_code == 201, r.text
    r = rahul.get(f"/files/{file_id}")
    assert r.status_code == 200
    r = rahul.get(f"/files/{file_id}/download")
    assert r.status_code == 404
    print("[PASS] re-sharing a previously-revoked user works and applies the new permission level")

    r = kamal.post(f"/files/{file_id}/share", json={"email": "nobody-registered@upes.ac.in", "permission": "view"})
    assert r.status_code == 404
    print("[PASS] sharing with an unregistered email is rejected with a clean error")

    r = kamal.post(f"/files/{file_id}/share", json={"email": "kamal@upes.ac.in", "permission": "download"})
    assert r.status_code == 400
    print("[PASS] owner attempting to share with themselves is rejected")

    print("\nALL PHASE 7 SHARING CHECKS PASSED")
    shutil.rmtree(TEST_STORAGE_DIR, ignore_errors=True)


if __name__ == "__main__":
    run()
