"""Train the Plant Disease classifier with a CPU-friendly scikit-learn model.

Why not the CNN (train_disease_cnn.py)? That needs TensorFlow, which has no
wheels for Python 3.14. This trainer uses handcrafted image features
(see image_features.py) + scikit-learn, so it runs on the same interpreter as
the Streamlit app (Python 3.14). It reads images straight from
PlantVillage/raw/color, so there is no need to copy ~54k files into
data/plant_disease.

By default it builds a focused "Tomato leaf disease" detector (the plant the
README uses as its example, and the richest in PlantVillage). Adjust
CLASS_PREFIX / PER_CLASS to change scope or training time.

    python src/train_disease.py
"""
import json
import sys
import time
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from PIL import Image, ImageFile
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import (accuracy_score, precision_recall_fscore_support,
                             classification_report, confusion_matrix)

from common import DATA, MODELS, REPORTS, ROOT, write_json
from image_features import extract_features

ImageFile.LOAD_TRUNCATED_IMAGES = True

PV_COLOR = ROOT / "PlantVillage-Dataset-master" / "raw" / "color"
CLASS_PREFIX = "Tomato___"   # train a focused Tomato leaf-disease detector
PER_CLASS = 120             # cap images per class to keep CPU training fast
SEED = 42


def _has_image_subdirs(folder):
    return [d for d in folder.iterdir() if d.is_dir() and any(d.glob("*.jp*"))]


def load_dataset(source, prefix=None, per_class=PER_CLASS):
    classes = sorted(d.name for d in source.iterdir() if d.is_dir())
    classes = [c for c in classes if any((source / c).glob("*.jp*"))]
    if prefix:
        classes = [c for c in classes if c.startswith(prefix)]
    if len(classes) < 2:
        raise ValueError(f"Need >=2 classes with images; found {len(classes)} under {source}")
    X, y = [], []
    for cls in classes:
        files = sorted((source / cls).glob("*.jp*"))[:per_class]
        for f in files:
            try:
                X.append(extract_features(Image.open(f)))
                y.append(cls)
            except Exception as e:  # skip unreadable / corrupt images
                print("skip", f, e)
    return np.asarray(X, dtype=np.float32), np.asarray(y), classes


def main():
    source = DATA / "plant_disease"
    arranged = _has_image_subdirs(source) if source.exists() else []
    t0 = time.time()
    if len(arranged) >= 2:
        print(f"Using arranged images in {source}")
        X, y, classes = load_dataset(source, prefix=None, per_class=PER_CLASS)
    elif PV_COLOR.exists():
        print(f"Using PlantVillage raw/color ({CLASS_PREFIX}* classes), capped at {PER_CLASS}/class")
        X, y, classes = load_dataset(PV_COLOR, prefix=CLASS_PREFIX, per_class=PER_CLASS)
    else:
        raise FileNotFoundError("No disease images found. Arrange class folders in data/plant_disease "
                                "or keep PlantVillage/raw/color present.")
    print(f"Loaded {len(X)} images across {len(classes)} classes (feature dim {X.shape[1]}) in {time.time()-t0:.1f}s")

    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=SEED, stratify=y)

    models = {
        "LogisticRegression": LogisticRegression(max_iter=2000, C=1.0, n_jobs=-1),
        "HistGradientBoosting": HistGradientBoostingClassifier(max_iter=150, learning_rate=0.1,
                                                               random_state=SEED),
    }
    cv = StratifiedKFold(3, shuffle=True, random_state=SEED)
    results, fitted = {}, {}
    for name, est in models.items():
        t1 = time.time()
        pipe = Pipeline([("scale", StandardScaler()), ("model", est)])
        scores = cross_validate(pipe, Xtr, ytr, cv=cv, scoring=["accuracy", "f1_macro"])
        pipe.fit(Xtr, ytr)
        pred = pipe.predict(Xte)
        print(f"  {name}: cv_acc={scores['test_accuracy'].mean():.3f} test_acc={accuracy_score(yte,pred):.3f} ({time.time()-t1:.1f}s)")
        pr, re, f1, _ = precision_recall_fscore_support(yte, pred, average="macro", zero_division=0)
        results[name] = {
            "cv_accuracy": float(scores["test_accuracy"].mean()),
            "cv_f1_macro": float(scores["test_f1_macro"].mean()),
            "test_accuracy": float(accuracy_score(yte, pred)),
            "test_precision_macro": float(pr),
            "test_recall_macro": float(re),
            "test_f1_macro": float(f1),
            "report": classification_report(yte, pred, output_dict=True, zero_division=0),
            "confusion_matrix": confusion_matrix(yte, pred, labels=classes).tolist(),
            "class_order": classes,
        }
        fitted[name] = pipe

    winner = max(results, key=lambda k: results[k]["cv_accuracy"])
    joblib.dump(fitted[winner], MODELS / "disease_classifier.joblib")
    (MODELS / "disease_classes.json").write_text(json.dumps(classes, indent=2))
    write_json(REPORTS / "disease_metrics.json", {
        "winner": winner, "models": results, "classes": classes,
        "source": str(source if len(arranged) >= 2 else PV_COLOR),
        "per_class_cap": PER_CLASS, "feature_dim": int(X.shape[1]),
        "note": ("CPU-friendly handcrafted features (grayscale thumbnail + RGB/HSV histograms + stats). "
                 "CNN variant (train_disease_cnn.py) needs TensorFlow + Python 3.10/3.11."),
    })
    print("\nSelected:", winner)
    print(pd.DataFrame(results).T[["cv_accuracy", "cv_f1_macro", "test_accuracy", "test_f1_macro"]])
    print("Total time: %.1fs" % (time.time() - t0))


if __name__ == "__main__":
    sys.exit(main())
