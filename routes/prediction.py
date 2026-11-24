 
import os
import joblib
import pandas as pd
import xgboost

from flask import Blueprint, render_template, request, flash
from flask_login import login_required
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from extensions import db
from models.prediction import Prediction
from models.customer import Customer
from models.campaign import Campaign
from models.recommendation import Recommendation


# ---------------------------------------------------------
# PREDICTION BLUEPRINT
# ---------------------------------------------------------

prediction_bp = Blueprint(
    "prediction",
    __name__,
    url_prefix="/prediction"
)


# ---------------------------------------------------------
# MACHINE LEARNING MODEL FILE PATHS
# ---------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ML_MODELS_DIR = os.path.join(BASE_DIR, "ml_models")

PREPROCESSOR_PATH = os.path.join(
    ML_MODELS_DIR, "conversion_preprocessor.joblib"
)

BOOSTER_PATH = os.path.join(
    ML_MODELS_DIR, "xgboost_conversion_booster.json"
)

THRESHOLD_PATH = os.path.join(
    ML_MODELS_DIR, "conversion_threshold.joblib"
)


# ---------------------------------------------------------
# LOAD CONVERSION MODEL
# ---------------------------------------------------------

def load_conversion_model():
    """Load the preprocessor, XGBoost booster, and threshold."""

    preprocessor = joblib.load(PREPROCESSOR_PATH)

    booster = xgboost.XGBClassifier()
    booster.load_model(BOOSTER_PATH)

    threshold = joblib.load(THRESHOLD_PATH)

    return preprocessor, booster, float(threshold)


# ---------------------------------------------------------
# RENDER PREDICTION FORM
# ---------------------------------------------------------

def render_prediction_form(**kwargs):
    """Load customers and campaigns and display the prediction form."""

    customers = Customer.query.order_by(
        Customer.full_name
    ).all()

    campaigns = Campaign.query.order_by(
        Campaign.campaign_name
    ).all()

    return render_template(
        "prediction.html",
        customers=customers,
        campaigns=campaigns,
        **kwargs
    )


# ---------------------------------------------------------
# GENERATE MARKETING RECOMMENDATION
# ---------------------------------------------------------

def generate_recommendation(prediction_result):
    """Generate a simple recommendation from the prediction result."""

    if prediction_result:

        recommendation_text = (
            "This customer is likely to convert. "
            "Prioritise follow-up and provide a personalised offer."
        )

        recommended_action = (
            "Prioritise follow-up and personalised offers"
        )

    else:

        recommendation_text = (
            "This customer is unlikely to convert. "
            "Improve engagement through a targeted promotion."
        )

        recommended_action = (
            "Improve engagement through targeted promotions"
        )

    return recommendation_text, recommended_action


# ---------------------------------------------------------
# CUSTOMER CONVERSION PREDICTION
# ---------------------------------------------------------

@prediction_bp.route("/", methods=["GET", "POST"])
@login_required
def predict_conversion():
    """Display the prediction form and process submitted session data."""

    if request.method == "POST":

        selected_customer_id = request.form.get("customer_id")
        selected_campaign_id = request.form.get("campaign_id")

        try:

            # Check that a customer and campaign were selected.
            if not selected_customer_id or not selected_campaign_id:

                flash(
                    "Please select both a customer and a campaign.",
                    "danger"
                )

                return render_prediction_form()

            customer_id = int(selected_customer_id)
            campaign_id = int(selected_campaign_id)

            # Confirm that the selected customer exists.
            customer = db.session.get(Customer, customer_id)

            if customer is None:

                flash(
                    "The selected customer does not exist.",
                    "danger"
                )

                return render_prediction_form(
                    selected_customer_id=selected_customer_id,
                    selected_campaign_id=selected_campaign_id
                )

            # Confirm that the selected campaign exists.
            campaign = db.session.get(Campaign, campaign_id)

            if campaign is None:

                flash(
                    "The selected campaign does not exist.",
                    "danger"
                )

                return render_prediction_form(
                    selected_customer_id=selected_customer_id,
                    selected_campaign_id=selected_campaign_id
                )

            # Read the session features submitted through the form.
            session_data = {

                "Administrative": int(
                    request.form["Administrative"]
                ),

                "Administrative_Duration": float(
                    request.form["Administrative_Duration"]
                ),

                "Informational": int(
                    request.form["Informational"]
                ),

                "Informational_Duration": float(
                    request.form["Informational_Duration"]
                ),

                "ProductRelated": int(
                    request.form["ProductRelated"]
                ),

                "ProductRelated_Duration": float(
                    request.form["ProductRelated_Duration"]
                ),

                "BounceRates": float(
                    request.form["BounceRates"]
                ),

                "ExitRates": float(
                    request.form["ExitRates"]
                ),

                "SpecialDay": float(
                    request.form["SpecialDay"]
                ),

                "Month": request.form["Month"],

                "OperatingSystems": int(
                    request.form["OperatingSystems"]
                ),

                "Browser": int(
                    request.form["Browser"]
                ),

                "Region": int(
                    request.form["Region"]
                ),

                "TrafficType": int(
                    request.form["TrafficType"]
                ),

                "VisitorType": request.form["VisitorType"],

                "Weekend": request.form["Weekend"] == "True",
            }

            # Convert submitted features into a one-row DataFrame.
            session_df = pd.DataFrame([session_data])

            # Load the saved machine-learning components.
            preprocessor, booster, threshold = load_conversion_model()

            # Apply the same preprocessing used during model training.
            processed_data = preprocessor.transform(session_df)

            # Predict the probability of purchase.
            probability = float(
                booster.predict_proba(processed_data)[0, 1]
            )

            # Apply the saved classification threshold.
            prediction_result = probability >= threshold

            prediction = (
                "Purchase"
                if prediction_result
                else "No purchase"
            )

            # Create the prediction record.
            new_prediction = Prediction(
                customer_id=customer_id,
                campaign_id=campaign_id,
                predicted_conversion=probability,
                prediction_result=prediction_result
            )

            db.session.add(new_prediction)

            # Save temporarily to obtain the prediction ID.
            db.session.flush()

            # Generate a recommendation from the prediction.
            recommendation_text, recommended_action = (
                generate_recommendation(prediction_result)
            )

            # Create the recommendation record.
            new_recommendation = Recommendation(
                prediction_id=new_prediction.prediction_id,
                campaign_id=campaign_id,
                recommendation_text=recommendation_text,
                recommended_action=recommended_action
            )

            db.session.add(new_recommendation)

            # Save prediction and recommendation together.
            db.session.commit()

            flash(
                "Prediction and recommendation successfully saved.",
                "success"
            )

            # Display the prediction results.
            return render_prediction_form(
                probability=round(probability * 100, 2),
                prediction=prediction,
                threshold=threshold * 100,
                recommendation=recommendation_text,
                recommended_action=recommended_action,
                session_data=session_data,
                selected_customer_id=str(customer_id),
                selected_campaign_id=str(campaign_id)
            )

        except (ValueError, KeyError, TypeError) as error:

            db.session.rollback()

            flash(
                f"Please check the submitted values. Details: {error}",
                "danger"
            )

            return render_prediction_form(
                selected_customer_id=selected_customer_id,
                selected_campaign_id=selected_campaign_id
            )

        except SQLAlchemyError as error:

            db.session.rollback()

            print(f"Database error: {error}")

            flash(
                "A database error occurred. The prediction and "
                "recommendation could not be saved.",
                "danger"
            )

            return render_prediction_form(
                selected_customer_id=selected_customer_id,
                selected_campaign_id=selected_campaign_id
            )

        except Exception as error:

            db.session.rollback()

            print(f"Prediction error: {error}")

            flash(
                "An unexpected error occurred while generating "
                "the prediction.",
                "danger"
            )

            return render_prediction_form(
                selected_customer_id=selected_customer_id,
                selected_campaign_id=selected_campaign_id
            )

    # Display the form when the page is first opened.
    return render_prediction_form()


# ---------------------------------------------------------
# PREDICTION HISTORY
# ---------------------------------------------------------

@prediction_bp.route("/history")
@login_required
def prediction_history():
    """Display previously generated conversion predictions."""

    predictions = (
        Prediction.query
        .options(
            joinedload(Prediction.customer),
            joinedload(Prediction.campaign)
        )
        .order_by(Prediction.prediction_date.desc())
        .all()
    )

    return render_template(
        "prediction_history.html",
        predictions=predictions
    )


# ---------------------------------------------------------
# MARKETING RECOMMENDATIONS
# ---------------------------------------------------------

@prediction_bp.route("/recommendations")
@login_required
def recommendations():
    """Display all saved marketing recommendations."""

    recommendations_list = (
        Recommendation.query
        .options(
            joinedload(Recommendation.prediction)
            .joinedload(Prediction.customer),

            joinedload(Recommendation.campaign)
        )
        .order_by(Recommendation.created_at.desc())
        .all()
    )

    return render_template(
        "recommendations.html",
        recommendations=recommendations_list
    )
