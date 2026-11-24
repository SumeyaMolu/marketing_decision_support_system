
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required

from extensions import db
from models.marketing_data import MarketingData
from models.campaign import Campaign
from models.customer import Customer


marketing_data_bp = Blueprint(
    "marketing_data",
    __name__,
    url_prefix="/marketing-data"
)


@marketing_data_bp.route("/")
@login_required
def index():
    records = MarketingData.query.order_by(
        MarketingData.recorded_at.desc()
    ).all()

    return render_template(
        "marketing_data/index.html",
        records=records
    )


@marketing_data_bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    campaigns = Campaign.query.all()
    customers = Customer.query.all()

    if request.method == "POST":
        try:
            record = MarketingData(
                campaign_id=request.form.get("campaign_id"),
                customer_id=request.form.get("customer_id") or None,
                channel=request.form.get("channel"),
                ad_spend=request.form.get("ad_spend") or 0,
                impressions=request.form.get("impressions") or 0,
                clicks=request.form.get("clicks") or 0,
                website_traffic=request.form.get("website_traffic") or 0,
                ctr=request.form.get("ctr") or 0,
                time_on_site=request.form.get("time_on_site") or 0,
                conversion=request.form.get("conversion") == "1"
            )

            db.session.add(record)
            db.session.commit()

            flash("Marketing data added successfully!", "success")
            return redirect(url_for("marketing_data.index"))

        except Exception as e:
            db.session.rollback()
            flash(f"Error adding marketing data: {str(e)}", "danger")

    return render_template(
        "marketing_data/add.html",
        campaigns=campaigns,
        customers=customers
    )


@marketing_data_bp.route("/edit/<int:record_id>", methods=["GET", "POST"])
@login_required
def edit(record_id):
    record = MarketingData.query.get_or_404(record_id)

    campaigns = Campaign.query.all()
    customers = Customer.query.all()

    if request.method == "POST":
        try:
            record.campaign_id = request.form.get("campaign_id")
            record.customer_id = request.form.get("customer_id") or None
            record.channel = request.form.get("channel")
            record.ad_spend = request.form.get("ad_spend") or 0
            record.impressions = request.form.get("impressions") or 0
            record.clicks = request.form.get("clicks") or 0
            record.website_traffic = request.form.get("website_traffic") or 0
            record.ctr = request.form.get("ctr") or 0
            record.time_on_site = request.form.get("time_on_site") or 0
            record.conversion = request.form.get("conversion") == "1"

            db.session.commit()

            flash("Marketing data updated successfully!", "success")
            return redirect(url_for("marketing_data.index"))

        except Exception as e:
            db.session.rollback()
            flash(f"Error updating marketing data: {str(e)}", "danger")

    return render_template(
        "marketing_data/edit.html",
        record=record,
        campaigns=campaigns,
        customers=customers
    )


@marketing_data_bp.route("/delete/<int:record_id>", methods=["POST"])
@login_required
def delete(record_id):
    record = MarketingData.query.get_or_404(record_id)

    try:
        db.session.delete(record)
        db.session.commit()

        flash("Marketing data deleted successfully!", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting marketing data: {str(e)}", "danger")

    return redirect(url_for("marketing_data.index"))
