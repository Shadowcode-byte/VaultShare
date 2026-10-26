"""
Phase 3 integration test — exercises the actual HTTP layer (not just
the service functions) using FastAPI's TestClient, against a throwaway
SQLite DB. Run with: python test_phase3_auth.py
"""
import os

os.environ["DATABASE_URL"] = "sqlite:///./test_phase3.db"

if os.path.exists("test_phase3.db"):
    os.remove("test_phase3.db")

from fastapi.testclient import TestClient  # noqa: E402

from app.db.base import Base  # noqa: E402
from app.db.session import engine  # noqa: E402
import app.models  # noqa: E402
from app.main import app  # noqa: E402

Base.metadata.create_all(engine)
client = TestClient(app)

EMAIL = "kamal@upes.ac.in"
PASSWORD = "a-reasonably-long-password"


def run():
    r = client.post("/auth/register", json={"name": "Kamal", "email": EMAIL, "password": PASSWORD})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["role"] == "student", "registration must never allow role escalation"
    assert "password" not in body and "password_hash" not in body
    print("[PASS] register succeeds, role forced to student, password never returned")

    r = client.post("/auth/register", json={"name": "Fake", "email": EMAIL, "password": PASSWORD})
    assert r.status_code == 409, r.text
    print("[PASS] duplicate email registration rejected (409)")

    r = client.post(
        "/auth/register",
        json={"name": "Attacker", "email": "attacker@upes.ac.in", "password": PASSWORD, "role": "admin"},
    )
    assert r.status_code == 201
    assert r.json()["role"] == "student", "role field in payload must be silently ignored, not applied"
    print("[PASS] extra 'role':'admin' field in registration payload is ignored")

    r = client.post("/auth/register", json={"name": "Weak", "email": "weak@upes.ac.in", "password": "short"})
    assert r.status_code == 422
    print("[PASS] short password rejected by validation (422)")

    r = client.post("/auth/login", json={"email": EMAIL, "password": "wrong-password-entirely"})
    assert r.status_code == 401
    print("[PASS] wrong password rejected")

    r_unknown = client.post("/auth/login", json={"email": "nobody@upes.ac.in", "password": "whatever123"})
    r_wrongpw = client.post("/auth/login", json={"email": EMAIL, "password": "whatever123wrong"})
    assert r_unknown.status_code == r_wrongpw.status_code == 401
    assert r_unknown.json()["detail"] == r_wrongpw.json()["detail"]
    print("[PASS] unknown-email and wrong-password return identical status+message")

    r = client.post("/auth/login", json={"email": EMAIL, "password": PASSWORD})
    assert r.status_code == 200, r.text
    cookie_names = [c for c in client.cookies.keys()]
    assert "vaultshare_session" in cookie_names
    print("[PASS] correct login succeeds and sets session cookie")

    r = client.get("/auth/me")
    assert r.status_code == 200
    assert r.json()["email"] == EMAIL
    print("[PASS] /auth/me returns the logged-in user")

    r = client.get("/auth/me", headers={"Cookie": ""})
    assert r.status_code == 401
    print("[PASS] request without session cookie is rejected (401)")

    stolen_cookie_value = client.cookies.get("vaultshare_session")
    r = client.post("/auth/logout")
    assert r.status_code == 204

    r = client.get("/auth/me", cookies={"vaultshare_session": stolen_cookie_value})
    assert r.status_code == 401
    print("[PASS] logout revokes the session server-side; a replayed old cookie is rejected")

    print("\nALL PHASE 3 AUTH CHECKS PASSED")


if __name__ == "__main__":
    run()
