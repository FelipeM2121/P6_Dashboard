"""
Preprocessing, model training/evaluation and benchmark for the
Titanic - Machine Learning from Disaster Kaggle competition.

Trains and tunes 5 classifiers:
    - Logistic Regression
    - K-Nearest Neighbors
    - Decision Tree
    - XGBoost
    - LightGBM
"""
import json
import time

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_validate, train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier

RANDOM_STATE = 42

# ---------------------------------------------------------------------------
# 1. Load data and engineer a couple of light features
# ---------------------------------------------------------------------------
df = pd.read_csv("data/train.csv")

df["family_size"] = df["sibsp"] + df["parch"] + 1
df["has_cabin"] = df["deck"].notna().astype(int)
df = df.drop(columns=["deck"])  # too many missing values to be useful directly

X = df.drop(columns=["survived"])
y = df["survived"]

numeric_features = ["age", "fare", "sibsp", "parch", "family_size"]
categorical_features = ["pclass", "sex", "embarked", "alone", "has_cabin"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE
)

# ---------------------------------------------------------------------------
# 2. Preprocessing pipeline: impute missing values, scale numeric, one-hot encode categorical
# ---------------------------------------------------------------------------
numeric_transformer = Pipeline(steps=[
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler()),
])

categorical_transformer = Pipeline(steps=[
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("onehot", OneHotEncoder(handle_unknown="ignore")),
])

preprocessor = ColumnTransformer(transformers=[
    ("num", numeric_transformer, numeric_features),
    ("cat", categorical_transformer, categorical_features),
])

# ---------------------------------------------------------------------------
# 3. Models + hyperparameter grids for tuning
# ---------------------------------------------------------------------------
models = {
    "Logistic Regression": (
        LogisticRegression(max_iter=1000, random_state=RANDOM_STATE),
        {"clf__C": [0.01, 0.1, 1, 10], "clf__penalty": ["l2"]},
    ),
    "K-Nearest Neighbors": (
        KNeighborsClassifier(),
        {"clf__n_neighbors": [3, 5, 7, 11], "clf__weights": ["uniform", "distance"]},
    ),
    "Decision Tree": (
        DecisionTreeClassifier(random_state=RANDOM_STATE),
        {"clf__max_depth": [3, 5, 7, None], "clf__min_samples_leaf": [1, 5, 10]},
    ),
    "XGBoost": (
        XGBClassifier(
            random_state=RANDOM_STATE, eval_metric="logloss", verbosity=0
        ),
        {"clf__n_estimators": [100, 300], "clf__max_depth": [3, 5], "clf__learning_rate": [0.05, 0.1]},
    ),
    "LightGBM": (
        LGBMClassifier(random_state=RANDOM_STATE, verbose=-1),
        {"clf__n_estimators": [100, 300], "clf__max_depth": [-1, 5], "clf__learning_rate": [0.05, 0.1]},
    ),
}

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
scoring = ["accuracy", "f1", "roc_auc"]

results = []
best_estimators = {}

for name, (estimator, param_grid) in models.items():
    pipeline = Pipeline(steps=[("preprocess", preprocessor), ("clf", estimator)])

    # Baseline cross-validation (no tuning)
    start = time.time()
    cv_scores = cross_validate(pipeline, X_train, y_train, cv=cv, scoring=scoring)
    baseline_time = time.time() - start

    # Hyperparameter tuning with GridSearchCV
    start = time.time()
    grid = GridSearchCV(pipeline, param_grid=param_grid, cv=cv, scoring="f1", n_jobs=-1)
    grid.fit(X_train, y_train)
    tuning_time = time.time() - start

    best_estimators[name] = grid.best_estimator_

    # Hold-out evaluation with the tuned model
    y_pred = grid.predict(X_test)
    y_proba = grid.predict_proba(X_test)[:, 1]

    results.append({
        "model": name,
        "cv_accuracy_mean": round(cv_scores["test_accuracy"].mean(), 4),
        "cv_accuracy_std": round(cv_scores["test_accuracy"].std(), 4),
        "cv_f1_mean": round(cv_scores["test_f1"].mean(), 4),
        "cv_roc_auc_mean": round(cv_scores["test_roc_auc"].mean(), 4),
        "best_params": grid.best_params_,
        "tuned_cv_f1": round(grid.best_score_, 4),
        "test_accuracy": round(accuracy_score(y_test, y_pred), 4),
        "test_precision": round(precision_score(y_test, y_pred), 4),
        "test_recall": round(recall_score(y_test, y_pred), 4),
        "test_f1": round(f1_score(y_test, y_pred), 4),
        "test_roc_auc": round(roc_auc_score(y_test, y_proba), 4),
        "baseline_cv_time_s": round(baseline_time, 2),
        "tuning_time_s": round(tuning_time, 2),
    })
    print(f"Done: {name}")

# ---------------------------------------------------------------------------
# 4. Benchmark summary
# ---------------------------------------------------------------------------
results_df = pd.DataFrame(results).sort_values("test_f1", ascending=False)
print("\n=== Benchmark results (sorted by held-out F1 score) ===")
print(results_df[[
    "model", "cv_accuracy_mean", "cv_f1_mean", "cv_roc_auc_mean",
    "test_accuracy", "test_precision", "test_recall", "test_f1", "test_roc_auc",
]].to_string(index=False))

results_df.to_csv("benchmark_results.csv", index=False)
with open("benchmark_results.json", "w") as f:
    json.dump(results, f, indent=2, default=str)

print("\nSaved benchmark_results.csv and benchmark_results.json")
print(f"\nBest model on held-out test set: {results_df.iloc[0]['model']} "
      f"(F1={results_df.iloc[0]['test_f1']}, ROC-AUC={results_df.iloc[0]['test_roc_auc']})")
