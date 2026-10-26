"""Authentication routes — register, login, logout."""
from flask import (
    Blueprint, render_template, redirect, url_for,
    flash, request, session,
)
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.user import User

bp = Blueprint("auth", __name__)

ALLOWED_PUBLIC_ROLES = ("seller", "buyer", "recovery_partner")


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        name     = request.form.get("name", "").strip()
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm_password", "")
        role     = request.form.get("role", "seller")
        contact  = request.form.get("contact", "").strip()

        errors = []

        # Validation (FR-01, VAL-01, SEC-01)
        if not name:
            errors.append("Full name is required.")
        if not email or "@" not in email:
            errors.append("A valid email address is required.")
        if len(password) < 8:
            errors.append("Password must be at least 8 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")
        if role not in ALLOWED_PUBLIC_ROLES:
            errors.append("Invalid role selected.")

        if not errors:
            existing = User.query.filter_by(email=email).first()
            if existing:
                errors.append("An account with that email address already exists.")

        if errors:
            return render_template(
                "auth/register.html",
                errors=errors,
                form_data=request.form,
                allowed_roles=ALLOWED_PUBLIC_ROLES,
            )

        user = User(name=name, email=email, role=role, contact=contact)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template(
        "auth/register.html",
        errors=[],
        form_data={},
        allowed_roles=ALLOWED_PUBLIC_ROLES,
    )


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return _post_login_redirect(current_user)

    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html", email=email)

        if not user.is_active_account:
            flash("Your account has been disabled. Please contact support.", "warning")
            return render_template("auth/login.html", email=email)

        login_user(user, remember=remember)
        next_page = request.args.get("next")
        # Validate next_page to prevent open redirect
        if next_page and next_page.startswith("/") and not next_page.startswith("//"):
            return redirect(next_page)
        return _post_login_redirect(user)

    return render_template("auth/login.html", email="")


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))


def _post_login_redirect(user):
    if user.is_admin():
        return redirect(url_for("admin.dashboard"))
    return redirect(url_for("listings.dashboard"))
