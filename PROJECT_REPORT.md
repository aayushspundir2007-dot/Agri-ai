# AgriSmart AI — Project Report

A research-grade, explainable decision-support prototype for sustainable
agriculture. It bundles three independently trained machine-learning
applications behind a single Streamlit dashboard:

1. **Crop Recommendation** — which crop to plant, from soil and climate.
2. **Crop Yield Prediction** — expected yield, from crop, region, year and environment.
3. **Plant Disease Detection** — likely disease, from a leaf image.

> This is a research/educational prototype. Outputs are estimates, not
> agronomic guarantees. Confirm decisions with local experts and field
> measurements.

---

## 1. Brief Description

AgriSmart AI is a Python + Streamlit web application that turns three public
agricultural datasets into three usable predictors. Each module is trained by
its own script (`src/train_crop.py`, `src/train_yield.py`,
`src/train_disease.py`), which compares a few candidate models with proper
cross-validation / chronological holdout, selects the best, saves it to
`models/`, and writes actual metrics to `reports/`. The `app.py` dashboard
loads those saved models and exposes a clean, themed UI for each task, plus a
Model Evaluation page that surfaces the recorded metrics.

The stack is deliberately lightweight and CPU-friendly: scikit-learn for the
tabular modules (crop, yield) and for the image module (disease), so the whole
project runs on a single Python interpreter without GPU/TensorFlow. A
TensorFlow/Keras CNN trainer is preserved separately
(`src/train_disease_cnn.py`) for users who want the higher-fidelity
MobileNetV2 model under Python 3.10/3.11.

---

## 2. Problem Statement

Smallholder and regional planners face three recurring, data-driven questions:

- **What should I plant here?** Soil nutrients (N, P, K), pH, temperature,
  humidity and rainfall vary by location and season, and choosing the wrong
  crop wastes a growing cycle. A recommendation model maps these measurable
  inputs to the crop most likely to thrive.
- **How much will it yield?** Expected yield drives input purchasing, storage
  and market planning. A regression model that uses crop type, country, year,
  rainfall, pesticide use and temperature can estimate yield (hg/ha) ahead of
  harvest.
- **What is wrong with this leaf?** Visual disease diagnosis requires
  expertise that is not always available. An image classifier can flag the
  likely disease class from a photo, prompting timely expert confirmation and
  treatment.

AgriSmart AI addresses all three with explainable, locally runnable models,
while being explicit about their limits: each is a decision-support aid, not a
replacement for agronomy.

---

## 3. Project Report

### 3.1 Datasets

| Module | Source | Size | Key fields |
|---|---|---|---|
| Crop Recommendation | Kaggle *crop-recommendation-dataset* | 2,200 rows, **22 crop classes** | `N, P, K, temperature, humidity, ph, rainfall` → `label` |
| Crop Yield | Kaggle *crop-yield-prediction-dataset* (FAO-derived) | 28,242 rows, **101 areas**, **10 crops**, **1990–2013** | `Area, Item, Year, average_rain_fall_mm_per_year, pesticides_tonnes, avg_temp` → `hg/ha_yield` |
| Plant Disease | PlantVillage (`raw/color`, Tomato subset) | **10 classes**, 120 images/class sampled → 1,200 images | leaf JPGs → class folders |

Notes on data preparation actually performed in this project:
- The local crop CSV used full-word column names
  (`Nitrogen, Phosphorus, Potassium, Temperature, Humidity, pH_Value, Rainfall, Crop`).
  `src/train_crop.py` was given a column-mapping shim so it trains without
  altering the original file.
- The yield CSV was not present in the project. It was sourced from a public
  GitHub mirror of the same Kaggle dataset
  ([MohabWafaie/Study-of-the-Effects-of-Climate-Change-on-Crop-Yields](https://github.com/MohabWafaie/Study-of-the-Effects-of-Climate-Change-on-Crop-Yields)),
  which has the identical 7-column schema, and placed at
  `data/yield/crop_yield.csv`. No data was fabricated.
- Disease images are read directly from `PlantVillage-Dataset-master/raw/color`
  (no need to copy ~54k files); a per-class cap keeps CPU training fast.

### 3.2 Methodology

**Crop Recommendation (multiclass classification)**
Pipeline: median imputation → `StandardScaler` → classifier. Models compared
with 5-fold stratified cross-validation (CV F1-macro as selection metric):
RandomForest, ExtraTrees, SVM-RBF, HistGradientBoosting. Selected:
**RandomForest**. Final test-set evaluation uses accuracy, macro
precision/recall/F1 and a confusion matrix.

**Crop Yield Prediction (regression)**
Pipeline: `ColumnTransformer` — numeric (median impute → `StandardScaler`) and
categorical (most-frequent impute → `OneHotEncoder(handle_unknown="ignore",
sparse_output=False)`) — then a regressor. A **chronological holdout** (latest
years reserved for testing) is used when years are available. Models compared:
RandomForest, ExtraTrees, HistGradientBoosting. Selected by RMSE:
**ExtraTrees**. Metrics: MAE, RMSE, R², WAPE.

> The `sparse_output=False` fix is required because scikit-learn 1.9 rejects
> sparse input at `HistGradientBoostingRegressor.fit`; it is a compatibility
> fix, not a modelling change.

**Plant Disease Detection (image classification)**
Because TensorFlow has no wheels for Python 3.14 and a CNN over 54k images is
impractical on CPU here, the active trainer uses a **CPU-friendly
scikit-learn** approach: a dependency-free handcrafted feature extractor
(`src/image_features.py`) producing a 1,120-dim vector (32×32 grayscale
thumbnail + RGB and HSV histograms + channel statistics), shared by trainer and
app so features match exactly. Pipeline: `StandardScaler` → classifier. Models
compared with 3-fold CV: LogisticRegression, HistGradientBoosting. Selected by
CV accuracy: **HistGradientBoosting**. The original
MobileNetV2 transfer-learning CNN is preserved as
`src/train_disease_cnn.py` for Python 3.10/3.11 + TensorFlow.

### 3.3 Results (actual, from completed runs)

| Module | Selected model | CV metric | Test metric |
|---|---|---|---|
| Crop Recommendation | RandomForest | CV accuracy **0.9943**, CV F1-macro **0.9943** | Test accuracy **0.9932**, Test F1-macro **0.9932** |
| Crop Yield | ExtraTrees | — (chronological holdout) | MAE **10,077.6**, RMSE **20,071.2**, R² **0.9555**, WAPE **11.46%** (6,251 test rows) |
| Plant Disease | HistGradientBoosting | CV accuracy **0.7958**, CV F1-macro **0.7932** | Test accuracy **0.8750**, Test F1-macro **0.8751** (10 Tomato classes) |

These figures are the real outputs written to `reports/`, not estimates.

### 3.4 Technology stack

- **Language/runtime:** Python 3.14 (works for the scikit-learn-based setup);
  Python 3.10/3.11 recommended for the full `requirements.txt` including
  TensorFlow.
- **ML:** scikit-learn 1.9, pandas, numpy, joblib.
- **Image features:** NumPy + Pillow only (no scikit-image/TensorFlow needed).
- **UI:** Streamlit 1.67, with a custom theme (`/.streamlit/config.toml`) and
  CSS for cards, confidence bars, hero banner and badges.
- **Not used on Python 3.14** (no wheels): TensorFlow, XGBoost, SHAP. They
  remain in `requirements.txt` for the Python 3.10/3.11 path.

### 3.5 Application & UX

`app.py` is a single-file Streamlit app with five pages:

- **Overview** — hero banner with live status pills, three hover-lift feature
  cards, a "How it works" callout.
- **Crop Recommendation** — soil/climate inputs in a card → primary button →
  large result card with the recommended crop and a top-5 animated confidence
  bar chart.
- **Crop Yield Prediction** — region/crop/year/environment inputs → predicted
  yield (hg/ha) in a styled result card. (Previously a "dataset needed" card;
  now functional.)
- **Plant Disease Detection** — drag-and-drop leaf uploader → preview + tips →
  predicted class with confidence and a top-5 confidence bar chart, plus a
  disclaimer.
- **Model Evaluation** — per-model metric tables, the selected model, and the
  full JSON reports.

Persistent sidebar elements: branding, navigation, and colour-coded
model-status badges (✓ Trained / Not trained), so the state of each module is
always visible.

### 3.6 How to run

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate   | macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt      # full (Python 3.10/3.11)
# On Python 3.14, install the core subset instead:
#   streamlit scikit-learn pandas numpy joblib matplotlib Pillow

python src/train_crop.py
python src/train_yield.py
python src/train_disease.py          # sklearn version (Python 3.14 OK)
# python src/train_disease_cnn.py     # CNN version (Python 3.10/3.11 + TensorFlow)

streamlit run app.py                  # http://localhost:8501
```

### 3.7 Project structure

```
app.py                         Streamlit dashboard (enhanced UI/UX)
.streamlit/config.toml         Theme (green palette, run-on-save)
requirements.txt               Dependencies
src/
  common.py                    Shared paths + metric helpers
  train_crop.py                Crop classifier (column-mapping shim)
  train_yield.py               Yield regressor (dense OneHotEncoder fix)
  train_disease.py             Disease classifier (sklearn, handcrafted features)
  train_disease_cnn.py         Disease classifier (MobileNetV2 CNN, TF, preserved)
  image_features.py            Shared image feature extractor
data/
  crop_recommendation/         Crop CSV
  yield/crop_yield.csv         Yield CSV (28,242 rows)
  plant_disease/               (image source lives in PlantVillage-Dataset-master/)
models/                        Saved .joblib models + disease_classes.json
reports/                       Per-model metrics JSON
PlantVillage-Dataset-master/   Plant disease image dataset (raw/color used)
```

### 3.8 Limitations & honest scope

- **Research prototype, not agronomic advice.** Predictions must be confirmed
  with local experts and field measurements.
- **Disease model is Tomato-only** and uses handcrafted features (not a
  lab-grade CNN); trained on a capped subset. PlantVillage is controlled/lab
  imagery, so field performance is unverified. The full CNN is available via
  `train_disease_cnn.py` on Python 3.11.
- **Yield model scope** is limited to 101 areas, 10 crops, 1990–2013.
  Predictions outside that geography/time range may be unreliable.
- **Crop recommendation** assumes idealized, complete soil/climate inputs;
  real farms need actual soil tests.
- **Python 3.14** cannot run TensorFlow/XGBoost/SHAP (no wheels); those are only
  available on the Python 3.10/3.11 path.

---

## 4. Summary

AgriSmart AI demonstrates an end-to-end, three-module agricultural
decision-support system: real public datasets, honest model comparison with
proper validation, saved artefacts with recorded metrics, and a polished
Streamlit interface. Crop recommendation (RandomForest, test F1 ≈ 0.99) and
yield estimation (ExtraTrees, R² ≈ 0.96) are strong tabular baselines; plant
disease detection (HistGradientBoosting, 87.5% test accuracy on 10 Tomato
classes) is a functional, CPU-friendly image classifier with a clear upgrade
path to a full CNN. All three modules are running and verified end-to-end.
