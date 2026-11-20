"""Load all ML models once at startup and expose them as module-level singletons."""
import json
import sys
import time
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
from PIL import Image

from app.core.config import settings
from app.core.monitoring import monitor

sys.path.insert(0, str(settings.SRC_DIR))
from image_features import extract_features  # noqa: E402

class MLModels:
    crop_model   = None
    yield_model  = None
    disease_model= None
    disease_classes: list = []
    load_times:  dict = {}

    @classmethod
    def load_all(cls):
        t0 = time.time()
        # Crop
        p = settings.MODELS_DIR / "crop_recommender.joblib"
        if p.exists():
            ts = time.time(); cls.crop_model = joblib.load(p)
            cls.load_times["crop"] = round(time.time()-ts, 3)
        # Yield
        p = settings.MODELS_DIR / "yield_regressor.joblib"
        if p.exists():
            ts = time.time(); cls.yield_model = joblib.load(p)
            cls.load_times["yield"] = round(time.time()-ts, 3)
        # Disease
        p  = settings.MODELS_DIR / "disease_classifier.joblib"
        cp = settings.MODELS_DIR / "disease_classes.json"
        if p.exists() and cp.exists():
            ts = time.time(); cls.disease_model = joblib.load(p)
            cls.disease_classes = json.loads(cp.read_text())
            cls.load_times["disease"] = round(time.time()-ts, 3)
        cls.load_times["total"] = round(time.time()-t0, 3)
        monitor.log_startup(cls.load_times)

    @classmethod
    def models_loaded(cls) -> dict:
        return {
            "crop":    cls.crop_model is not None,
            "yield":   cls.yield_model is not None,
            "disease": cls.disease_model is not None,
        }

    @classmethod
    def predict_crop(cls, N, P, K, temperature, humidity, ph, rainfall):
        import pandas as pd
        row = pd.DataFrame([{
            "N": N, "P": P, "K": K,
            "temperature": temperature, "humidity": humidity,
            "ph": ph, "rainfall": rainfall
        }])
        pred = cls.crop_model.predict(row)[0]
        probs = {}
        if hasattr(cls.crop_model, "predict_proba"):
            p = cls.crop_model.predict_proba(row)[0]
            probs = {cls.crop_model.classes_[i]: round(float(p[i]), 4)
                     for i in np.argsort(p)[::-1][:5]}
        return pred, probs

    @classmethod
    def predict_yield(cls, area, item, year, rainfall, pesticides, temp):
        import pandas as pd
        row = pd.DataFrame([{
            "Area": area, "Item": item, "Year": year,
            "average_rain_fall_mm_per_year": rainfall,
            "pesticides_tonnes": pesticides, "avg_temp": temp
        }])
        return float(cls.yield_model.predict(row)[0])

    @classmethod
    def predict_disease(cls, image: Image.Image):
        feats = extract_features(image).reshape(1, -1)
        probs = cls.disease_model.predict_proba(feats)[0]
        idx   = int(np.argmax(probs))
        top5  = {cls.disease_classes[i]: round(float(probs[i]), 4)
                 for i in np.argsort(probs)[::-1][:5]}
        return cls.disease_classes[idx], round(float(probs[idx]), 4), top5

ml = MLModels()
