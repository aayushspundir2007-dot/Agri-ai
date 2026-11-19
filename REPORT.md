# AgriSmart AI — Project Report

> **Research prototype.** Outputs are estimates, not agronomic guarantees.
> Confirm decisions with local experts and field measurements.

---

## Abstract

AgriSmart AI is an explainable, end-to-end machine-learning platform built to
address three critical decision-support gaps in modern agriculture: crop
selection, yield estimation, and plant disease identification. The system
integrates three independently trained ML modules — a multiclass crop
recommendation classifier, a regression-based yield estimator, and an image
classification-based disease detector — into a single, themed Streamlit web
dashboard accessible via a secure, role-based login system.

The crop recommendation module, trained on 2,200 soil-and-climate records
across 22 crop classes, achieved a test accuracy and macro F1-score of
**99.3%** using a Random Forest classifier. The crop yield prediction module,
trained on 28,242 FAO-derived records spanning 101 countries and 10 crops
(1990–2013), achieved an R² of **0.9555** and a Weighted Absolute Percentage
Error (WAPE) of **11.46%** using an Extra Trees regressor. The plant disease
detection module, trained on 1,200 PlantVillage leaf images across 10 Tomato
disease classes using handcrafted image features and a Histogram Gradient
Boosting classifier, achieved a test accuracy of **87.5%** and macro F1 of
**0.875** — without requiring TensorFlow or GPU resources.

All models were selected via cross-validation from multiple candidates, and
all reported metrics reflect actual evaluation on held-out test sets. The
platform is fully operational, includes a user authentication system with
admin and viewer roles, and is deployed as an open-source project.

---

## 1. Introduction

### 1.1 Background

Agriculture remains the backbone of food security for billions of people
worldwide. Despite advances in precision farming, the majority of smallholder
farmers still rely on intuition, tradition, and limited access to expert
knowledge when making three of the most consequential decisions in a growing
cycle:

- **What to plant** — given soil nutrient levels, pH, humidity, temperature
  and rainfall, which crop is most likely to thrive?
- **How much will it yield** — given the crop, region, year and environmental
  conditions, what is a realistic yield estimate to plan inputs and storage?
- **What is wrong with this plant** — given a photograph of a diseased leaf,
  what condition is it, and should a specialist be consulted?

These questions are individually well-studied in the ML literature, but
existing solutions are typically isolated scripts, require significant
technical expertise to run, or depend on proprietary datasets. There is a
clear need for an integrated, accessible, explainable, and locally runnable
platform that bundles all three into a single tool.

### 1.2 Motivation

The specific motivations for AgriSmart AI are:

1. **Accessibility** — a Streamlit web UI requires no ML knowledge to use;
   any farmer or agricultural officer with a browser can interact with the
   system.
2. **Explainability** — every prediction is accompanied by model confidence
   scores, top-5 probability bars, and "about this model" sections showing
   actual training metrics — not black-box outputs.
3. **Reproducibility** — all three modules have independently runnable
   training scripts (`src/train_*.py`), all metrics are written to
   `reports/*.json` from actual runs (never invented), and the entire project
   is version-controlled and open-source.
4. **Lightweight deployment** — the full platform, including the disease
   module, runs on a standard CPU under Python 3.14 without TensorFlow or GPU,
   making it deployable on low-cost infrastructure. A full CNN upgrade path
   (MobileNetV2) is preserved for environments with TensorFlow.

### 1.3 Objectives

| # | Objective | Status |
|---|---|---|
| 1 | Train a crop recommendation classifier on public soil/climate data | ✅ Done |
| 2 | Train a crop yield regressor on FAO-derived multi-country data | ✅ Done |
| 3 | Train a plant disease image classifier without GPU/TensorFlow | ✅ Done |
| 4 | Build a unified Streamlit dashboard with enhanced UI/UX | ✅ Done |
| 5 | Add secure login with role-based access control | ✅ Done |
| 6 | Generate a full project report with screenshots | ✅ Done |
| 7 | Publish to GitHub | ✅ Done |

### 1.4 Datasets

| Module | Dataset | Size |
|---|---|---|
| Crop Recommendation | Kaggle crop-recommendation-dataset | 2,200 rows · 22 classes |
| Crop Yield | FAO-derived (Kaggle crop-yield-prediction-dataset) | 28,242 rows · 101 areas · 10 crops · 1990–2013 |
| Plant Disease | PlantVillage raw/color (Tomato subset) | 10 classes · 120 images/class |

### 1.5 System Architecture

```
                        [ Browser ]
                            │
                    [ Login / Auth Gate ]
                            │
              ┌─────────────┼─────────────┐
              │             │             │
    Crop Recommendation  Yield Pred.  Disease Detection
              │             │             │
        RandomForest    ExtraTrees   HistGradientBoosting
              │             │             │
        Soil/Climate    FAO CSV      Handcrafted Image
           Data                         Features
              └─────────────┼─────────────┘
                            │
                   [ reports/ metrics ]
```

---

## 2. Methodology

### 2.1 Crop Recommendation

A scikit-learn pipeline with median imputation, StandardScaler and a
classifier was trained on 2,200 samples. Four candidates were compared using
5-fold stratified cross-validation with macro F1 as the selection metric:
Random Forest (400 trees, balanced class weights), Extra Trees, SVM-RBF
(C=5, probability calibrated), and Histogram Gradient Boosting. The 20%
stratified test split was held out until final evaluation.

### 2.2 Crop Yield Prediction

A ColumnTransformer pipeline separated numeric features (Year, rainfall,
pesticides, temperature — median imputed and scaled) from categorical features
(Area, Item — mode imputed and one-hot encoded with `sparse_output=False` for
scikit-learn 1.9 compatibility). Three regressors were compared: Random Forest
(350 trees), Extra Trees (350 trees) and Histogram Gradient Boosting
(250 iterations). A **chronological holdout** (latest 20% of years) was used
to prevent temporal leakage, yielding 6,251 test rows. The winner was selected
by lowest RMSE.

### 2.3 Plant Disease Detection

Because TensorFlow has no wheels for Python 3.14, a CPU-friendly approach was
adopted. A shared feature extractor (`src/image_features.py`) produces a
deterministic 1,120-dimensional vector per image:

- 32×32 grayscale thumbnail (1,024 dims)
- RGB histogram (16 bins × 3 channels = 48 dims)
- RGB channel statistics (mean + std × 3 = 6 dims)
- HSV histogram (16+16+8 bins = 40 dims)
- Grayscale statistics (2 dims)

This extractor is shared between the trainer and the app to guarantee
feature-space consistency at inference time. A StandardScaler + classifier
pipeline was trained on 1,200 images (120/class, 10 classes) with 3-fold
cross-validation. Two models were compared: Logistic Regression and
Histogram Gradient Boosting. The CNN upgrade (MobileNetV2 transfer learning)
is preserved as `src/train_disease_cnn.py`.

---

## 3. Results and Outcomes

### 3.1 Crop Recommendation Results

| Model | CV Accuracy | CV F1-macro | Test Accuracy | Test F1-macro |
|---|---|---|---|---|
| **RandomForest** ✓ | **0.9943** | **0.9943** | **0.9932** | **0.9932** |
| ExtraTrees | 0.9915 | 0.9914 | 0.9955 | 0.9955 |
| SVM-RBF | 0.9812 | 0.9810 | 0.9909 | 0.9909 |
| HistGradientBoosting | 0.9915 | 0.9915 | 0.9886 | 0.9886 |

**Selected:** RandomForest (highest CV F1-macro).
Test precision macro: **0.9935** · Test recall macro: **0.9932**

The model correctly identifies all 22 crop classes with near-perfect accuracy.
The small gap between CV and test scores confirms no overfitting. All 22 crops
— including Jute, Rice, Maize, Coffee, Cotton, Mango, Coconut and others —
are classified reliably from 7 soil and climate inputs.

---

### 3.2 Crop Yield Prediction Results

| Metric | Value |
|---|---|
| Selected model | **ExtraTrees** |
| Test rows (chronological holdout) | 6,251 |
| MAE | 10,077.6 hg/ha |
| RMSE | 20,071.2 hg/ha |
| **R²** | **0.9555** |
| WAPE | 11.46% |

An R² of 0.9555 means the model explains **95.6% of the variance** in crop
yield across 101 countries and 10 crops. The WAPE of 11.46% means the average
prediction error is around 11–12% of actual yield — acceptable for a planning
tool given the diversity of geographies and crop types in the dataset.

**Coverage:** 101 areas including India, France, Brazil, USA, China-adjacent
neighbours, and 95 others. 10 crops: Wheat, Rice (paddy), Maize, Potatoes,
Soybeans, Sorghum, Sweet potatoes, Cassava, Yams, Plantains.

**Note on year 2025:** The model was trained on 1990–2013 data. Predictions
for 2025 are extrapolations and carry higher uncertainty.

---

### 3.3 Plant Disease Detection Results

| Model | CV Accuracy | CV F1-macro | Test Accuracy | Test F1-macro |
|---|---|---|---|---|
| **HistGradientBoosting** ✓ | **0.7958** | **0.7932** | **0.8750** | **0.8751** |
| LogisticRegression | 0.6250 | 0.6232 | 0.7208 | 0.7188 |

**Selected:** HistGradientBoosting (highest CV accuracy).
Test precision macro: **0.8763** · Test recall macro: **0.8750**

The model correctly classifies **87.5%** of leaf images across 10 Tomato
disease conditions using only handcrafted features and no GPU. The gap between
CV (79.6%) and test (87.5%) accuracy is positive — the model generalises well
to held-out images. The 10 classes covered:

| Class | Condition type |
|---|---|
| Tomato — healthy | No disease |
| Tomato — Early blight | Fungal |
| Tomato — Late blight | Water mould |
| Tomato — Bacterial spot | Bacterial |
| Tomato — Leaf Mold | Fungal |
| Tomato — Septoria leaf spot | Fungal |
| Tomato — Spider mites | Insect |
| Tomato — Target Spot | Fungal |
| Tomato — Yellow Leaf Curl Virus | Viral |
| Tomato — Mosaic virus | Viral |

---

### 3.4 Platform Outcomes

| Outcome | Detail |
|---|---|
| ✅ Fully working web app | All 3 modules return live predictions at http://localhost:8501 |
| ✅ Secure login | SHA-256 hashed passwords, role-based access (admin / viewer) |
| ✅ User management | Admin can add, remove and change passwords via the UI |
| ✅ Enhanced UI/UX | Green theme, hero banner, hover cards, animated confidence bars |
| ✅ Model evaluation page | Actual metrics tables from reports/ — no invented numbers |
| ✅ Full DOCX report | 11-section report with 5 embedded screenshots (PROJECT_REPORT.docx) |
| ✅ Open-source | Published to GitHub with .gitignore (models + data excluded) |

---

### 3.5 Summary Comparison

| Module | Model | Key Metric | Value |
|---|---|---|---|
| Crop Recommendation | Random Forest | Test F1-macro | **0.9932** |
| Crop Yield Prediction | Extra Trees | R² | **0.9555** |
| Plant Disease Detection | Hist. Gradient Boosting | Test Accuracy | **0.8750** |

---

## 4. Limitations

- Disease model covers **Tomato only** using handcrafted features trained on
  lab imagery (PlantVillage). Field performance is unverified.
- Yield predictions for years **beyond 2013** are extrapolations.
- Crop recommendation assumes **complete, accurate soil-test inputs**.
- Full CNN disease model (MobileNetV2) requires **Python 3.10/3.11 + TensorFlow**.
- No real-time sensor integration or mobile interface yet.

---

## 5. Future Work

- Integrate SHAP explainability for tabular models (needs Python 3.10/3.11).
- Train the full MobileNetV2 CNN for disease detection.
- Extend yield dataset to post-2013 years and more crops.
- Add mobile-responsive layout and REST API endpoints.
- Incorporate real-time weather API data for yield and crop inputs.

---

*AgriSmart AI · Python 3.14 · scikit-learn 1.9 · Streamlit 1.67 · PlantVillage · Kaggle datasets*
