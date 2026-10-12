
from extensions import db
from flask_login import UserMixin


class User(UserMixin, db.Model):
    __tablename__ = "users"

    user_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    full_name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(100),
        nullable=False,
        unique=True
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    role_id = db.Column(
        db.Integer,
        db.ForeignKey("roles.role_id"),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    # Relationship with Role
    role = db.relationship(
        "Role",
        back_populates="users"
    )

    # Relationship with Campaign
    campaigns = db.relationship(
        "Campaign",
        back_populates="created_by_user"
    )

    # Relationship with Report
    reports = db.relationship(
        "Report",
        back_populates="user"
    )

    # Flask-Login user identifier
    def get_id(self):
        return str(self.user_id)


