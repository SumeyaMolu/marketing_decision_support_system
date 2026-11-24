import os
from urllib.parse import quote_plus

from flask import Flask, render_template
from flask_login import (
    LoginManager,
    login_required,
    current_user,
)

from extensions import db

app = Flask(__name__)

# Database Configuration
mysql_password = os.getenv("MYSQL_PASSWORD", "YOUR_PASSWORD")
encoded_password = quote_plus(mysql_password)

app.config["SQLALCHEMY_DATABASE_URI"] = (
    "mysql+pymysql://root:"
    f"{encoded_password}@localhost/marketing_decision_support_system"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Flask Secret Key
app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY",
    "development-only-change-this-secret"
)

# Initialize Database
db.init_app(app)

# Flask Login Configuration
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"


# ==========================================
# IMPORT DATABASE MODELS
# ==========================================

from models.role import Role
from models.user import User
from models.customer import Customer
from models.campaign import Campaign
from models.campaign_customer import CampaignCustomer
from models.marketing_data import MarketingData
from models.prediction import Prediction
from models.recommendation import Recommendation
from models.report import Report


# ==========================================
# USER LOADER
# ==========================================

@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (ValueError, TypeError):
        return None


# ==========================================
# IMPORT BLUEPRINTS
# ==========================================

from routes.auth import auth_bp
from routes.users import users_bp
from routes.prediction import prediction_bp
from routes.mmm import mmm_bp
from routes.reports import reports_bp
from routes.marketing_data import marketing_data_bp


# ==========================================
# REGISTER BLUEPRINTS
# ==========================================

app.register_blueprint(auth_bp)
app.register_blueprint(users_bp)
app.register_blueprint(prediction_bp)
app.register_blueprint(mmm_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(marketing_data_bp)


# ==========================================
# DASHBOARD
# ==========================================

@app.route("/")
@login_required
def home():
    return render_template(
        "dashboard.html",
        user=current_user,
        name=current_user.full_name,
        role=current_user.role.role_name
        if current_user.role
        else "Unassigned",
    )


# ==========================================
# ACCESS DENIED
# ==========================================

@app.route("/access-denied")
@login_required
def access_denied():
    return render_template("access_denied.html"), 403


# ==========================================
# DATABASE CONNECTION TEST
# ==========================================

@app.route("/test-db")
def test_db():
    try:
        db.session.execute(db.text("SELECT 1"))
        return "Database connection successful!"

    except Exception:
        app.logger.exception("Database connection test failed")

        return (
            "Database connection failed. Check the application logs.",
            500,
        )


# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":
    app.run(debug=True)