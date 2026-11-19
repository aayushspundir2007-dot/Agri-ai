# AgriSmart AI — ML Bakeoff Starter

Three applications: crop recommendation, crop yield estimation, and plant disease image classification.

## Setup
Use Python 3.10 or 3.11:
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```
TensorFlow installation may vary by operating system/GPU.

## Dataset placement
1. Crop recommendation CSV: `data/crop_recommendation/Crop_recommendation.csv`
   Expected columns: `N,P,K,temperature,humidity,ph,rainfall,label`.
   Dataset: https://www.kaggle.com/datasets/varshitanalluri/crop-recommendation-dataset

2. Crop yield CSV: `data/yield/crop_yield.csv`
   Expected common columns: `Area,Item,Year,average_rain_fall_mm_per_year,pesticides_tonnes,avg_temp,hg/ha_yield`.
   Dataset: https://www.kaggle.com/datasets/patelris/crop-yield-prediction-dataset
   Advanced benchmark: https://cybench.agml.org/ (requires its own data adapter; this starter script is for the simpler CSV schema).

3. Plant disease images: arrange into class folders:
```
data/plant_disease/Tomato___Early_blight/*.jpg
data/plant_disease/Tomato___Late_blight/*.jpg
data/plant_disease/Tomato___healthy/*.jpg
```
PlantVillage has 54,306 images; check source licence and terms. It contains controlled/lab images, so do not claim field performance without field-image testing.

## Train and run
```bash
python src/train_crop.py
python src/train_yield.py
python src/train_disease.py
streamlit run app.py
```

## Evaluation protocol
- Classification: accuracy, macro precision/recall/F1, confusion matrix.
- Regression: MAE, RMSE, R², WAPE; use chronological holdout when year is available.
- Image classification: macro F1, per-class recall, confusion matrix; group by plant/field if metadata allows to prevent leakage.
- Keep the test set untouched. Fit preprocessing only on training data. Record actual metrics only; never invent results.
