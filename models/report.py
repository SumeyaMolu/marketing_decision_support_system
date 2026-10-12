
from extensions import db


class Report(db.Model):
    __tablename__ = "reports"

    report_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id"),
        nullable=False
    )

    campaign_id = db.Column(
        db.Integer,
        db.ForeignKey("campaigns.campaign_id"),
        nullable=False
    )

    report_title = db.Column(
        db.String(150),
        nullable=False
    )

    report_type = db.Column(
        db.String(50)
    )

    report_content = db.Column(
        db.Text
    )

    generated_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    # Relationship with User
    user = db.relationship(
        "User",
        back_populates="reports"
    )

    # Relationship with Campaign
    campaign = db.relationship(
        "Campaign",
        back_populates="reports"
    )
