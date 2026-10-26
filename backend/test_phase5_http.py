"""
Run with: python test_phase5_http.py
"""
import os
import shutil

TEST_STORAGE_DIR = "./test_phase5_storage"
os.environ["DATABASE_URL"] = "sqlite:///./test_phase5_http.db"
os.environ["SECURE_STORAGE_DIR"] = TEST_STORAGE_DIR

if os.path.exists("test_phase5_http.db"):
    os.remove("test_phase5_http.db")
if os.path.exists(TEST_STORAGE_DIR):
    shutil.rmtree(TEST_STORAGE_DIR)

from fastapi.testclient import TestClient  # noqa: E402

from app.db.base import Base  # noqa: E402
from app.db.session import engine  # noqa: E402
import app.models  # noqa: E402
from app.models.file import File  # noqa: E402
from app.main import app  # noqa: E402

Base.metadata.create_all(engine)
client = TestClient(app)

PDF_CONTENT = b"%PDF-1.4\nKamal's real VaultShare project report content.\n" + b"x" * 300


def run():
    client.post("/auth/register", json={"name": "Kamal", "email": "kamal@upes.ac.in", "password": "a-long-enough-password"})
    client.post("/auth/login", json={"email": "kamal@upes.ac.in", "password": "a-long-enough-password"})

    r = client.post("/files/upload", files={"file": ("Report.pdf", PDF_CONTENT, "application/pdf")})
    assert r.status_code == 201, r.text
    file_meta = r.json()
    file_id = file_meta["id"]
    assert file_meta["original_filename"] == "Report.pdf"
    assert len(file_meta["sha256_hash"]) == 64
    print("[PASS] upload succeeds, returns metadata with a proper SHA-256 hash")

    from app.db.session import SessionLocal
    with SessionLocal() as db:
        record = db.get(File, file_id)
        with open(record.encrypted_storage_path, "rb") as f:
            on_disk = f.read()
        storage_path = record.encrypted_storage_path
    assert b"Kamal's real VaultShare" not in on_disk
    print("[PASS] file on disk is genuinely encrypted (plaintext not present in stored bytes)")

    mode = oct(os.stat(storage_path).st_mode)[-3:]
    assert mode == "600", f"expected 0600 permissions, got {mode}"
    print("[PASS] encrypted file on disk has 0600 (owner-only) permissions")

    r = client.get("/files/mine")
    assert r.status_code == 200
    assert len(r.json()) == 1
    print("[PASS] owner sees their uploaded file in the file list")

    r = client.get(f"/files/{file_id}/download")
    assert r.status_code == 200
    assert r.content == PDF_CONTENT
    print("[PASS] owner download returns byte-for-byte identical original content")

    rahul_client = TestClient(app)
    rahul_client.post("/auth/register", json={"name": "Rahul", "email": "rahul@upes.ac.in", "password": "another-long-password"})
    rahul_client.post("/auth/login", json={"email": "rahul@upes.ac.in", "password": "another-long-password"})

    r = rahul_client.get(f"/files/{file_id}/download")
    assert r.status_code == 404, r.text
    print("[PASS] non-owner accessing the file gets 404 (existence not confirmed), not 403")

    r = rahul_client.get("/files/not-a-real-id-at-all/download")
    assert r.status_code == 404
    print("[PASS] a genuinely nonexistent file_id also gets 404 -- identical to the unauthorized case")

    with open(storage_path, "r+b") as f:
        data = bytearray(f.read())
        data[10] ^= 0xFF
        f.seek(0)
        f.write(bytes(data))

    r = client.get(f"/files/{file_id}/download")
    assert r.status_code == 500
    assert "corrupted" in r.json()["detail"].lower() or "could not be decrypted" in r.json()["detail"].lower()
    print("[PASS] tampered on-disk ciphertext is detected on download attempt, clean error returned (not corrupted data)")

    print("\nALL PHASE 5 HTTP CHECKS PASSED")
    shutil.rmtree(TEST_STORAGE_DIR, ignore_errors=True)


if __name__ == "__main__":
    run()
