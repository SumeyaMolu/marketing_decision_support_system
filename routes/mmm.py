
from flask import Blueprint, render_template
from flask_login import login_required

import numpy as np

from mmm.mmm_model import (
    load_mmm_data,
    validate_mmm_data,
    apply_adstock,
    apply_saturation,
    build_mmm_regression,
    evaluate_mmm_test,
    calculate_channel_performance,
    calculate_vif,
)


mmm_bp = Blueprint("mmm", __name__)


@mmm_bp.route("/mmm")
@login_required
def mmm_dashboard():

    # 1. Load and validate the dataset
    marketing_df = load_mmm_data()

    validate_mmm_data(marketing_df)

    # 2. Define advertising channels
    impression_columns = [
        f"Channel{i}_impression"
        for i in range(5)
    ]

    # 3. Create chronological trend
    marketing_df["time_trend"] = np.arange(
        len(marketing_df)
    )

    # 4. Apply adstock transformation
    marketing_df = apply_adstock(
        marketing_df,
        impression_columns,
        decay_rate=0.5
    )

    # 5. Split data chronologically
    split_index = int(
        len(marketing_df) * 0.80
    )

    train_raw = marketing_df.iloc[
        :split_index
    ].copy()

    test_raw = marketing_df.iloc[
        split_index:
    ].copy()

    # 6. Learn saturation parameters from training data
    adstock_columns = [
        f"{column}_adstock"
        for column in impression_columns
    ]

    saturation_params = {
        column: train_raw[column].median()
        for column in adstock_columns
    }

    # 7. Apply saturation transformation
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

    # 8. Train MMM regression model
    mmm_model = build_mmm_regression(
        train_df
    )

    # 9. Evaluate test data
    test_evaluation = evaluate_mmm_test(
        mmm_model,
        test_df
    )

    # 10. Calculate test performance metrics
    actual = test_evaluation[
        "Actual Conversions"
    ].to_numpy()

    predicted = test_evaluation[
        "Predicted Conversions"
    ].to_numpy()

    mae = np.mean(
        np.abs(actual - predicted)
    )

    rmse = np.sqrt(
        np.mean((actual - predicted) ** 2)
    )

    ss_res = np.sum(
        (actual - predicted) ** 2
    )

    ss_total = np.sum(
        (actual - np.mean(actual)) ** 2
    )

    test_r_squared = (
        1 - (ss_res / ss_total)
        if ss_total > 0
        else np.nan
    )

    # 11. Calculate channel performance
    channel_performance = calculate_channel_performance(
        marketing_df,
        mmm_model
    )

    # 12. Calculate multicollinearity
    vif_results = calculate_vif(
        train_df
    )

    return render_template(
        "mmm_dashboard.html",
        mae=mae,
        rmse=rmse,
        test_r_squared=test_r_squared,
        channel_performance=channel_performance.to_dict(
            orient="records"
        ),
        vif_results=vif_results.to_dict(
            orient="records"
        ),
        total_weeks=len(marketing_df),
        training_weeks=len(train_df),
        testing_weeks=len(test_df),
    )
