
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import func

from extensions import db
from models.campaign import Campaign
from models.campaign_customer import CampaignCustomer
from models.prediction import Prediction
from models.recommendation import Recommendation
from models.report import Report

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


@reports_bp.route("/")
@login_required
def reports_list():

    reports = (
        Report.query
        .filter_by(user_id=current_user.user_id)
        .order_by(Report.generated_at.desc())
        .all()
    )

    return render_template(
        "reports.html",
        reports=reports
    )


@reports_bp.route("/generate", methods=["GET", "POST"])
@login_required
def generate_report():

    campaigns = Campaign.query.order_by(
        Campaign.campaign_id.desc()
    ).all()

    if request.method == "POST":

        campaign_id = request.form.get("campaign_id")
        report_title = request.form.get("report_title", "").strip()

        if not campaign_id or not report_title:
            flash("Please select a campaign and enter a report title.", "error")
            return redirect(url_for("reports.generate_report"))

        campaign = db.session.get(Campaign, campaign_id)

        if not campaign:
            flash("The selected campaign could not be found.", "error")
            return redirect(url_for("reports.generate_report"))

        # Count customers associated with the campaign
        total_customers = CampaignCustomer.query.filter_by(
            campaign_id=campaign.campaign_id
        ).count()

        # Retrieve prediction statistics
        predictions = Prediction.query.filter_by(
            campaign_id=campaign.campaign_id
        ).all()

        total_predictions = len(predictions)

        predicted_conversions = sum(
            1 for prediction in predictions
            if prediction.prediction_result is True
        )

        predicted_non_conversions = sum(
            1 for prediction in predictions
            if prediction.prediction_result is False
        )

        average_probability = (
            sum(
                float(prediction.predicted_conversion or 0)
                for prediction in predictions
            ) / total_predictions
            if total_predictions > 0 else 0
        )

        # Count recommendations
        total_recommendations = Recommendation.query.filter_by(
            campaign_id=campaign.campaign_id
        ).count()

        # Generate report content
        report_content = f"""
CAMPAIGN PERFORMANCE REPORT

Campaign: {campaign.campaign_name}

CAMPAIGN OVERVIEW
Total customers associated with campaign: {total_customers}

PREDICTION SUMMARY
Total predictions made: {total_predictions}
Predicted conversions: {predicted_conversions}
Predicted non-conversions: {predicted_non_conversions}
Average predicted conversion probability: {average_probability * 100:.2f}%

RECOMMENDATION SUMMARY
Total recommendations generated: {total_recommendations}

MARKETING INSIGHTS
"""

        if total_predictions == 0:
            report_content += (
                "No predictions have been made for this campaign yet. "
                "Run customer conversion predictions to generate further insights."
            )
        else:
            report_content += (
                f"{predicted_conversions} customers were classified as likely "
                f"to convert, while {predicted_non_conversions} were classified "
                "as unlikely to convert. "
            )

            if average_probability >= 0.5:
                report_content += (
                    "The average predicted conversion probability is relatively "
                    "high. Consider prioritising customer follow-up."
                )
            else:
                report_content += (
                    "The average predicted conversion probability is relatively "
                    "low. Consider reviewing campaign targeting and engagement."
                )

        # Save report
        new_report = Report(
            user_id=current_user.user_id,
            campaign_id=campaign.campaign_id,
            report_title=report_title,
            report_type="Campaign Performance",
            report_content=report_content
        )

        db.session.add(new_report)
        db.session.commit()

        flash("Campaign report generated successfully!", "success")

        return redirect(
            url_for(
                "reports.view_report",
                report_id=new_report.report_id
            )
        )

    return render_template(
        "generate_report.html",
        campaigns=campaigns
    )


@reports_bp.route("/<int:report_id>")
@login_required
def view_report(report_id):

    report = Report.query.filter_by(
        report_id=report_id,
        user_id=current_user.user_id
    ).first_or_404()

    return render_template(
        "view_report.html",
        report=report
    )
