# Kaggle Challenge: Titanic - Machine Learning from Disaster

End-to-end solution for the Kaggle competition
[**Titanic - Machine Learning from Disaster**](https://www.kaggle.com/competitions/titanic),
a binary classification problem: predict whether a passenger survived the
Titanic shipwreck from attributes such as class, sex, age and fare.

## Project structure

```
kaggle_titanic_challenge/
├── data/
│   ├── prepare_data.py     # builds data/train.csv from the public Titanic dataset
│   └── train.csv           # 891 passengers x 10 columns
├── eda.py                  # exploratory data analysis (stats, missing values, outliers, plots)
├── benchmark.py            # preprocessing + training/tuning/evaluation of 5 models
├── figures/                # PNG plots produced by eda.py
├── benchmark_results.csv   # benchmark table produced by benchmark.py
└── benchmark_results.json  # same results with full hyperparameter grids
```

## 1. Dataset

The competition dataset (891 labeled passengers, 10 features after cleanup:
`pclass`, `sex`, `age`, `sibsp`, `parch`, `fare`, `embarked`, `deck`,
`alone`, target `survived`).

Run `python data/prepare_data.py` to (re)generate `data/train.csv`.

## 2 & 3. Exploration / EDA

`python eda.py` prints:
- shape, dtypes, descriptive statistics (numeric & categorical)
- missing-value counts (`deck` 688, `age` 177, `embarked` 2)
- outlier counts per numeric column via the IQR rule
- survival rates broken down by sex and passenger class

and saves plots to `figures/`:
- `survival_counts.png` — class balance of the target
- `age_distribution.png` — age histogram split by survival
- `fare_by_class.png` — fare distribution per passenger class (boxplot)
- `survival_by_class_sex.png` — survival rate by class and sex
- `correlation_heatmap.png` — correlation matrix of numeric features

**Key findings:**
- The target is moderately imbalanced (~38% survived).
- `deck` is missing for ~77% of passengers and is dropped; `age` (~20% missing)
  is imputed with the median; `embarked` (2 missing) with the mode.
- `fare` is heavily right-skewed with a long tail of high-fare outliers
  (first-class passengers).
- Strong survival signal from `sex` (74% women vs 19% men) and `pclass`
  (63% in 1st class vs 24% in 3rd class).

## 4. Preprocessing

Implemented with a `scikit-learn` `ColumnTransformer` inside a `Pipeline`
(see `benchmark.py`):
- Feature engineering: `family_size = sibsp + parch + 1`, `has_cabin` flag
  derived from `deck` (then `deck` itself is dropped).
- Numeric features (`age`, `fare`, `sibsp`, `parch`, `family_size`):
  median imputation + standard scaling.
- Categorical features (`pclass`, `sex`, `embarked`, `alone`, `has_cabin`):
  most-frequent imputation + one-hot encoding.
- Stratified 80/20 train/test split (`random_state=42`).

## 5. Models & benchmark

`python benchmark.py` trains and evaluates **five** classifiers:

| # | Model               | Library      |
|---|---------------------|--------------|
| 1 | Logistic Regression | scikit-learn |
| 2 | K-Nearest Neighbors | scikit-learn |
| 3 | Decision Tree       | scikit-learn |
| 4 | XGBoost             | xgboost      |
| 5 | LightGBM            | lightgbm     |

For each model:
1. **Baseline 5-fold stratified cross-validation** (`accuracy`, `f1`, `roc_auc`)
   on the training split to get an initial read on performance.
2. **Hyperparameter tuning** with `GridSearchCV` (5-fold CV, optimizing F1).
3. **Held-out evaluation** of the tuned model on the untouched 20% test split
   (`accuracy`, `precision`, `recall`, `f1`, `roc_auc`).

Results are written to `benchmark_results.csv` / `benchmark_results.json` and
printed as a ranked comparison table (sorted by held-out F1 score).

### Results

Held-out test set (20% stratified split), tuned models sorted by F1 score:

| Model               | CV Accuracy | CV F1  | CV ROC-AUC | Test Accuracy | Test Precision | Test Recall | Test F1 | Test ROC-AUC |
|---------------------|:-----------:|:------:|:----------:|:-------------:|:--------------:|:-----------:|:-------:|:------------:|
| Logistic Regression | 0.8076      | 0.7432 | 0.8610     | 0.8101        | 0.7869         | 0.6957      | **0.7385** | 0.8462    |
| LightGBM            | 0.8132      | 0.7496 | 0.8755     | 0.7877        | 0.7460         | 0.6812      | 0.7121     | 0.8160    |
| XGBoost             | 0.8062      | 0.7432 | 0.8752     | 0.7877        | 0.7541         | 0.6667      | 0.7077     | 0.8105    |
| K-Nearest Neighbors | 0.7936      | 0.7210 | 0.8358     | 0.7654        | 0.6957         | 0.6957      | 0.6957     | 0.8372    |
| Decision Tree       | 0.7781      | 0.7116 | 0.7675     | 0.7263        | 0.6613         | 0.5942      | 0.6260     | 0.7384    |

**Best model:** Logistic Regression — best held-out F1 (0.7385) and ROC-AUC
(0.8462), tuned to `C=0.1`. The boosted-tree models (LightGBM, XGBoost) reach
the highest cross-validated ROC-AUC (~0.875) but generalize slightly worse on
the held-out split, while the simpler linear model proves to be a strong,
well-calibrated baseline for this small, mostly-linearly-separable dataset.
The Decision Tree is the weakest model, as expected for a single unconstrained
tree on tabular data of this size.

Full comparison table — including best hyperparameters from `GridSearchCV` and
training/tuning times — is available in
[`benchmark_results.csv`](benchmark_results.csv) /
[`benchmark_results.json`](benchmark_results.json).

## How to reproduce

```bash
pip install scikit-learn pandas numpy matplotlib seaborn xgboost lightgbm
cd kaggle_titanic_challenge
python data/prepare_data.py
python eda.py
python benchmark.py
```
