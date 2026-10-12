
from extensions import db


class Campaign(db.Model):
    __tablename__ = "campaigns"

    campaign_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    campaign_name = db.Column(
        db.String(100),
        nullable=False
    )

    channel = db.Column(
        db.String(50),
        nullable=False
    )

    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    budget = db.Column(db.Numeric(12, 2))

    created_by = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id"),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    # Relationship with User
    created_by_user = db.relationship(
        "User",
        back_populates="campaigns"
    )

    # Relationship with MarketingData
    marketing_data_records = db.relationship(
        "MarketingData",
        back_populates="campaign"
    )

    # Relationship with Prediction
    predictions = db.relationship(
        "Prediction",
        back_populates="campaign"
    )

    # Relationship with Recommendation
    recommendations = db.relationship(
        "Recommendation",
        back_populates="campaign"
    )

    # Relationship with Report
    reports = db.relationship(
        "Report",
        back_populates="campaign"
    )



