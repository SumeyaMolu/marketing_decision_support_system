from extensions import db


class CampaignCustomer(db.Model):
    __tablename__ = "campaign_customer"

    campaign_customer_id = db.Column(
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
        db.ForeignKey("customers.customer_id"),
        nullable=False
    )