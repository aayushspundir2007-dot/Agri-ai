"""Integration tests for POST /api/predict/crop."""
import pytest

pytestmark = pytest.mark.integration

ENDPOINT = "/api/predict/crop"
VALID = dict(N=90, P=42, K=43, temperature=25.0, humidity=80.0, ph=6.5, rainfall=100.0)


def test_crop_endpoint_returns_200(client, admin_headers):
    r = client.post(ENDPOINT, json=VALID, headers=admin_headers)
    assert r.status_code == 200

def test_crop_endpoint_requires_auth(client):
    r = client.post(ENDPOINT, json=VALID)
    assert r.status_code in (401, 403)

def test_crop_probabilities_top5_are_valid(client, admin_headers):
    r = client.post(ENDPOINT, json=VALID, headers=admin_headers)
    probs = r.json()["probabilities"]
    assert all(0 <= v <= 1 for v in probs.values())
    assert sum(probs.values()) <= 1.0 + 1e-5

def test_crop_response_has_crop_field(client, admin_headers):
    r = client.post(ENDPOINT, json=VALID, headers=admin_headers)
    assert "crop" in r.json()

def test_crop_response_has_probabilities(client, admin_headers):
    r = client.post(ENDPOINT, json=VALID, headers=admin_headers)
    assert "probabilities" in r.json()
    assert isinstance(r.json()["probabilities"], dict)

def test_crop_response_has_model_field(client, admin_headers):
    r = client.post(ENDPOINT, json=VALID, headers=admin_headers)
    assert r.json()["model"] == "RandomForest"

def test_missing_field_returns_422(client, admin_headers):
    bad = {k: v for k, v in VALID.items() if k != "rainfall"}
    r = client.post(ENDPOINT, json=bad, headers=admin_headers)
    assert r.status_code == 422

def test_out_of_range_nitrogen_returns_422(client, admin_headers):
    bad = {**VALID, "N": 999}
    r = client.post(ENDPOINT, json=bad, headers=admin_headers)
    assert r.status_code == 422

def test_out_of_range_ph_returns_422(client, admin_headers):
    bad = {**VALID, "ph": 20.0}
    r = client.post(ENDPOINT, json=bad, headers=admin_headers)
    assert r.status_code == 422

def test_viewer_can_predict_crop(client, viewer_headers):
    r = client.post(ENDPOINT, json=VALID, headers=viewer_headers)
    assert r.status_code == 200
