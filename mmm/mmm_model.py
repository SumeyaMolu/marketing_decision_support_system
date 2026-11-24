
# ============================================================
# MARKETING MIX MODELING (MMM)
#
# Step 1: Data Loading and Preparation
# Step 2: Advertising Adstock Transformation
# Step 3: Advertising Saturation Transformation
# Step 4: OLS Regression Modelling
# Step 5: Model Performance Evaluation
# Step 6: Chronological Train-Test Evaluation
# Step 7: Actual vs Predicted Conversions Visualisation
# Step 8: Multicollinearity Analysis (VIF)
# Step 9: Channel Contribution and ROI Analysis
# Step 10: Channel Contribution Visualisation
# ============================================================

import os
import pandas as pd
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt

from statsmodels.stats.outliers_influence import (
    variance_inflation_factor
)


# ============================================================
# DATASET PATH
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

DATA_PATH = os.path.join(
    BASE_DIR,
    "data",
    "national_all_channels.csv"
)


# ============================================================
# STEP 1: LOAD AND PREPARE DATA
# ============================================================

def load_mmm_data():

    df = pd.read_csv(DATA_PATH)

    df["time"] = pd.to_datetime(df["time"])

    df = df.sort_values("time").reset_index(drop=True)

    return df


def validate_mmm_data(df):

    required_columns = [
        "time",
        "conversions",
        "revenue_per_conversion",
        "Channel0_impression",
        "Channel1_impression",
        "Channel2_impression",
        "Channel3_impression",
        "Channel4_impression",
        "Channel0_spend",
        "Channel1_spend",
        "Channel2_spend",
        "Channel3_spend",
        "Channel4_spend",
        "Organic_channel0_impression",
        "competitor_sales_control",
        "sentiment_score_control",
        "Promo"
    ]

    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing columns: {missing_columns}"
        )

    if df[required_columns].isnull().any().any():
        raise ValueError(
            "Missing values detected in the dataset."
        )

    if df["time"].duplicated().any():
        raise ValueError(
            "Duplicate dates detected."
        )

    numeric_data = df.select_dtypes(
        include=np.number
    )

    if not np.isfinite(
        numeric_data.to_numpy()
    ).all():
        raise ValueError(
            "Invalid numerical values detected."
        )

    if (df["conversions"] < 0).any():
        raise ValueError(
            "Conversions cannot be negative."
        )

    if (df["revenue_per_conversion"] < 0).any():
        raise ValueError(
            "Revenue per conversion cannot be negative."
        )

    spend_columns = [
        f"Channel{i}_spend"
        for i in range(5)
    ]

    if (df[spend_columns] < 0).any().any():
        raise ValueError(
            "Advertising spend cannot be negative."
        )

    print("Dataset validation successful!")


# ============================================================
# STEP 2: ADSTOCK TRANSFORMATION
# ============================================================

def apply_adstock(
    data,
    channel_columns,
    decay_rate=0.5
):

    transformed_data = data.copy()

    for column in channel_columns:

        adstock_values = []

        previous_adstock = 0

        for current_value in transformed_data[column]:

            current_adstock = (
                current_value
                + decay_rate * previous_adstock
            )

            adstock_values.append(
                current_adstock
            )

            previous_adstock = current_adstock

        transformed_data[
            f"{column}_adstock"
        ] = adstock_values

    return transformed_data


# ============================================================
# STEP 3: SATURATION TRANSFORMATION
# ============================================================

def apply_saturation(
    data,
    channel_columns,
    saturation_params=None
):

    transformed_data = data.copy()

    for column in channel_columns:

        if saturation_params is None:

            alpha = transformed_data[column].median()

        else:

            alpha = saturation_params[column]

        if alpha <= 0:
            raise ValueError(
                f"Invalid saturation parameter for {column}"
            )

        transformed_data[
            f"{column}_saturation"
        ] = (
            transformed_data[column]
            / (transformed_data[column] + alpha)
        )

    return transformed_data


# ============================================================
# STEP 4: OLS REGRESSION MODEL
# ============================================================

def prepare_regression_features(data):

    model_data = data.copy()

    if "time_trend" not in model_data.columns:

        model_data["time_trend"] = np.arange(
            len(model_data)
        )

    channel_features = [
        f"Channel{i}_impression_adstock_saturation"
        for i in range(5)
    ]

    control_features = [
        "Organic_channel0_impression",
        "competitor_sales_control",
        "sentiment_score_control",
        "Promo",
        "time_trend"
    ]

    feature_columns = (
        channel_features + control_features
    )

    X = model_data[feature_columns].copy()

    # Scale organic impressions.
    X["Organic_channel0_impression"] = (
        X["Organic_channel0_impression"] / 1_000_000
    )

    # Scale conversions to millions.
    y = model_data["conversions"] / 1_000_000

    return X, y


def build_mmm_regression(data):

    X, y = prepare_regression_features(data)

    X = sm.add_constant(
        X,
        has_constant="add"
    )

    model = sm.OLS(y, X).fit(
        cov_type="HAC",
        cov_kwds={"maxlags": 4}
    )

    return model


# ============================================================
# STEP 5: TRAINING MODEL PERFORMANCE EVALUATION
# ============================================================

def evaluate_mmm_model(model):

    actual = np.asarray(
        model.model.endog
    )

    predicted = np.asarray(
        model.fittedvalues
    )

    conversion_scale = 1_000_000

    actual_conversions = (
        actual * conversion_scale
    )

    predicted_conversions = (
        predicted * conversion_scale
    )

    mae = np.mean(
        np.abs(
            actual_conversions - predicted_conversions
        )
    )

    rmse = np.sqrt(
        np.mean(
            (actual_conversions - predicted_conversions) ** 2
        )
    )

    r_squared = model.rsquared

    print("\nTRAINING MODEL PERFORMANCE")
    print("===========================")

    print(f"MAE: {mae:,.2f}")

    print(f"RMSE: {rmse:,.2f}")

    print(f"R-squared: {r_squared:.4f}")

    comparison = pd.DataFrame({

        "Actual Conversions": actual_conversions,

        "Predicted Conversions": predicted_conversions,

        "Prediction Error": (
            actual_conversions - predicted_conversions
        )

    })

    print("\nTRAINING DATA: ACTUAL VS PREDICTED")
    print("==================================")

    print(
        comparison.head(10).round(2).to_string(index=False)
    )

    return comparison


# ============================================================
# STEP 6: CHRONOLOGICAL TEST DATA EVALUATION
# ============================================================

def evaluate_mmm_test(model, test_data):

    # Prepare test features.
    X_test, y_test = prepare_regression_features(
        test_data
    )

    X_test = sm.add_constant(
        X_test,
        has_constant="add"
    )

    # Ensure test columns match training columns.
    X_test = X_test.reindex(
        columns=model.model.exog_names,
        fill_value=0
    )

    # Predict conversions for unseen observations.
    predictions = model.predict(X_test)

    conversion_scale = 1_000_000

    actual = (
        np.asarray(y_test) * conversion_scale
    )

    predicted = (
        np.asarray(predictions) * conversion_scale
    )

    # Calculate MAE.
    mae = np.mean(
        np.abs(actual - predicted)
    )

    # Calculate RMSE.
    rmse = np.sqrt(
        np.mean((actual - predicted) ** 2)
    )

    # Calculate test R-squared.
    ss_res = np.sum(
        (actual - predicted) ** 2
    )

    ss_total = np.sum(
        (actual - np.mean(actual)) ** 2
    )

    if ss_total > 0:

        r_squared = 1 - (ss_res / ss_total)

    else:

        r_squared = np.nan

    print("\nCHRONOLOGICAL TEST PERFORMANCE")
    print("================================")

    print(
        f"Testing observations: {len(test_data)}"
    )

    print(f"MAE: {mae:,.2f}")

    print(f"RMSE: {rmse:,.2f}")

    print(f"Test R-squared: {r_squared:.4f}")

    # Actual versus predicted conversions.
    comparison = pd.DataFrame({

        "Date": test_data["time"].to_numpy(),

        "Actual Conversions": actual,

        "Predicted Conversions": predicted,

        "Prediction Error": actual - predicted

    })

    print("\nTEST DATA: ACTUAL VS PREDICTED")
    print("==============================")

    print(
        comparison.to_string(
            index=False,
            formatters={
                "Actual Conversions": "{:,.2f}".format,
                "Predicted Conversions": "{:,.2f}".format,
                "Prediction Error": "{:,.2f}".format
            }
        )
    )

    return comparison


# ============================================================
# STEP 7: ACTUAL VS PREDICTED CONVERSIONS VISUALISATION
# ============================================================

def plot_actual_vs_predicted(comparison):

    plt.figure(figsize=(12, 6))

    plt.plot(
        comparison["Date"],
        comparison["Actual Conversions"],
        label="Actual Conversions",
        marker="o"
    )

    plt.plot(
        comparison["Date"],
        comparison["Predicted Conversions"],
        label="Predicted Conversions",
        marker="o"
    )

    plt.title(
        "Actual vs Predicted Conversions"
    )

    plt.xlabel("Date")

    plt.ylabel("Number of Conversions")

    plt.legend()

    plt.xticks(rotation=45)

    plt.grid(True)

    plt.tight_layout()

    plt.show()


# ============================================================
# STEP 8: MULTICOLLINEARITY ANALYSIS (VIF)
# ============================================================

def calculate_vif(data):

    X, _ = prepare_regression_features(data)

    X = sm.add_constant(
        X,
        has_constant="add"
    )

    vif_results = []

    for i, column in enumerate(X.columns):

        if column == "const":
            continue

        vif_value = variance_inflation_factor(
            X.values,
            i
        )

        vif_results.append({

            "Variable": column,

            "VIF": vif_value

        })

    vif_df = pd.DataFrame(vif_results)

    return vif_df.sort_values(
        by="VIF",
        ascending=False
    ).reset_index(drop=True)


# ============================================================
# STEP 9: CHANNEL CONTRIBUTION AND ROI ANALYSIS
# ============================================================

def calculate_channel_performance(data, model):

    performance_results = []

    total_channel_contribution = 0

    conversion_scale = 1_000_000

    print("\nRegression target scale detected:")

    print(
        f"Conversion multiplier: {conversion_scale:,}"
    )

    # Calculate modelled channel contributions.
    for i in range(5):

        feature_name = (
            f"Channel{i}_impression_adstock_saturation"
        )

        coefficient = model.params[feature_name]

        channel_activity = data[feature_name]

        contribution_in_model_units = (
            coefficient * channel_activity
        ).sum()

        contribution_conversions = (
            contribution_in_model_units
            * conversion_scale
        )

        total_channel_contribution += (
            contribution_conversions
        )

        performance_results.append({

            "Channel": f"Channel {i}",

            "Coefficient": coefficient,

            "Modelled Contribution (Conversions)": (
                contribution_conversions
            )

        })

    # Calculate contribution shares.
    for result in performance_results:

        if total_channel_contribution > 0:

            contribution_share = (

                result[
                    "Modelled Contribution (Conversions)"
                ]

                / total_channel_contribution

            ) * 100

        else:

            contribution_share = np.nan

        result["Contribution Share (%)"] = (
            contribution_share
        )

    # Calculate revenue and ROAS proxies.
    average_revenue_per_conversion = (
        data["revenue_per_conversion"].mean()
    )

    for i, result in enumerate(performance_results):

        spend_column = f"Channel{i}_spend"

        total_spend = data[spend_column].sum()

        estimated_revenue_proxy = (

            result[
                "Modelled Contribution (Conversions)"
            ]

            * average_revenue_per_conversion

        )

        if total_spend > 0:

            roas_proxy = (
                estimated_revenue_proxy / total_spend
            )

        else:

            roas_proxy = np.nan

        result["Total Advertising Spend"] = (
            total_spend
        )

        result["Estimated Revenue Proxy"] = (
            estimated_revenue_proxy
        )

        result["ROAS Proxy"] = roas_proxy

    performance_df = pd.DataFrame(
        performance_results
    )

    return performance_df


# ============================================================
# STEP 10: CHANNEL CONTRIBUTION VISUALISATION
# ============================================================

def plot_channel_contributions(channel_performance):

    plt.figure(figsize=(10, 6))

    plt.bar(
        channel_performance["Channel"],
        channel_performance["Contribution Share (%)"]
    )

    plt.title(
        "Marketing Channel Contribution Analysis"
    )

    plt.xlabel("Advertising Channels")

    plt.ylabel("Contribution Share (%)")

    plt.grid(
        axis="y",
        linestyle="--",
        alpha=0.7
    )

    plt.tight_layout()

    plt.show()


# ============================================================
# DEFINE ADVERTISING CHANNELS
# ============================================================

impression_columns = [
    f"Channel{i}_impression"
    for i in range(5)
]


# ============================================================
# MAIN EXECUTION
# ============================================================

if __name__ == "__main__":

    # --------------------------------------------------------
    # STEP 1: LOAD AND VALIDATE DATASET
    # --------------------------------------------------------

    marketing_df = load_mmm_data()

    validate_mmm_data(marketing_df)

    print("\nMMM DATASET INFORMATION")
    print("-----------------------")

    print(
        "Dataset shape:",
        marketing_df.shape
    )

    print(
        "Date range:",
        marketing_df["time"].min().date(),
        "to",
        marketing_df["time"].max().date()
    )

    # --------------------------------------------------------
    # CONVERSION DATA SCALE CHECK
    # --------------------------------------------------------

    print("\nCONVERSION DATA SCALE CHECK")
    print("===========================")

    print(
        "Minimum conversions:",
        marketing_df["conversions"].min()
    )

    print(
        "Maximum conversions:",
        marketing_df["conversions"].max()
    )

    print(
        "Average conversions:",
        marketing_df["conversions"].mean()
    )

    print(
        "Total conversions:",
        marketing_df["conversions"].sum()
    )

    print(
        "Average revenue per conversion:",
        marketing_df["revenue_per_conversion"].mean()
    )

    # --------------------------------------------------------
    # STEP 2: APPLY ADSTOCK TRANSFORMATION
    # --------------------------------------------------------

    # Preserve the chronological trend across both periods.
    marketing_df["time_trend"] = np.arange(
        len(marketing_df)
    )

    marketing_df = apply_adstock(
        marketing_df,
        impression_columns,
        decay_rate=0.5
    )

    print("\nADSTOCK TRANSFORMATION COMPLETED")

    # --------------------------------------------------------
    # CHRONOLOGICAL TRAIN-TEST SPLIT
    # --------------------------------------------------------

    split_index = int(
        len(marketing_df) * 0.80
    )

    train_raw = marketing_df.iloc[
        :split_index
    ].copy()

    test_raw = marketing_df.iloc[
        split_index:
    ].copy()

    print("\nCHRONOLOGICAL DATA SPLIT")
    print("========================")

    print(
        "Training observations:",
        len(train_raw)
    )

    print(
        "Testing observations:",
        len(test_raw)
    )

    print(
        "Training date range:",
        train_raw["time"].min().date(),
        "to",
        train_raw["time"].max().date()
    )

    print(
        "Testing date range:",
        test_raw["time"].min().date(),
        "to",
        test_raw["time"].max().date()
    )

    # --------------------------------------------------------
    # STEP 3: APPLY SATURATION TRANSFORMATION
    # --------------------------------------------------------

    adstock_columns = [
        f"{column}_adstock"
        for column in impression_columns
    ]

    # Learn saturation parameters from training data only.
    saturation_params = {

        column: train_raw[column].median()

        for column in adstock_columns

    }

    # Apply the same saturation parameters to all weeks.
    marketing_df = apply_saturation(
        marketing_df,
        adstock_columns,
        saturation_params
    )

    train_df = marketing_df.iloc[
        :split_index
    ].copy()

    test_df = marketing_df.iloc[
        split_index:
    ].copy()

    print("\nSATURATION TRANSFORMATION COMPLETED")

    # --------------------------------------------------------
    # STEP 4: TRAIN OLS REGRESSION MODEL
    # --------------------------------------------------------

    mmm_model = build_mmm_regression(
        train_df
    )

    print("\nOLS REGRESSION RESULTS")
    print("======================")

    print(
        mmm_model.summary()
    )

    # --------------------------------------------------------
    # STEP 5: EVALUATE TRAINING PERFORMANCE
    # --------------------------------------------------------

    training_evaluation = evaluate_mmm_model(
        mmm_model
    )

    # --------------------------------------------------------
    # STEP 6: EVALUATE TEST PERFORMANCE
    # --------------------------------------------------------

    test_evaluation = evaluate_mmm_test(
        mmm_model,
        test_df
    )

    # --------------------------------------------------------
    # STEP 7: VISUALISE ACTUAL VS PREDICTED CONVERSIONS
    # --------------------------------------------------------

    plot_actual_vs_predicted(test_evaluation)

    # --------------------------------------------------------
    # STEP 8: MULTICOLLINEARITY ANALYSIS
    # --------------------------------------------------------

    vif_results = calculate_vif(
        train_df
    )

    print("\nMULTICOLLINEARITY ANALYSIS (VIF)")
    print("================================")

    print(
        vif_results.to_string(index=False)
    )

    # --------------------------------------------------------
    # STEP 9: CHANNEL CONTRIBUTION AND ROI ANALYSIS
    # --------------------------------------------------------

    channel_performance = calculate_channel_performance(
        marketing_df,
        mmm_model
    )

    print(
        "\nMARKETING CHANNEL CONTRIBUTION AND ROI ANALYSIS"
    )

    print(
        "================================================"
    )

    print(
        channel_performance.round(4).to_string(index=False)
    )

    # --------------------------------------------------------
    # STEP 10: VISUALISE CHANNEL CONTRIBUTIONS
    # --------------------------------------------------------

    plot_channel_contributions(channel_performance)

    print("\nMMM analysis completed successfully!")
