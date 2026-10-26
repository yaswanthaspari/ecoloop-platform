"""REST-style JSON API routes."""
import json
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models.listing import Listing
from app.models.recommendation import Recommendation
from app.services.ecoimpact_service import get_ecoimpact
from app.services.recovery_engine import evaluate as engine_evaluate, ROUTE_DISPLAY
from app.services.image_classifier import get_classifier
from app.services import listing_service

bp = Blueprint("api", __name__)


# ── Auth ──────────────────────────────────────────────────────────────────────

@bp.route("/auth/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    # Delegate to auth logic — kept thin
    from app.routes.auth import ALLOWED_PUBLIC_ROLES
    from app.models.user import User

    name     = (data.get("name") or "").strip()
    email    = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role     = data.get("role", "seller")

    errors = []
    if not name: errors.append("name required")
    if not email or "@" not in email: errors.append("valid email required")
    if len(password) < 8: errors.append("password must be ≥8 chars")
    if role not in ALLOWED_PUBLIC_ROLES: errors.append("invalid role")

    if errors:
        return jsonify({"errors": errors}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"errors": ["Email already registered."]}), 409

    user = User(name=name, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "Account created.", "user_id": user.id}), 201


@bp.route("/auth/login", methods=["POST"])
def login():
    from flask_login import login_user
    from app.models.user import User

    data  = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    pw    = data.get("password") or ""
    user  = User.query.filter_by(email=email).first()

    if not user or not user.check_password(pw) or not user.is_active_account:
        return jsonify({"error": "Invalid credentials."}), 401

    login_user(user)
    return jsonify({"message": "Logged in.", "role": user.role})


@bp.route("/auth/logout", methods=["POST"])
@login_required
def logout():
    from flask_login import logout_user
    logout_user()
    return jsonify({"message": "Logged out."})


# ── Listings ──────────────────────────────────────────────────────────────────

@bp.route("/listings", methods=["GET"])
def get_listings():
    page = request.args.get("page", 1, type=int)
    q    = request.args.get("q", "")
    cat  = request.args.get("category", "")

    query = Listing.query.filter_by(status="available")
    if q:
        query = query.filter(Listing.title.ilike(f"%{q}%"))
    if cat:
        query = query.filter_by(category_confirmed=cat)

    p = query.order_by(Listing.created_at.desc()).paginate(page=page, per_page=20)
    return jsonify({
        "listings": [_listing_summary(l) for l in p.items],
        "total":    p.total,
        "pages":    p.pages,
        "page":     p.page,
    })


@bp.route("/listings/<int:listing_id>", methods=["GET"])
def get_listing(listing_id):
    listing = db.get_or_404(Listing, listing_id)
    if not listing.is_public():
        if not current_user.is_authenticated:
            return jsonify({"error": "Not authorised."}), 403
        if not (listing.owned_by(current_user.id) or current_user.is_admin()):
            return jsonify({"error": "Not authorised."}), 403
    return jsonify(_listing_detail(listing))


@bp.route("/listings/<int:listing_id>/ecoimpact", methods=["GET"])
def get_ecoimpact_api(listing_id):
    listing = db.get_or_404(Listing, listing_id)
    rec = listing.recommendation
    eco = get_ecoimpact(
        category=listing.category_confirmed,
        route=rec.route if rec else "manual_review",
        safety_flag=rec.safety_flag if rec else False,
    )
    return jsonify({
        "category":    eco.category,
        "records_found": eco.records_found,
        "impacts":     eco.impacts,
        "route_advice": eco.route_advice,
        "unavailable_message": eco.unavailable_message,
    })


@bp.route("/listings/<int:listing_id>/classify", methods=["POST"])
@login_required
def classify(listing_id):
    listing = db.get_or_404(Listing, listing_id)
    if not listing.owned_by(current_user.id) and not current_user.is_admin():
        return jsonify({"error": "Forbidden."}), 403

    import os
    clf = get_classifier()
    if not clf:
        return jsonify({"inference_status": "fallback", "message": "Classifier not available."}), 200

    image_full = os.path.join(current_app.config["UPLOAD_FOLDER"],
                              listing.image_path or "")
    if not listing.image_path or not os.path.exists(image_full):
        return jsonify({"error": "No image associated with this listing."}), 400

    result = clf.classify(image_full)
    assessment = listing_service.save_assessment(listing.id, result)
    db.session.commit()

    return jsonify({
        "predicted_category": result.predicted_category,
        "confidence":         result.confidence,
        "model_version":      result.model_version,
        "inference_status":   result.inference_status,
        "message":            result.message,
    })


@bp.route("/listings/<int:listing_id>/recommend", methods=["POST"])
@login_required
def recommend(listing_id):
    listing = db.get_or_404(Listing, listing_id)
    if not listing.owned_by(current_user.id) and not current_user.is_admin():
        return jsonify({"error": "Forbidden."}), 403

    data = request.get_json(silent=True) or {}
    safety_flags = data.get("safety_flags", [])

    result = engine_evaluate(
        category=listing.category_confirmed,
        working_status=listing.working_status,
        physical_condition=listing.physical_condition,
        defects=listing.defects,
        repair_history=listing.repair_history,
        estimated_repair_cost=listing.estimated_repair_cost,
        estimated_resale_value=listing.estimated_resale_value,
        asking_price=listing.asking_price,
        age_years=listing.age_years,
        safety_flags=safety_flags,
        repair_ratio_threshold=current_app.config.get("REPAIR_COST_RATIO_THRESHOLD", 0.60),
    )
    listing_service.save_recommendation(listing.id, result)
    db.session.commit()

    return jsonify({
        "route":            result.route,
        "route_display":    ROUTE_DISPLAY.get(result.route, result.route),
        "suitability_score": result.suitability_score,
        "reason_codes":     result.reason_codes,
        "explanation":      result.explanation,
        "safety_flag":      result.safety_flag,
        "manual_review_flag": result.manual_review_flag,
    })


@bp.route("/my-listings", methods=["GET"])
@login_required
def my_listings():
    listings = (
        Listing.query
        .filter_by(seller_id=current_user.id)
        .order_by(Listing.created_at.desc())
        .all()
    )
    return jsonify({"listings": [_listing_summary(l) for l in listings]})


@bp.route("/admin/summary", methods=["GET"])
@login_required
def admin_summary():
    if not current_user.is_admin():
        return jsonify({"error": "Forbidden."}), 403
    from sqlalchemy import func
    status_counts = dict(
        db.session.query(Listing.status, func.count(Listing.id))
        .group_by(Listing.status).all()
    )
    return jsonify({"status_counts": status_counts, "total": Listing.query.count()})


# ── Helpers ───────────────────────────────────────────────────────────────────

def _listing_summary(l):
    return {
        "id":             l.id,
        "title":          l.title,
        "category":       l.category_confirmed,
        "working_status": l.working_status,
        "asking_price":   l.asking_price,
        "status":         l.status,
        "route":          l.recommendation.route if l.recommendation else None,
        "image_path":     l.image_path,
        "created_at":     l.created_at.isoformat() if l.created_at else None,
    }


def _listing_detail(l):
    rec = l.recommendation
    return {
        **_listing_summary(l),
        "brand_model":   l.brand_model,
        "age_years":     l.age_years,
        "physical_condition": l.physical_condition,
        "defects":       l.defects,
        "repair_history": l.repair_history,
        "estimated_repair_cost": l.estimated_repair_cost,
        "estimated_resale_value": l.estimated_resale_value,
        "recommendation": {
            "route":          rec.route,
            "suitability_score": rec.suitability_score,
            "reason_codes":   json.loads(rec.reason_codes or "[]"),
            "explanation":    rec.explanation,
            "safety_flag":    rec.safety_flag,
            "manual_review_flag": rec.manual_review_flag,
        } if rec else None,
    }
