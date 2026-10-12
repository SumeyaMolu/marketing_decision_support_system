
from extensions import db


class Role(db.Model):
    __tablename__ = "roles"

    role_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    role_name = db.Column(
        db.String(50),
        nullable=False,
        unique=True
    )

    description = db.Column(db.String(255))

    users = db.relationship(
        "User",
        back_populates="role"
    )
