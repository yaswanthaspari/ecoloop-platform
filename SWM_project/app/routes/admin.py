"""
Admin blueprint — dashboard, listing review, user management,
environmental knowledge management.
All routes are protected by the @admin_required decorator.
"""
import json
from functools import wraps
from flask import (
    Blueprint, render_template, redirect, url_for,
    flash, request, abort, jsonify,
)
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.listing import Listing
from app.models.recommendation import Recommendation
from app.models.environmental_impact import EnvironmentalImpact
from app.models.listing_status_history import ListingStatusHistory
from app.services import listing_service
from app.services.image_classifier import FLAT_CATEGORIES

bp = Blueprint("admin", __name__)


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_admin():
            abort(403)
        return f(*args, **kwargs)
    return decorated


# ── Dashboard ─────────────────────────────────────────────────────────────────

@bp.route("/")
@admin_required
def dashboard():
    from sqlalchemy import func
    from app.models.partner_interest import PartnerInterest

    total_users    = User.query.count()
    total_listings = Listing.query.count()
    flagged        = Listing.query.filter_by(status="pending_review").count()

    # Listings by status
    status_counts = dict(
        db.session.query(Listing.status, func.count(Listing.id))
        .group_by(Listing.status).all()
    )

    # Listings by category
    category_counts = dict(
        db.session.query(Listing.category_confirmed, func.count(Listing.id))
        .group_by(Listing.category_confirmed).all()
    )

    # Recommendations by route
    route_counts = dict(
        db.session.query(Recommendation.route, func.count(Recommendation.id))
        .group_by(Recommendation.route).all()
    )

    # Recent activity
    recent_history = (
        ListingStatusHistory.query
        .order_by(ListingStatusHistory.changed_at.desc())
        .limit(20).all()
    )

    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        total_listings=total_listings,
        flagged=flagged,
        status_counts=status_counts,
        category_counts=category_counts,
        route_counts=route_counts,
        recent_history=recent_history,
    )


# ── Listing management ────────────────────────────────────────────────────────

@bp.route("/listings")
@admin_required
def listings():
    q_status   = request.args.get("status", "")
    q_category = request.args.get("category", "")
    q_search   = request.args.get("q", "")
    q_route    = request.args.get("route", "")
    q_flagged  = request.args.get("flagged", "")
    page       = request.args.get("page", 1, type=int)

    query = Listing.query

    if q_status:
        query = query.filter_by(status=q_status)
    if q_category:
        query = query.filter_by(category_confirmed=q_category)
    if q_search:
        query = query.filter(Listing.title.ilike(f"%{q_search}%"))
    if q_route:
        query = query.join(Recommendation).filter(Recommendation.route == q_route)
    if q_flagged == "1":
        query = (
            query.join(Recommendation)
            .filter(
                (Recommendation.safety_flag == True) |  # noqa: E712
                (Recommendation.manual_review_flag == True)
            )
        )

    query = query.order_by(Listing.created_at.desc())
    pagination = query.paginate(page=page, per_page=20, error_out=False)

    return render_template(
        "admin/listings.html",
        pagination=pagination,
        listings=pagination.items,
        categories=FLAT_CATEGORIES,
        valid_statuses=Listing.VALID_STATUSES,
        valid_routes=Recommendation.VALID_ROUTES,
        filters={
            "status": q_status, "category": q_category,
            "q": q_search, "route": q_route, "flagged": q_flagged,
        },
    )


@bp.route("/listings/<int:listing_id>")
@admin_required
def listing_detail(listing_id):
    listing = db.get_or_404(Listing, listing_id)
    history = (
        ListingStatusHistory.query
        .filter_by(listing_id=listing_id)
        .order_by(ListingStatusHistory.changed_at.desc())
        .all()
    )
    return render_template(
        "admin/listing_detail.html",
        listing=listing,
        history=history,
        valid_statuses=Listing.VALID_STATUSES,
    )


@bp.route("/listings/<int:listing_id>/status", methods=["POST"])
@admin_required
def update_listing_status(listing_id):
    listing    = db.get_or_404(Listing, listing_id)
    new_status = request.form.get("new_status", "")
    note       = request.form.get("note", "").strip()

    if new_status not in Listing.VALID_STATUSES:
        flash("Invalid status selected.", "danger")
        return redirect(url_for("admin.listing_detail", listing_id=listing_id))

    # Safety check: do not approve safety-flagged items for ordinary resale
    if (
        new_status == "available"
        and listing.recommendation
        and listing.recommendation.safety_flag
    ):
        flash(
            "This listing has a safety flag. It cannot be set to 'available' "
            "without additional review. Use 'pending_review' or 'rejected'.",
            "danger",
        )
        return redirect(url_for("admin.listing_detail", listing_id=listing_id))

    listing_service.change_status(listing, new_status, current_user.id, note=note)
    db.session.commit()
    flash(f"Listing status updated to '{new_status}'.", "success")
    return redirect(url_for("admin.listing_detail", listing_id=listing_id))


# ── User management ───────────────────────────────────────────────────────────

@bp.route("/users")
@admin_required
def users():
    q_search = request.args.get("q", "").strip()
    q_role   = request.args.get("role", "").strip()
    page     = request.args.get("page", 1, type=int)

    query = User.query
    if q_search:
        query = query.filter(
            (User.name.ilike(f"%{q_search}%")) | (User.email.ilike(f"%{q_search}%"))
        )
    if q_role:
        query = query.filter_by(role=q_role)

    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=25, error_out=False
    )
    return render_template(
        "admin/users.html",
        pagination=pagination,
        users=pagination.items,
        filters={"q": q_search, "role": q_role},
    )


@bp.route("/users/<int:user_id>/toggle-active", methods=["POST"])
@admin_required
def toggle_user_active(user_id):
    user = db.get_or_404(User, user_id)
    if user.id == current_user.id:
        flash("You cannot deactivate your own account.", "warning")
        return redirect(url_for("admin.users"))
    user.is_active_account = not user.is_active_account
    db.session.commit()
    state = "activated" if user.is_active_account else "deactivated"
    flash(f"Account {state}.", "success")
    return redirect(url_for("admin.users"))


# ── Environmental knowledge management ────────────────────────────────────────

@bp.route("/environmental-impacts")
@admin_required
def env_impacts():
    q_category = request.args.get("category", "")
    q_status   = request.args.get("status", "")
    page       = request.args.get("page", 1, type=int)

    query = EnvironmentalImpact.query
    if q_category:
        query = query.filter_by(category=q_category)
    if q_status:
        query = query.filter_by(review_status=q_status)

    pagination = query.order_by(
        EnvironmentalImpact.category, EnvironmentalImpact.review_status
    ).paginate(page=page, per_page=20, error_out=False)

    return render_template(
        "admin/env_impacts.html",
        pagination=pagination,
        records=pagination.items,
        categories=FLAT_CATEGORIES,
        filters={"category": q_category, "status": q_status},
    )


@bp.route("/environmental-impacts/new", methods=["GET", "POST"])
@admin_required
def new_env_impact():
    if request.method == "POST":
        record, errors = _parse_env_impact_form(request.form)
        if errors:
            return render_template(
                "admin/env_impact_form.html",
                record=None,
                errors=errors,
                categories=FLAT_CATEGORIES,
                form_data=request.form,
            )
        db.session.add(record)
        db.session.commit()
        flash("Environmental knowledge record created.", "success")
        return redirect(url_for("admin.env_impacts"))

    return render_template(
        "admin/env_impact_form.html",
        record=None, errors=[], categories=FLAT_CATEGORIES, form_data={},
    )


@bp.route("/environmental-impacts/<int:record_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_env_impact(record_id):
    record = db.get_or_404(EnvironmentalImpact, record_id)

    if request.method == "POST":
        updated, errors = _parse_env_impact_form(request.form, existing=record)
        if errors:
            return render_template(
                "admin/env_impact_form.html",
                record=record, errors=errors,
                categories=FLAT_CATEGORIES, form_data=request.form,
            )
        db.session.commit()
        flash("Record updated.", "success")
        return redirect(url_for("admin.env_impacts"))

    return render_template(
        "admin/env_impact_form.html",
        record=record, errors=[], categories=FLAT_CATEGORIES, form_data={},
    )


def _parse_env_impact_form(form, existing=None):
    """Parse and validate environmental impact form data."""
    from datetime import date
    import re

    errors = []
    category   = form.get("category", "").strip()
    hazard     = form.get("hazard_type", "").strip()
    disposal   = form.get("improper_disposal_effect", "").strip()
    consequence = form.get("environmental_consequence", "").strip()
    action     = form.get("recommended_action", "").strip()
    src_title  = form.get("source_title", "").strip()
    src_org    = form.get("source_organization", "").strip()
    src_url    = form.get("source_url", "").strip()
    reviewed_at_raw = form.get("reviewed_at", "").strip()
    review_status = form.get("review_status", "pending")

    if not category:
        errors.append("Category is required.")
    if not disposal:
        errors.append("Improper disposal effect is required.")
    if not action:
        errors.append("Recommended action is required.")
    if src_url and not re.match(r"^https?://", src_url):
        errors.append("Source URL must begin with http:// or https://")
    if review_status not in ("pending", "reviewed", "inactive"):
        errors.append("Invalid review status.")

    reviewed_at = None
    if reviewed_at_raw:
        try:
            reviewed_at = date.fromisoformat(reviewed_at_raw)
        except ValueError:
            errors.append("Reviewed date must be in YYYY-MM-DD format.")

    if errors:
        return None, errors

    if existing is None:
        record = EnvironmentalImpact()
    else:
        record = existing

    record.category                  = category
    record.hazard_type               = hazard or None
    record.improper_disposal_effect  = disposal
    record.environmental_consequence = consequence or None
    record.recommended_action        = action
    record.source_title              = src_title or None
    record.source_organization       = src_org or None
    record.source_url                = src_url or None
    record.reviewed_at               = reviewed_at
    record.review_status             = review_status

    return record, []


# ── Summary API (for Chart.js) ────────────────────────────────────────────────

@bp.route("/api/summary")
@admin_required
def api_summary():
    from sqlalchemy import func

    status_counts = dict(
        db.session.query(Listing.status, func.count(Listing.id))
        .group_by(Listing.status).all()
    )
    route_counts = dict(
        db.session.query(Recommendation.route, func.count(Recommendation.id))
        .group_by(Recommendation.route).all()
    )
    category_counts = dict(
        db.session.query(Listing.category_confirmed, func.count(Listing.id))
        .group_by(Listing.category_confirmed).all()
    )

    return jsonify({
        "status_counts":   status_counts,
        "route_counts":    route_counts,
        "category_counts": category_counts,
        "total_users":     User.query.count(),
        "total_listings":  Listing.query.count(),
        "flagged":         Listing.query.filter_by(status="pending_review").count(),
    })
