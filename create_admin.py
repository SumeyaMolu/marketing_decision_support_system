
from getpass import getpass

from werkzeug.security import generate_password_hash

from app import app, db
from models.role import Role
from models.user import User


def create_admin():
    print("\nMarketing Decision Support System")
    print("Create your administrator account\n")

    full_name = input("Enter your full name: ").strip()
    email = input("Enter your email address: ").strip().lower()

    if not full_name or not email:
        print("Name and email are required.")
        return

    password = getpass("Create a password: ")
    confirm_password = getpass("Confirm your password: ")

    if len(password) < 12:
        print("Use a password with at least 12 characters.")
        return

    if password != confirm_password:
        print("The passwords do not match.")
        return

    with app.app_context():
        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            print("A user with that email already exists.")
            return

        admin_role = Role.query.filter_by(
            role_name="Administrator"
        ).first()

        if admin_role is None:
            admin_role = Role(
                role_name="Administrator",
                description="Manages the system and user access."
            )
            db.session.add(admin_role)
            db.session.flush()

        admin = User(
            full_name=full_name,
            email=email,
            password_hash=generate_password_hash(password),
            role_id=admin_role.role_id
        )

        try:
            db.session.add(admin)
            db.session.commit()
            print("\nAdministrator account created successfully!")
            print("You can now sign in through your login page.")

        except Exception:
            db.session.rollback()
            print("Account creation failed. Check the application logs.")
            app.logger.exception("Administrator creation failed")


if __name__ == "__main__":
    create_admin()
