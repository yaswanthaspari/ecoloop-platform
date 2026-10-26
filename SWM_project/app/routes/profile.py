"""User profile routes."""
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db

bp = Blueprint("profile", __name__)


@bp.route("/")
@login_required
def view():
    from app.models.listing import Listing
    listings = (
        Listing.query
        .filter_by(seller_id=current_user.id)
        .order_by(Listing.created_at.desc())
        .limit(10)
        .all()
    )
    return render_template("profile/view.html", user=current_user, listings=listings)


@bp.route("/edit", methods=["GET", "POST"])
@login_required
def edit():
    if request.method == "POST":
        name    = request.form.get("name", "").strip()
        contact = request.form.get("contact", "").strip()

        if not name:
            flash("Name cannot be empty.", "danger")
            return render_template("profile/edit.html", user=current_user)

        current_user.name    = name
        current_user.contact = contact or None
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("profile.view"))

    return render_template("profile/edit.html", user=current_user)


@bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        current_pw = request.form.get("current_password", "")
        new_pw     = request.form.get("new_password", "")
        confirm    = request.form.get("confirm_password", "")

        if not current_user.check_password(current_pw):
            flash("Current password is incorrect.", "danger")
            return render_template("profile/change_password.html")

        if len(new_pw) < 8:
            flash("New password must be at least 8 characters.", "danger")
            return render_template("profile/change_password.html")

        if new_pw != confirm:
            flash("Passwords do not match.", "danger")
            return render_template("profile/change_password.html")

        current_user.set_password(new_pw)
        db.session.commit()
        flash("Password changed successfully.", "success")
        return redirect(url_for("profile.view"))

    return render_template("profile/change_password.html")
