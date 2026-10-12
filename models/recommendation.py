
from extensions import db


class Recommendation(db.Model):
    __tablename__ = "recommendations"

    recommendation_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    prediction_id = db.Column(
        db.Integer,
        db.ForeignKey("predictions.prediction_id"),
        nullable=False
    )

    campaign_id = db.Column(
        db.Integer,
        db.ForeignKey("campaigns.campaign_id"),
        nullable=False
    )

    recommendation_text = db.Column(
        db.Text,
        nullable=False
    )

    recommended_action = db.Column(
        db.String(255)
    )

    recommended_budget = db.Column(
        db.Numeric(12, 2)
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    # Relationship with Prediction
    prediction = db.relationship(
        "Prediction",
        back_populates="recommendations"
    )

    # Relationship with Campaign
    campaign = db.relationship(
        "Campaign",
        back_populates="recommendations"
    )
