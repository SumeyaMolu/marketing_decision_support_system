
from extensions import db


class Prediction(db.Model):
    __tablename__ = "predictions"

    prediction_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    customer_id = db.Column(
        db.Integer,
        db.ForeignKey("customers.customer_id"),
        nullable=False
    )

    campaign_id = db.Column(
        db.Integer,
        db.ForeignKey("campaigns.campaign_id"),
        nullable=False
    )

    predicted_conversion = db.Column(
        db.Numeric(6, 4)
    )

    prediction_result = db.Column(
        db.Boolean
    )

    prediction_date = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    # Relationship with Customer
    customer = db.relationship(
        "Customer",
        back_populates="predictions"
    )

    # Relationship with Campaign
    campaign = db.relationship(
        "Campaign",
        back_populates="predictions"
    )

    # Relationship with Recommendation
    recommendations = db.relationship(
        "Recommendation",
        back_populates="prediction"
    )


