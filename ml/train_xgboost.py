from pathlib import Path

import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    classification_report,
    confusion_matrix,
)

from xgboost import XGBClassifier


# --------------------------------------------------
# 1. Locate the project folders and dataset
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"
MODEL_DIR = PROJECT_DIR / "ml" / "saved_models"

MODEL_DIR.mkdir(parents=True, exist_ok=True)

dataset_files = [
    file
    for file in DATA_DIR.glob("*.csv")
    if "online_shoppers_intention" in file.name.lower()
]

if not dataset_files:
    raise FileNotFoundError(
        "Online Shoppers dataset not found in the data folder."
    )

DATASET_PATH = dataset_files[0]

print("Loading dataset:", DATASET_PATH.name)

df = pd.read_csv(DATASET_PATH)


# --------------------------------------------------
# 2. Validate and prepare the target
# --------------------------------------------------

if "Revenue" not in df.columns:
    raise ValueError("The dataset must contain a Revenue column.")

df = df.dropna(subset=["Revenue"]).copy()

# Convert True/False or equivalent target values to 1/0.
if df["Revenue"].dtype == object:
    target_values = (
        df["Revenue"].astype(str).str.strip().str.lower()
    )

    target_mapping = {
        "true": 1,
        "false": 0,
        "1": 1,
        "0": 0,
    }

    df["Revenue"] = target_values.map(target_mapping)

if df["Revenue"].isna().any():
    raise ValueError(
        "Revenue contains values that could not be converted "
        "to binary labels."
    )

y = df["Revenue"].astype(int)

if not set(y.unique()).issubset({0, 1}):
    raise ValueError("Revenue must contain only binary 0/1 values.")


# --------------------------------------------------
# 3. Prepare the features
# --------------------------------------------------

# Exclude the target and PageValues to reduce leakage risk.
excluded_columns = ["Revenue", "PageValues"]

X = df.drop(
    columns=excluded_columns,
    errors="ignore",
)

# Treat text and Boolean columns as categorical.
categorical_columns = X.select_dtypes(
    include=["object", "category", "bool"]
).columns.tolist()

numerical_columns = [
    column
    for column in X.columns
    if column not in categorical_columns
]

# Ensure numeric columns contain valid numbers.
for column in numerical_columns:
    X[column] = pd.to_numeric(X[column], errors="coerce")

# Fill missing values using training data only.
# Imputation is performed inside the pipeline below.
from sklearn.impute import SimpleImputer

numeric_pipeline = Pipeline(
    steps=[
        ("imputer", SimpleImputer(strategy="median")),
    ]
)

categorical_pipeline = Pipeline(
    steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        (
            "onehot",
            OneHotEncoder(handle_unknown="ignore"),
        ),
    ]
)

preprocessor = ColumnTransformer(
    transformers=[
        ("numeric", numeric_pipeline, numerical_columns),
        ("categorical", categorical_pipeline, categorical_columns),
    ]
)


# --------------------------------------------------
# 4. Split the data
# --------------------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y,
)

print("\nDataset preparation complete.")
print("Total records:", len(df))
print("Training records:", len(X_train))
print("Testing records:", len(X_test))
print("Features:", X.shape[1])
print("Training conversion rate:", round(y_train.mean(), 4))


# --------------------------------------------------
# 5. Train the XGBoost model
# --------------------------------------------------

model = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        (
            "classifier",
            XGBClassifier(
                n_estimators=300,
                max_depth=4,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                objective="binary:logistic",
                eval_metric="logloss",
                random_state=42,
                n_jobs=-1,
            ),
        ),
    ]
)

print("\nTraining XGBoost model...")
model.fit(X_train, y_train)

print("Training completed.")


# --------------------------------------------------
# 6. Evaluate the model
# --------------------------------------------------

predictions = model.predict(X_test)
probabilities = model.predict_proba(X_test)[:, 1]

print("\n========== MODEL EVALUATION ==========")

print("Accuracy:", round(accuracy_score(y_test, predictions), 4))
print(
    "Precision:",
    round(precision_score(y_test, predictions, zero_division=0), 4),
)
print(
    "Recall:",
    round(recall_score(y_test, predictions, zero_division=0), 4),
)
print(
    "F1-score:",
    round(f1_score(y_test, predictions, zero_division=0), 4),
)
print("ROC-AUC:", round(roc_auc_score(y_test, probabilities), 4))

print("\nClassification report:")
print(classification_report(y_test, predictions, zero_division=0))

print("Confusion matrix:")
print(confusion_matrix(y_test, predictions))


# --------------------------------------------------
# 7. Save the model and feature information
# --------------------------------------------------

model_path = MODEL_DIR / "xgboost_conversion_model.joblib"
metadata_path = MODEL_DIR / "xgboost_model_metadata.joblib"

joblib.dump(model, model_path)

joblib.dump(
    {
        "features": X.columns.tolist(),
        "target": "Revenue",
        "excluded_columns": excluded_columns,
        "positive_class": 1,
        "dataset_name": DATASET_PATH.name,
    },
    metadata_path,
)

print("\nModel saved to:", model_path)
print("Metadata saved to:", metadata_path)
print("\nXGBoost training script finished successfully.")