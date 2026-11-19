# AgriSmart AI — ML Bakeoff Project Blueprint

## Project objective
Build a smart-agriculture decision-support prototype with three independently trained applications:
1. Crop recommendation (multiclass classification)
2. Crop yield estimation (regression)
3. Plant disease recognition (image classification with transfer learning)

This is a research/educational prototype. Outputs are estimates and must not be treated as agronomic guarantees or treatment prescriptions.

## Architecture

```text
                    AgriSmart AI / Streamlit UI
                               |
           +-------------------+-------------------+
           |                   |                   |
     Crop recommendation  Crop yield prediction  Disease detection
       classification        regression             CNN
           |                   |                   |
     Crop dataset          Yield dataset       Leaf image dataset
           |                   |                   |
     Preprocessing         Preprocessing        Resize / augment
     Imputation            Imputation           Transfer learning
     Scaling               Encoding             MobileNetV2
           |                   |                   |
     Model comparison      Model comparison     Validation metrics
           +-------------------+-------------------+
                               |
                    Saved models and reports
```

## Public datasets

### 1. Crop recommendation
Suggested public dataset: https://www.kaggle.com/datasets/varshitanalluri/crop-recommendation-dataset
Expected common columns: `N`, `P`, `K`, `temperature`, `humidity`, `ph`, `rainfall`, `label`.
Place the CSV at `data/crop_recommendation/Crop_recommendation.csv`.

### 2. Crop yield
Suggested public dataset: https://www.kaggle.com/datasets/patelris/crop-yield-prediction-dataset
Expected common columns: `Area`, `Item`, `Year`, `average_rain_fall_mm_per_year`, `pesticides_tonnes`, `avg_temp`, `hg/ha_yield`.
Place the CSV at `data/yield/crop_yield.csv`.
Advanced benchmark alternative: https://cybench.agml.org/ . It needs a dataset-specific data adapter; the included yield trainer expects the simpler CSV schema above.

### 3. Plant disease
Suggested dataset: PlantVillage https://github.com/spMohanty/PlantVillage-Dataset
Arrange images into class subfolders under `data/plant_disease/`, for example:

```text
data/plant_disease/
  Tomato___Early_blight/
    image001.jpg
  Tomato___Late_blight/
    image002.jpg
  Tomato___healthy/
    image003.jpg
```

PlantVillage is predominantly controlled/lab imagery. For stronger external validation, test on separate field images such as PlantDoc: https://github.com/pratikkayal/PlantDoc-Dataset . Review dataset licences and usage terms before redistribution or commercial use.

## Models to compare

| Task | Candidate models |
|---|---|
| Crop recommendation | Logistic Regression, KNN, SVM, Decision Tree, Random Forest, Extra Trees, XGBoost |
| Crop yield | Linear Regression, Ridge, Decision Tree, Random Forest, Extra Trees, XGBoost |
| Disease images | Custom CNN, MobileNetV2, EfficientNetB0 |

Included starter trainers currently implement Random Forest, Extra Trees, SVM, HistGradientBoosting for crop classification; Random Forest, Extra Trees and HistGradientBoosting for yield regression; and MobileNetV2 transfer learning for image classification. Extend these trainers for the full comparison before claiming those models were tested.

## Evaluation

- Classification: accuracy, macro precision, macro recall, macro F1, confusion matrix.
- Regression: MAE, RMSE, R², WAPE.
- Image model: validation accuracy/loss, macro F1, per-class recall and confusion matrix.
- Keep a final test set untouched. Use a chronological holdout for yield where years are available. Use plant/field/source grouping for images when metadata permits to reduce near-duplicate leakage.
- Save actual metrics from completed runs. Never invent or pre-fill scores.

## Implementation plan

1. Download the three datasets and verify their licences and schemas.
2. Place files in the specified `data/` folders.
3. Install dependencies from `requirements.txt` in a Python 3.10/3.11 virtual environment.
4. Run each trainer independently:

```bash
python src/train_crop.py
python src/train_yield.py
python src/train_disease.py
```

5. Inspect generated model files in `models/` and evaluation JSON files in `reports/`.
6. Launch the dashboard:

```bash
streamlit run app.py
```

7. Add the advanced improvements: Optuna tuning, XGBoost baselines, SHAP explanations for tabular models, Grad-CAM for image predictions, grouped image validation, and downloadable prediction reports.
8. Prepare the final report and presentation with dataset descriptions, EDA, methodology, model comparisons, limitations and real screenshots.

## Project files

- `app.py`: Streamlit application
- `requirements.txt`: Python dependencies
- `src/train_crop.py`: crop classifier training and evaluation
- `src/train_yield.py`: yield regression training and evaluation
- `src/train_disease.py`: MobileNetV2 image classifier training
- `src/common.py`: shared paths and metric helpers
- `README.md`: setup and execution instructions
- `PROJECT_BLUEPRINT.md`: this architecture, dataset and implementation guide
