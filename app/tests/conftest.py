"""Shared pytest fixtures for unit, integration and e2e tests."""
import io
import json
import shutil
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from PIL import Image

# ── paths ────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[3]
MODELS_DIR  = ROOT / "models"
REPORTS_DIR = ROOT / "reports"
SRC_DIR     = ROOT / "src"
PV_COLOR    = ROOT / "PlantVillage-Dataset-master" / "raw" / "color"


# ── temp users.json fixture ───────────────────────────────────────
@pytest.fixture()
def temp_users_file(tmp_path, monkeypatch):
    """Create a temporary users.json with known test credentials."""
    import hashlib
    def h(pw): return hashlib.sha256(pw.encode()).hexdigest()
    users = {
        "admin":  {"password": h("admin123"),  "role": "admin",  "name": "Admin User"},
        "farmer": {"password": h("farmer123"), "role": "viewer", "name": "Farm User"},
        "demo":   {"password": h("demo123"),   "role": "viewer", "name": "Demo Guest"},
    }
    f = tmp_path / "users.json"
    f.write_text(json.dumps(users))
    monkeypatch.setattr("app.core.config.settings.USERS_FILE", f)
    monkeypatch.setattr("app.routers.auth.settings.USERS_FILE", f)
    monkeypatch.setattr("app.routers.users.settings.USERS_FILE", f)
    return f


# ── FastAPI test client ───────────────────────────────────────────
@pytest.fixture(scope="session")
def app_client():
    """Session-scoped TestClient — models loaded once."""
    from app.main import app
    from app.core.ml_loader import ml
    ml.load_all()
    with TestClient(app) as client:
        yield client


@pytest.fixture()
def client(app_client, temp_users_file):
    """Per-test client with fresh temp users file."""
    return app_client


# ── Auth token fixtures ───────────────────────────────────────────
@pytest.fixture()
def admin_token(client):
    resp = client.post("/api/auth/login",
                       json={"username": "admin", "password": "admin123"})
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()["access_token"]


@pytest.fixture()
def viewer_token(client):
    resp = client.post("/api/auth/login",
                       json={"username": "farmer", "password": "farmer123"})
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest.fixture()
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture()
def viewer_headers(viewer_token):
    return {"Authorization": f"Bearer {viewer_token}"}


# ── Sample leaf image fixture ────────────────────────────────────
@pytest.fixture(scope="session")
def sample_leaf_path():
    """Return path to a real PlantVillage leaf image if available,
    otherwise create a synthetic green-ish image."""
    folder = PV_COLOR / "Tomato___healthy"
    if folder.exists():
        jpgs = sorted(folder.glob("*.jp*"))
        if jpgs:
            return jpgs[0]
    # fallback: synthetic 64×64 green image
    img = Image.new("RGB", (64, 64), (80, 160, 80))
    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    img.save(tmp.name)
    return Path(tmp.name)


@pytest.fixture(scope="session")
def sample_leaf_bytes(sample_leaf_path):
    return sample_leaf_path.read_bytes()


@pytest.fixture(scope="session")
def sample_leaf_image(sample_leaf_path):
    return Image.open(sample_leaf_path).convert("RGB")
