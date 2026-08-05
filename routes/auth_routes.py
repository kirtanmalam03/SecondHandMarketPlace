from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
import re

from models import db
from models.user import User
from routes.product_routes import INDIA_STATES_AND_UT

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def validate_email(email):
    """Validate email format"""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email)


def validate_password(password):
    """Validate password strength"""
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    return True, ""


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("products.home"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        location = request.form.get("location", "").strip()
        phone = request.form.get("phone", "").strip()

        # Validation
        errors = []
        if not name:
            errors.append("Name is required.")
        if not email:
            errors.append("Email is required.")
        elif not validate_email(email):
            errors.append("Invalid email format.")
        if not password:
            errors.append("Password is required.")
        elif password != confirm_password:
            errors.append("Passwords do not match.")
        else:
            is_valid, msg = validate_password(password)
            if not is_valid:
                errors.append(msg)

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("register.html", name=name, email=email, location=location, phone=phone, india_states=INDIA_STATES_AND_UT)

        # Check existing user
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email is already registered. Please login.", "warning")
            return render_template("register.html", name=name, location=location, phone=phone, india_states=INDIA_STATES_AND_UT)

        # Create new user
        user = User(
            name=name,
            email=email,
            location=location,
            phone=phone if phone else None
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Account created successfully! Please login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html", india_states=INDIA_STATES_AND_UT)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("products.home"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = request.form.get("remember") == "on"

        if not email or not password:
            flash("Please enter both email and password.", "danger")
            return render_template("login.html")

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash("Invalid email or password.", "danger")
            return render_template("login.html")

        if not user.is_active:
            flash("Your account has been deactivated.", "danger")
            return render_template("login.html")

        login_user(user, remember=remember)
        flash(f"Welcome back, {user.name}! 👋", "success")

        # Redirect to next page or home
        next_page = request.args.get("next")
        if next_page:
            return redirect(next_page)
        return redirect(url_for("products.home"))

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/profile")
@login_required
def profile():
    return render_template("profile.html")


@auth_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        location = request.form.get("location", "").strip()
        phone = request.form.get("phone", "").strip()

        if not name:
            flash("Name is required.", "danger")
        else:
            current_user.name = name
            current_user.location = location if location else None
            current_user.phone = phone if phone else None
            db.session.commit()
            flash("Profile updated successfully!", "success")
            return redirect(url_for("auth.profile"))

    return render_template("edit_profile.html", india_states=INDIA_STATES_AND_UT)