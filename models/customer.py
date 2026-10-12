
from extensions import db


class Customer(db.Model):
    __tablename__ = "customers"

    customer_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    full_name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    # Relationship with MarketingData
    marketing_data_records = db.relationship(
        "MarketingData",
        back_populates="customer"
    )

    # Relationship with Prediction
    predictions = db.relationship(
        "Prediction",
        back_populates="customer"
    )


