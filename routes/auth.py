
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user
from werkzeug.security import check_password_hash

from models.user import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for("home"))

        flash("Invalid email or password.", "error")

    return render_template("login.html")
