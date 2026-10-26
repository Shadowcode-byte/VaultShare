"""
Confirms the validation service is actually wired correctly behind
auth at the HTTP layer, not just correct in isolation.
Run with: python test_phase4_http.py
"""
import os

os.environ["DATABASE_URL"] = "sqlite:///./test_phase4_http.db"
if os.path.exists("test_phase4_http.db"):
    os.remove("test_phase4_http.db")

from fastapi.testclient import TestClient  # noqa: E402

from app.db.base import Base  # noqa: E402
from app.db.session import engine  # noqa: E402
import app.models  # noqa: E402
from app.main import app  # noqa: E402

Base.metadata.create_all(engine)
client = TestClient(app)


def run():
    # 1. Anonymous request rejected before validation even runs
    r = client.post("/files/validate", files={"file": ("resume.pdf", b"%PDF-1.4\n" + b"x" * 100, "application/pdf")})
    assert r.status_code == 401
    print("[PASS] unauthenticated upload attempt rejected (401) before any validation runs")

    # 2. Register + login
    client.post("/auth/register", json={"name": "Kamal", "email": "kamal@upes.ac.in", "password": "a-long-enough-password"})
    r = client.post("/auth/login", json={"email": "kamal@upes.ac.in", "password": "a-long-enough-password"})
    assert r.status_code == 200

    # 3. Authenticated + valid file -> accepted
    r = client.post("/files/validate", files={"file": ("resume.pdf", b"%PDF-1.4\n" + b"x" * 100, "application/pdf")})
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "valid"
    print("[PASS] authenticated + valid PDF accepted")

    # 4. Authenticated but a spoofed extension -> rejected with 400, not 500
    r = client.post("/files/validate", files={"file": ("virus.pdf", b"MZ" + b"\x90" * 100, "application/pdf")})
    assert r.status_code == 400, r.text
    assert "does not match" in r.json()["detail"]
    print("[PASS] authenticated but content/extension mismatch rejected (400, clean error message)")

    print("\nALL PHASE 4 HTTP CHECKS PASSED")


if __name__ == "__main__":
    run()
