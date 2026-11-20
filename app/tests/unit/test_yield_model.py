"""Unit tests for the Crop Yield Prediction model."""
import pytest
import pandas as pd

pytestmark = pytest.mark.unit

ROOT = __import__('pathlib').Path(__file__).resolve().parents[4]
MODELS_DIR = ROOT / "models"


@pytest.fixture(scope="module")
def yield_model():
    import joblib
    p = MODELS_DIR / "yield_regressor.joblib"
    if not p.exists():
        pytest.skip("yield_regressor.joblib not found")
    return joblib.load(p)


def _row(**kwargs):
    defaults = dict(Area="India", Item="Wheat", Year=2010,
                    average_rain_fall_mm_per_year=1083.0,
                    pesticides_tonnes=55000.0, avg_temp=24.0)
    defaults.update(kwargs)
    return pd.DataFrame([defaults])


def test_model_loads_successfully(yield_model):
    assert yield_model is not None

def test_predict_returns_positive_value(yield_model):
    val = float(yield_model.predict(_row())[0])
    assert val > 0

def test_predict_returns_float(yield_model):
    val = yield_model.predict(_row())[0]
    assert isinstance(float(val), float)

def test_known_india_wheat_range(yield_model):
    val = float(yield_model.predict(_row(Area="India", Item="Wheat", Year=2010))[0])
    assert 10_000 < val < 50_000, f"India Wheat 2010 expected 10k–50k hg/ha, got {val:.0f}"

def test_known_france_maize_range(yield_model):
    val = float(yield_model.predict(_row(
        Area="France", Item="Maize", Year=2005,
        average_rain_fall_mm_per_year=640.0,
        pesticides_tonnes=90000.0, avg_temp=12.0))[0])
    assert 40_000 < val < 100_000, f"France Maize 2005 expected 40k–100k hg/ha, got {val:.0f}"

def test_sparse_input_handled(yield_model):
    """Ensure no sparse matrix error on prediction."""
    val = float(yield_model.predict(_row())[0])
    assert val > 0

def test_unknown_country_returns_value(yield_model):
    """Model should not crash on unseen category."""
    val = float(yield_model.predict(_row(Area="Atlantis", Item="Wheat"))[0])
    assert isinstance(val, float)

# ── parametrized pairs ───────────────────────────────────────────
KNOWN = [
    (dict(Area="India",  Item="Wheat",     Year=2010, average_rain_fall_mm_per_year=1083, pesticides_tonnes=55000, avg_temp=24), (10000, 50000)),
    (dict(Area="France", Item="Maize",     Year=2005, average_rain_fall_mm_per_year=640,  pesticides_tonnes=90000, avg_temp=12), (40000,100000)),
    (dict(Area="Brazil", Item="Soybeans",  Year=2000, average_rain_fall_mm_per_year=1800, pesticides_tonnes=40000, avg_temp=25), (5000,  50000)),
    (dict(Area="Germany",Item="Potatoes",  Year=2008, average_rain_fall_mm_per_year=700,  pesticides_tonnes=120000,avg_temp=10), (50000,400000)),
    (dict(Area="Kenya",  Item="Maize",     Year=2005, average_rain_fall_mm_per_year=900,  pesticides_tonnes=5000,  avg_temp=22), (1000,  40000)),
]

@pytest.mark.parametrize("inputs,expected_range", KNOWN)
def test_parametrized_yield(yield_model, inputs, expected_range):
    val = float(yield_model.predict(pd.DataFrame([inputs]))[0])
    lo, hi = expected_range
    assert lo < val < hi, f"Expected {lo}–{hi} hg/ha for {inputs['Area']}/{inputs['Item']}, got {val:.0f}"
