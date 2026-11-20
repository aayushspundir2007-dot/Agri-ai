"""Integration tests for POST /api/predict/disease."""
import io
import pytest
from PIL import Image

pytestmark = pytest.mark.integration

ENDPOINT = "/api/predict/disease"


def _image_file(image: Image.Image, fmt="JPEG"):
    buf = io.BytesIO()
    image.save(buf, format=fmt)
    buf.seek(0)
    return ("leaf.jpg", buf, "image/jpeg")


def test_disease_endpoint_returns_200(client, admin_headers, sample_leaf_image):
    r = client.post(ENDPOINT,
                    files={"file": _image_file(sample_leaf_image)},
                    headers=admin_headers)
    assert r.status_code == 200

def test_disease_requires_auth(client, sample_leaf_image):
    r = client.post(ENDPOINT, files={"file": _image_file(sample_leaf_image)})
    assert r.status_code in (401, 403)

def test_disease_response_has_class_field(client, admin_headers, sample_leaf_image):
    r = client.post(ENDPOINT,
                    files={"file": _image_file(sample_leaf_image)},
                    headers=admin_headers)
    assert "predicted_class" in r.json()

def test_disease_response_has_confidence(client, admin_headers, sample_leaf_image):
    r = client.post(ENDPOINT,
                    files={"file": _image_file(sample_leaf_image)},
                    headers=admin_headers)
    conf = r.json()["confidence"]
    assert 0.0 <= conf <= 1.0

def test_disease_response_has_top5(client, admin_headers, sample_leaf_image):
    r = client.post(ENDPOINT,
                    files={"file": _image_file(sample_leaf_image)},
                    headers=admin_headers)
    top5 = r.json()["top5"]
    assert isinstance(top5, dict) and len(top5) >= 1

def test_disease_response_has_model_field(client, admin_headers, sample_leaf_image):
    r = client.post(ENDPOINT,
                    files={"file": _image_file(sample_leaf_image)},
                    headers=admin_headers)
    assert r.json()["model"] == "HistGradientBoosting"

def test_non_image_file_returns_422(client, admin_headers):
    bad = io.BytesIO(b"this is not an image")
    r = client.post(ENDPOINT,
                    files={"file": ("test.txt", bad, "text/plain")},
                    headers=admin_headers)
    assert r.status_code == 422

def test_png_image_accepted(client, admin_headers):
    img = Image.new("RGB", (64, 64), (100, 180, 100))
    buf = io.BytesIO(); img.save(buf, format="PNG"); buf.seek(0)
    r = client.post(ENDPOINT,
                    files={"file": ("leaf.png", buf, "image/png")},
                    headers=admin_headers)
    assert r.status_code == 200
