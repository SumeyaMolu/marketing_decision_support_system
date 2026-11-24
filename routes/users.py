
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
)
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash

from extensions import db
from models.user import User
from models.role import Role

users_bp = Blueprint("users", __name__)


def is_administrator():
    """Check whether the logged-in user is an Administrator."""
    return (
        current_user.is_authenticated
        and current_user.role is not None
        and current_user.role.role_name == "Administrator"
    )


@users_bp.route("/users", methods=["GET", "POST"])
@login_required
def user_list():
    """Display registered users and allow Administrators to create accounts."""

    # Restrict user management to Administrators.
    if not is_administrator():
        return render_template("access_denied.html"), 403

    # Handle the account creation form.
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role_id = request.form.get("role_id", "").strip()

        # Validate required fields.
        if not full_name or not email or not password or not role_id:
            flash("Please complete all required fields.", "error")
            return redirect(url_for("users.user_list"))

        # Validate field lengths.
        if len(full_name) > 100 or len(email) > 100:
            flash("The name or email address is too long.", "error")
            return redirect(url_for("users.user_list"))

        # Require a minimum password length.
        if len(password) < 12:
            flash(
                "The password must contain at least 12 characters.",
                "error",
            )
            return redirect(url_for("users.user_list"))

        # Prevent duplicate accounts.
        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash(
                "An account with this email already exists.",
                "error",
            )
            return redirect(url_for("users.user_list"))

        # Verify that the selected role exists.
        try:
            selected_role = db.session.get(Role, int(role_id))
        except (ValueError, TypeError):
            selected_role = None

        if selected_role is None:
            flash("Please select a valid role.", "error")
            return redirect(url_for("users.user_list"))

        # Create the account with a securely hashed password.
        new_user = User(
            full_name=full_name,
            email=email,
            password_hash=generate_password_hash(password),
            role_id=selected_role.role_id,
        )

        try:
            db.session.add(new_user)
            db.session.commit()

            flash(
                "User account created successfully.",
                "success",
            )

        except Exception:
            db.session.rollback()

            current_app.logger.exception(
                "Administrator user creation failed"
            )

            flash(
                "Unable to create the account. Please try again.",
                "error",
            )

        return redirect(url_for("users.user_list"))

    # Retrieve users and roles for the page.
    users = User.query.order_by(User.user_id.asc()).all()
    roles = Role.query.order_by(Role.role_name.asc()).all()

    return render_template(
        "users.html",
        users=users,
        roles=roles,
    )