"""Unit tests for JWT auth and password hashing."""
import time
import pytest
from jose import JWTError

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _patch_users(temp_users_file):
    """Ensure every test in this module uses temp users."""
    pass


# ── Password hashing ─────────────────────────────────────────────
def test_hash_is_sha256_crypt():
    from app.core.security import hash_password
    h = hash_password("secret")
    assert h.startswith("$5$")

def test_verify_sha256_crypt_password():
    from app.core.security import hash_password, verify_password
    h = hash_password("mypassword")
    assert verify_password("mypassword", h) is True

def test_reject_wrong_sha256_crypt_password():
    from app.core.security import hash_password, verify_password
    h = hash_password("correct")
    assert verify_password("wrong", h) is False

def test_verify_legacy_sha256_hash():
    """Legacy users.json uses SHA-256 — must still work."""
    import hashlib
    from app.core.security import verify_password
    h = hashlib.sha256("admin123".encode()).hexdigest()
    assert verify_password("admin123", h) is True

def test_reject_wrong_sha256_password():
    import hashlib
    from app.core.security import verify_password
    h = hashlib.sha256("correct".encode()).hexdigest()
    assert verify_password("wrong", h) is False


# ── JWT creation & decoding ──────────────────────────────────────
def test_create_and_decode_token():
    from app.core.security import create_token, decode_token
    token = create_token({"sub": "alice", "role": "admin"})
    payload = decode_token(token)
    assert payload["sub"] == "alice"
    assert payload["role"] == "admin"

def test_token_contains_username():
    from app.core.security import create_token, decode_token
    token = create_token({"sub": "bob", "role": "viewer"})
    assert decode_token(token)["sub"] == "bob"

def test_token_has_expiry():
    from app.core.security import create_token, decode_token
    token = create_token({"sub": "alice"})
    payload = decode_token(token)
    assert "exp" in payload

def test_expired_token_rejected():
    from app.core.security import create_token, decode_token
    token = create_token({"sub": "alice"}, expires_hours=-1)
    with pytest.raises(JWTError):
        decode_token(token)

def test_tampered_token_rejected():
    from app.core.security import create_token, decode_token
    token = create_token({"sub": "alice"}) + "tampered"
    with pytest.raises(JWTError):
        decode_token(token)

def test_admin_role_in_token():
    from app.core.security import create_token, decode_token
    token = create_token({"sub": "admin", "role": "admin"})
    assert decode_token(token)["role"] == "admin"

def test_viewer_role_in_token():
    from app.core.security import create_token, decode_token
    token = create_token({"sub": "farmer", "role": "viewer"})
    assert decode_token(token)["role"] == "viewer"


# ── Login endpoint via router ────────────────────────────────────
def test_valid_login_returns_token(client):
    resp = client.post("/api/auth/login",
                       json={"username": "admin", "password": "admin123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_invalid_password_returns_401(client):
    resp = client.post("/api/auth/login",
                       json={"username": "admin", "password": "wrongpass"})
    assert resp.status_code == 401

def test_unknown_user_returns_401(client):
    resp = client.post("/api/auth/login",
                       json={"username": "nobody", "password": "pass"})
    assert resp.status_code == 401

def test_login_response_has_role(client):
    resp = client.post("/api/auth/login",
                       json={"username": "admin", "password": "admin123"})
    assert resp.json()["role"] == "admin"

def test_viewer_login_returns_viewer_role(client):
    resp = client.post("/api/auth/login",
                       json={"username": "farmer", "password": "farmer123"})
    assert resp.json()["role"] == "viewer"
