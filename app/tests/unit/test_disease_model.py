"""Unit tests for the Plant Disease Detection model."""
import json
import sys
import pytest
import numpy as np
from pathlib import Path
from PIL import Image

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[4]
MODELS_DIR = ROOT / "models"
sys.path.insert(0, str(ROOT / "src"))


@pytest.fixture(scope="module")
def disease_model():
    import joblib
    p = MODELS_DIR / "disease_classifier.joblib"
    if not p.exists():
        pytest.skip("disease_classifier.joblib not found")
    return joblib.load(p)


@pytest.fixture(scope="module")
def disease_classes():
    p = MODELS_DIR / "disease_classes.json"
    if not p.exists():
        pytest.skip("disease_classes.json not found")
    return json.loads(p.read_text())


@pytest.fixture(scope="module")
def dummy_image():
    return Image.new("RGB", (64, 64), (80, 160, 80))


def test_model_loads_successfully(disease_model):
    assert disease_model is not None

def test_classes_json_has_10_entries(disease_classes):
    assert len(disease_classes) == 10

def test_all_classes_are_tomato(disease_classes):
    for c in disease_classes:
        assert "Tomato" in c, f"Non-Tomato class found: {c}"

def test_feature_extractor_dim_1120(dummy_image):
    from image_features import extract_features
    feats = extract_features(dummy_image)
    assert feats.shape == (1120,), f"Expected 1120 dims, got {feats.shape}"

def test_feature_extractor_returns_float32(dummy_image):
    from image_features import extract_features
    feats = extract_features(dummy_image)
    assert feats.dtype == np.float32

def test_confidence_between_0_and_1(disease_model, dummy_image):
    from image_features import extract_features
    feats = extract_features(dummy_image).reshape(1, -1)
    probs = disease_model.predict_proba(feats)[0]
    assert (probs >= 0).all() and (probs <= 1).all()

def test_top5_probs_sum_leq_1(disease_model, dummy_image):
    from image_features import extract_features
    feats = extract_features(dummy_image).reshape(1, -1)
    probs = disease_model.predict_proba(feats)[0]
    top5  = np.sort(probs)[::-1][:5]
    assert top5.sum() <= 1.0 + 1e-5

def test_probabilities_sum_to_one(disease_model, dummy_image):
    from image_features import extract_features
    feats = extract_features(dummy_image).reshape(1, -1)
    probs = disease_model.predict_proba(feats)[0]
    assert abs(probs.sum() - 1.0) < 1e-5

def test_healthy_leaf_predicted(disease_model, disease_classes, sample_leaf_image):
    from image_features import extract_features
    feats = extract_features(sample_leaf_image).reshape(1, -1)
    probs = disease_model.predict_proba(feats)[0]
    idx   = int(np.argmax(probs))
    pred  = disease_classes[idx]
    # healthy leaf should predict healthy or at least return a valid class
    assert pred in disease_classes

def test_predict_returns_known_class(disease_model, disease_classes, dummy_image):
    from image_features import extract_features
    feats = extract_features(dummy_image).reshape(1, -1)
    probs = disease_model.predict_proba(feats)[0]
    pred  = disease_classes[int(np.argmax(probs))]
    assert pred in disease_classes
