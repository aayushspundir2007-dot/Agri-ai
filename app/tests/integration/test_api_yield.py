"""Integration tests for POST /api/predict/yield."""
import pytest

pytestmark = pytest.mark.integration

ENDPOINT = "/api/predict/yield"
VALID = dict(area="India", item="Wheat", year=2010,
             rainfall=1083.0, pesticides=55000.0, temperature=24.0)


def test_yield_endpoint_returns_200(client, admin_headers):
    r = client.post(ENDPOINT, json=VALID, headers=admin_headers)
    assert r.status_code == 200

def test_yield_requires_auth(client):
    r = client.post(ENDPOINT, json=VALID)
    assert r.status_code in (401, 403)

def test_yield_returns_float(client, admin_headers):
    r = client.post(ENDPOINT, json=VALID, headers=admin_headers)
    assert isinstance(r.json()["yield_hgha"], float)

def test_yield_returns_positive_value(client, admin_headers):
    r = client.post(ENDPOINT, json=VALID, headers=admin_headers)
    assert r.json()["yield_hgha"] > 0

def test_yield_response_echoes_inputs(client, admin_headers):
    r = client.post(ENDPOINT, json=VALID, headers=admin_headers)
    d = r.json()
    assert d["area"] == "India"
    assert d["item"] == "Wheat"
    assert d["year"] == 2010

def test_unknown_country_still_returns_value(client, admin_headers):
    payload = {**VALID, "area": "Narnia"}
    r = client.post(ENDPOINT, json=payload, headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["yield_hgha"] > 0

def test_missing_area_returns_422(client, admin_headers):
    bad = {k: v for k, v in VALID.items() if k != "area"}
    r = client.post(ENDPOINT, json=bad, headers=admin_headers)
    assert r.status_code == 422

def test_year_out_of_range_returns_422(client, admin_headers):
    bad = {**VALID, "year": 1800}
    r = client.post(ENDPOINT, json=bad, headers=admin_headers)
    assert r.status_code == 422

def test_response_has_model_field(client, admin_headers):
    r = client.post(ENDPOINT, json=VALID, headers=admin_headers)
    assert r.json()["model"] == "ExtraTrees"
