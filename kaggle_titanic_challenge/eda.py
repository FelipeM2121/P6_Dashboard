"""Exploratory Data Analysis for the Titanic - Machine Learning from Disaster dataset."""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import os

OUT_DIR = "figures"
os.makedirs(OUT_DIR, exist_ok=True)

df = pd.read_csv("data/train.csv")

print("=== Shape ===")
print(df.shape)

print("\n=== Dtypes ===")
print(df.dtypes)

print("\n=== Missing values ===")
missing = df.isna().sum().sort_values(ascending=False)
print(missing[missing > 0])

print("\n=== Descriptive statistics (numeric) ===")
print(df.describe())

print("\n=== Descriptive statistics (categorical) ===")
print(df.describe(include="object"))

print("\n=== Survival rate by sex ===")
print(df.groupby("sex")["survived"].mean())

print("\n=== Survival rate by pclass ===")
print(df.groupby("pclass")["survived"].mean())

# --- Outlier detection on numeric columns via IQR ---
print("\n=== Outliers (IQR method) ===")
for col in ["age", "fare", "sibsp", "parch"]:
    q1, q3 = df[col].quantile([0.25, 0.75])
    iqr = q3 - q1
    low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    n_outliers = ((df[col] < low) | (df[col] > high)).sum()
    print(f"{col}: {n_outliers} outliers outside [{low:.2f}, {high:.2f}]")

# --- Visualizations ---
plt.figure(figsize=(6, 4))
sns.countplot(data=df, x="survived")
plt.title("Survival counts")
plt.savefig(f"{OUT_DIR}/survival_counts.png", bbox_inches="tight")
plt.close()

plt.figure(figsize=(6, 4))
sns.histplot(data=df, x="age", hue="survived", multiple="stack", bins=30)
plt.title("Age distribution by survival")
plt.savefig(f"{OUT_DIR}/age_distribution.png", bbox_inches="tight")
plt.close()

plt.figure(figsize=(6, 4))
sns.boxplot(data=df, x="pclass", y="fare")
plt.title("Fare by passenger class")
plt.savefig(f"{OUT_DIR}/fare_by_class.png", bbox_inches="tight")
plt.close()

plt.figure(figsize=(6, 4))
sns.barplot(data=df, x="pclass", y="survived", hue="sex")
plt.title("Survival rate by class and sex")
plt.savefig(f"{OUT_DIR}/survival_by_class_sex.png", bbox_inches="tight")
plt.close()

plt.figure(figsize=(8, 6))
numeric_cols = df.select_dtypes("number")
sns.heatmap(numeric_cols.corr(), annot=True, fmt=".2f", cmap="coolwarm")
plt.title("Correlation heatmap (numeric features)")
plt.savefig(f"{OUT_DIR}/correlation_heatmap.png", bbox_inches="tight")
plt.close()

print(f"\nFigures saved to ./{OUT_DIR}/")
