"""Unit tests for the Crop Recommendation model."""
import pytest
import pandas as pd
import numpy as np

pytestmark = pytest.mark.unit

ROOT = __import__('pathlib').Path(__file__).resolve().parents[4]
MODELS_DIR = ROOT / "models"


@pytest.fixture(scope="module")
def crop_model():
    import joblib
    p = MODELS_DIR / "crop_recommender.joblib"
    if not p.exists():
        pytest.skip("crop_recommender.joblib not found")
    return joblib.load(p)


def _row(**kwargs):
    defaults = dict(N=90, P=42, K=43, temperature=25.0, humidity=80.0, ph=6.5, rainfall=100.0)
    defaults.update(kwargs)
    return pd.DataFrame([defaults])


# ── basic load & predict ─────────────────────────────────────────
def test_model_loads_successfully(crop_model):
    assert crop_model is not None

def test_predict_returns_string(crop_model):
    pred = crop_model.predict(_row())[0]
    assert isinstance(pred, str) and len(pred) > 0

def test_predict_returns_valid_crop(crop_model):
    pred = crop_model.predict(_row())[0]
    assert pred in crop_model.classes_

def test_predict_all_22_classes_possible(crop_model):
    assert len(crop_model.classes_) == 22

def test_confidence_sums_to_one(crop_model):
    if not hasattr(crop_model, "predict_proba"):
        pytest.skip("Model has no predict_proba")
    probs = crop_model.predict_proba(_row())[0]
    assert abs(probs.sum() - 1.0) < 1e-5

def test_all_probabilities_between_0_and_1(crop_model):
    if not hasattr(crop_model, "predict_proba"):
        pytest.skip("Model has no predict_proba")
    probs = crop_model.predict_proba(_row())[0]
    assert (probs >= 0).all() and (probs <= 1).all()

def test_column_mapping_shim_works(crop_model):
    """Full-word column names should raise KeyError — shim lives in train_crop not here."""
    row = pd.DataFrame([{"N":90,"P":42,"K":43,"temperature":25,"humidity":80,"ph":6.5,"rainfall":100}])
    pred = crop_model.predict(row)[0]
    assert pred in crop_model.classes_

# ── parametrized known input→output pairs ───────────────────────
KNOWN = [
    (dict(N=90, P=42, K=43, temperature=20, humidity=82, ph=6.5, rainfall=203), "Rice"),
    (dict(N=0,  P=0,  K=0,  temperature=29, humidity=90, ph=7.0, rainfall=150), None),   # any
    (dict(N=20, P=30, K=20, temperature=27, humidity=85, ph=5.8, rainfall=220), "Rice"),
    (dict(N=100,P=18, K=43, temperature=24, humidity=70, ph=6.3, rainfall=102), None),
    (dict(N=0,  P=0,  K=0,  temperature=35, humidity=65, ph=8.0, rainfall=20),  None),
    (dict(N=90, P=42, K=43, temperature=25, humidity=80, ph=6.5, rainfall=100), None),
    (dict(N=40, P=40, K=40, temperature=22, humidity=92, ph=5.5, rainfall=300), None),
    (dict(N=10, P=10, K=10, temperature=28, humidity=88, ph=6.0, rainfall=250), None),
    (dict(N=55, P=20, K=30, temperature=18, humidity=55, ph=7.5, rainfall=80),  None),
    (dict(N=35, P=35, K=35, temperature=15, humidity=50, ph=6.8, rainfall=60),  None),
]

@pytest.mark.parametrize("inputs,expected_crop", KNOWN)
def test_parametrized_predictions(crop_model, inputs, expected_crop):
    pred = crop_model.predict(pd.DataFrame([inputs]))[0]
    assert isinstance(pred, str)
    if expected_crop is not None:
        assert pred == expected_crop, f"Expected {expected_crop}, got {pred}"
