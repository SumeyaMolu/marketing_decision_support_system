
import os
from urllib.parse import quote_plus

from flask import Flask
from flask_login import LoginManager
from dotenv import load_dotenv

from extensions import db


# Load environment variables from .env
load_dotenv()

# Initialize Flask application
app = Flask(__name__)


# ---------------------------------------------
# Application configuration
# ---------------------------------------------

mysql_user = os.getenv("MYSQL_USER", "root")
mysql_password = os.getenv("MYSQL_PASSWORD", "")
mysql_host = os.getenv("MYSQL_HOST", "localhost")
mysql_database = os.getenv(
    "MYSQL_DATABASE",
    "marketing_decision_support_system"
)

secret_key = os.getenv("SECRET_KEY")

if not secret_key:
    raise RuntimeError(
        "SECRET_KEY is missing. Add a secure SECRET_KEY to your .env file."
    )

encoded_user = quote_plus(mysql_user)
encoded_password = quote_plus(mysql_password)

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{encoded_user}:{encoded_password}"
    f"@{mysql_host}/{mysql_database}"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = secret_key


# ---------------------------------------------
# Initialize database
# ---------------------------------------------

db.init_app(app)


# ---------------------------------------------
# Initialize Flask-Login
# ---------------------------------------------

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"


# ---------------------------------------------
# Import database models
# ---------------------------------------------

from models.role import Role
from models.user import User
from models.customer import Customer
from models.campaign import Campaign
from models.campaign_customer import CampaignCustomer
from models.marketing_data import MarketingData
from models.prediction import Prediction
from models.recommendation import Recommendation
from models.report import Report


# ---------------------------------------------
# Register authentication routes
# ---------------------------------------------

from routes.auth import auth_bp

app.register_blueprint(auth_bp)


# ---------------------------------------------
# Load logged-in users
# ---------------------------------------------

@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (ValueError, TypeError):
        return None


# ---------------------------------------------
# Home page
# ---------------------------------------------

@app.route("/")
def home():
    return "Marketing Decision Support System"


# ---------------------------------------------
# Test database connection
# ---------------------------------------------

@app.route("/test-db")
def test_db():
    try:
        db.session.execute(db.text("SELECT 1"))
        return "Database connection successful!"

    except Exception:
        app.logger.exception("Database connection test failed")
        return (
            "Database connection failed. "
            "Check your .env configuration and application logs."
        ), 500


# ---------------------------------------------
# Run application
# ---------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)

