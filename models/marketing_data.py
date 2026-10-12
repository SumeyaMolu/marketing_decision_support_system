
from extensions import db


class MarketingData(db.Model):
    __tablename__ = "marketing_data"

    marketing_data_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    campaign_id = db.Column(
        db.Integer,
        db.ForeignKey("campaigns.campaign_id"),
        nullable=False
    )

    customer_id = db.Column(
        db.Integer,
        db.ForeignKey("customers.customer_id")
    )

    channel = db.Column(
        db.String(50),
        nullable=False
    )

    ad_spend = db.Column(db.Numeric(12, 2))
    impressions = db.Column(db.Integer)
    clicks = db.Column(db.Integer)
    website_traffic = db.Column(db.Integer)
    ctr = db.Column(db.Numeric(6, 4))
    time_on_site = db.Column(db.Numeric(10, 2))
    conversion = db.Column(db.Boolean)

    recorded_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    # Relationship with Campaign
    campaign = db.relationship(
        "Campaign",
        back_populates="marketing_data_records"
    )

    # Relationship with Customer
    customer = db.relationship(
        "Customer",
        back_populates="marketing_data_records"
    )
