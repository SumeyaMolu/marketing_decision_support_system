from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
)
from flask_login import (
    login_user,
    logout_user,
    current_user,
    login_required,
)
from werkzeug.security import (
    check_password_hash,
    generate_password_hash,
)

from extensions import db
from models.user import User
from models.role import Role

auth_bp = Blueprint("auth", __name__)


# ----------------------------------------
# REGISTRATION
# ----------------------------------------
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    # Validate required fields
    if not full_name or not email or not password:
        flash("Please complete all required fields.", "error")
        return render_template("register.html")

    if len(full_name) > 100 or len(email) > 100:
        flash("Your name or email is too long.", "error")
        return render_template("register.html")

    if len(password) < 12:
        flash(
            "Your password must contain at least 12 characters.",
            "error",
        )
        return render_template("register.html")

    if password != confirm_password:
        flash("Your passwords do not match.", "error")
        return render_template("register.html")

    # Check for an existing account
    existing_user = User.query.filter_by(email=email).first()

    if existing_user:
        flash(
            "An account with this email already exists.",
            "error",
        )
        return render_template("register.html")

    # Assign the default role
    analyst_role = Role.query.filter_by(
        role_name="Marketing Analyst"
    ).first()

    if analyst_role is None:
        flash(
            "Registration is unavailable because the Marketing Analyst "
            "role has not been configured.",
            "error",
        )
        return render_template("register.html")

    # Hash the password before saving
    new_user = User(
        full_name=full_name,
        email=email,
        password_hash=generate_password_hash(password),
        role_id=analyst_role.role_id,
    )

    try:
        db.session.add(new_user)
        db.session.commit()

        flash(
            "Account created successfully. Please sign in.",
            "success",
        )
        return redirect(url_for("auth.login"))

    except Exception:
        db.session.rollback()
        current_app.logger.exception("Registration failed")

        flash(
            "We could not create your account. Please try again.",
            "error",
        )
        return render_template("register.html")


# ----------------------------------------
# LOGIN
# ----------------------------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not email or not password:
        flash(
            "Please enter both your email and password.",
            "error",
        )
        return render_template("login.html")

    user = User.query.filter_by(email=email).first()

    if user is None:
        current_app.logger.warning(
            "Login failed: account not found for %s",
            email,
        )
        flash("Invalid email or password.", "error")
        return render_template("login.html")

    if not check_password_hash(user.password_hash, password):
        current_app.logger.warning(
            "Login failed: password verification failed for %s",
            email,
        )
        flash("Invalid email or password.", "error")
        return render_template("login.html")

    # Successful login
    login_user(user)
    flash("Login successful!", "success")

    # Go to the protected dashboard
    return redirect(url_for("home"))


# ----------------------------------------
# LOGOUT
# ----------------------------------------
@auth_bp.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")

    return redirect(url_for("auth.login"))

