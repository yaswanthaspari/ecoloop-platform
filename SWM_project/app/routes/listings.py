"""
Listing routes — create, view, edit, withdraw, dashboard.
Includes the 6-step listing workflow with AI classification,
recovery engine and EcoImpact.
"""
import json
import os
import logging
from flask import (
    Blueprint, render_template, redirect, url_for,
    flash, request, current_app, jsonify, abort,
)
from flask_login import login_required, current_user
from app import db
from app.models.listing import Listing
from app.models.partner_interest import PartnerInterest
from app.services import listing_service
from app.services.recovery_engine import (
    evaluate as engine_evaluate,
    ROUTE_DISPLAY, ROUTE_ICON,
)
from app.services.ecoimpact_service import get_ecoimpact
from app.services.image_classifier import (
    get_classifier, FLAT_CATEGORIES, CATEGORY_TAXONOMY,
)

bp = Blueprint("listings", __name__)
logger = logging.getLogger(__name__)


# ── Seller dashboard ─────────────────────────────────────────────────────────

@bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.is_admin():
        return redirect(url_for("admin.dashboard"))

    user_listings = (
        Listing.query
        .filter_by(seller_id=current_user.id)
        .order_by(Listing.created_at.desc())
        .all()
    )

    counts = {
        "total":          len(user_listings),
        "available":      sum(1 for l in user_listings if l.status == "available"),
        "pending_review": sum(1 for l in user_listings if l.status == "pending_review"),
        "draft":          sum(1 for l in user_listings if l.status == "draft"),
        "completed":      sum(1 for l in user_listings if l.status == "completed"),
        "reserved":       sum(1 for l in user_listings if l.status == "reserved"),
    }

    recent = user_listings[:5]
    return render_template(
        "listings/dashboard.html",
        user_listings=user_listings,
        counts=counts,
        recent=recent,
    )


# ── My listings ──────────────────────────────────────────────────────────────

@bp.route("/my")
@login_required
def my_listings():
    status_filter = request.args.get("status", "")
    q = Listing.query.filter_by(seller_id=current_user.id)
    if status_filter and status_filter in Listing.VALID_STATUSES:
        q = q.filter_by(status=status_filter)
    listings = q.order_by(Listing.created_at.desc()).all()
    return render_template(
        "listings/my_listings.html",
        listings=listings,
        status_filter=status_filter,
        valid_statuses=Listing.VALID_STATUSES,
    )


# ── Create listing (multi-step) ───────────────────────────────────────────────

@bp.route("/new", methods=["GET"])
@login_required
def new_listing():
    classifier = get_classifier()
    return render_template(
        "listings/create.html",
        categories=FLAT_CATEGORIES,
        taxonomy=json.dumps({k: v for k, v in CATEGORY_TAXONOMY.items()}),
        classifier_available=classifier.is_available() if classifier else False,
    )


@bp.route("/create", methods=["POST"])
@login_required
def create_listing():
    """Final submission of the multi-step form — saves everything to DB."""
    errors = []

    # ── Collect form fields ───────────────────────────────────────────────────
    title             = request.form.get("title", "").strip()
    category          = request.form.get("category_confirmed", "").strip()
    category_source   = request.form.get("category_source", "user")
    brand_model       = request.form.get("brand_model", "").strip()
    working_status    = request.form.get("working_status", "")
    physical_condition = request.form.get("physical_condition", "fair")
    defects           = request.form.get("defects", "").strip()
    repair_history    = request.form.get("repair_history", "").strip()
    additional_notes  = request.form.get("additional_notes", "").strip()
    safety_flags_raw  = request.form.get("safety_flags", "[]")
    age_years_raw     = request.form.get("age_years", "")
    repair_cost_raw   = request.form.get("estimated_repair_cost", "")
    resale_val_raw    = request.form.get("estimated_resale_value", "")
    asking_raw        = request.form.get("asking_price", "")

    # Numeric parsing (VAL-02)
    def parse_positive_float(val, label):
        if val.strip() == "":
            return None, None
        try:
            f = float(val)
            if f < 0:
                return None, f"{label} must be non-negative."
            return f, None
        except ValueError:
            return None, f"{label} must be a valid number."

    age_years, err = parse_positive_float(age_years_raw, "Age")
    if err: errors.append(err)
    repair_cost, err = parse_positive_float(repair_cost_raw, "Estimated repair cost")
    if err: errors.append(err)
    resale_value, err = parse_positive_float(resale_val_raw, "Estimated resale value")
    if err: errors.append(err)
    asking_price, err = parse_positive_float(asking_raw, "Asking price")
    if err: errors.append(err)

    # Required fields
    if not title:
        errors.append("Item title is required.")
    if not category:
        errors.append("Please confirm or select a category.")
    if not working_status:
        errors.append("Working status is required.")

    # Parse safety flags
    try:
        safety_flags = json.loads(safety_flags_raw)
    except (json.JSONDecodeError, TypeError):
        safety_flags = []

    # Parse diagnostic answers and detected components
    diagnostic_answers_raw = request.form.get("diagnostic_answers", "{}")
    try:
        diagnostic_answers = json.loads(diagnostic_answers_raw)
    except (json.JSONDecodeError, TypeError):
        diagnostic_answers = {}

    detected_components_raw = request.form.get("detected_components", "[]")
    try:
        detected_components = json.loads(detected_components_raw)
    except (json.JSONDecodeError, TypeError):
        detected_components = []

    # Image upload (VAL-03)
    image_path = None
    file = request.files.get("image") or request.files.get("image_upload_temp")
    if file and file.filename:
        try:
            image_path = listing_service.save_upload(file)
        except ValueError as exc:
            errors.append(str(exc))
    elif request.form.get("image"):
        # Image was already uploaded and saved in Step 1/2 (/classify)
        candidate = os.path.basename(request.form.get("image"))
        candidate_path = os.path.join(current_app.config["UPLOAD_FOLDER"], candidate)
        if os.path.isfile(candidate_path):
            image_path = candidate
        else:
            errors.append("Uploaded photo not found. Please re-upload your photo.")
    else:
        errors.append("An item photo is required.")

    if errors:
        classifier = get_classifier()
        return render_template(
            "listings/create.html",
            categories=FLAT_CATEGORIES,
            taxonomy=json.dumps({k: v for k, v in CATEGORY_TAXONOMY.items()}),
            classifier_available=classifier.is_available() if classifier else False,
            errors=errors,
            form_data=request.form,
        )

    # ── Run recovery engine ──────────────────────────────────────────────────
    rec_result = engine_evaluate(
        category=category,
        working_status=working_status,
        physical_condition=physical_condition,
        defects=defects,
        repair_history=repair_history,
        estimated_repair_cost=repair_cost,
        estimated_resale_value=resale_value,
        asking_price=asking_price,
        age_years=age_years,
        safety_flags=safety_flags,
        repair_ratio_threshold=current_app.config.get(
            "REPAIR_COST_RATIO_THRESHOLD", 0.60
        ),
        diagnostic_answers=diagnostic_answers,
        detected_components=detected_components,
    )

    # Determine initial listing status
    if rec_result.safety_flag or rec_result.manual_review_flag:
        initial_status = "pending_review"
    else:
        initial_status = "available"

    try:
        listing = Listing(
            seller_id=current_user.id,
            title=title,
            category_confirmed=category,
            category_source=category_source,
            brand_model=brand_model or None,
            age_years=age_years,
            working_status=working_status,
            physical_condition=physical_condition,
            defects=defects or None,
            repair_history=repair_history or None,
            estimated_repair_cost=repair_cost,
            estimated_resale_value=resale_value,
            asking_price=asking_price,
            additional_notes=additional_notes or None,
            image_path=image_path,
            status=initial_status,
        )
        db.session.add(listing)
        db.session.flush()   # get listing.id

        # Save image assessment with detected components and diagnostic findings
        predicted_cat_raw = request.form.get("predicted_category", "")
        conf_raw = request.form.get("predicted_confidence", "")
        model_ver = request.form.get("model_version", "")
        inf_status = request.form.get("inference_status", "fallback")
        if predicted_cat_raw or inf_status == "fallback" or detected_components:
            from app.models.image_assessment import ImageAssessment
            assessment = ImageAssessment(
                listing_id=listing.id,
                predicted_category=predicted_cat_raw or None,
                confidence=float(conf_raw) if conf_raw else None,
                model_version=model_ver or None,
                inference_status=inf_status,
                detected_components=json.dumps(detected_components) if detected_components else None,
                diagnostic_answers=json.dumps(diagnostic_answers) if diagnostic_answers else None,
            )
            db.session.add(assessment)

        # Save recommendation
        listing_service.save_recommendation(listing.id, rec_result)

        # Record initial status history
        from app.models.listing_status_history import ListingStatusHistory
        from datetime import datetime, timezone
        history = ListingStatusHistory(
            listing_id=listing.id,
            changed_by=current_user.id,
            old_status=None,
            new_status=initial_status,
            note="Listing created.",
        )
        db.session.add(history)

        db.session.commit()
        flash("Listing created successfully!", "success")
        return redirect(url_for("listings.detail", listing_id=listing.id))

    except Exception as exc:
        db.session.rollback()
        logger.error("Failed to save listing: %s", exc)
        flash("An error occurred while saving the listing. Please try again.", "danger")
        classifier = get_classifier()
        return render_template(
            "listings/create.html",
            categories=FLAT_CATEGORIES,
            taxonomy=json.dumps({k: v for k, v in CATEGORY_TAXONOMY.items()}),
            classifier_available=classifier.is_available() if classifier else False,
            errors=["Database error — please try again."],
            form_data=request.form,
        )


# ── Listing detail ───────────────────────────────────────────────────────────

@bp.route("/<int:listing_id>")
def detail(listing_id):
    listing = db.get_or_404(Listing, listing_id)

    # Non-public listings visible only to owner or admin
    if not listing.is_public():
        if not current_user.is_authenticated:
            abort(403)
        if not (listing.owned_by(current_user.id) or current_user.is_admin()):
            abort(403)

    eco = None
    if listing.recommendation:
        eco = get_ecoimpact(
            category=listing.category_confirmed,
            route=listing.recommendation.route,
            safety_flag=listing.recommendation.safety_flag,
        )

    existing_interest = None
    if current_user.is_authenticated:
        existing_interest = PartnerInterest.query.filter_by(
            listing_id=listing.id, user_id=current_user.id
        ).first()

    return render_template(
        "listings/detail.html",
        listing=listing,
        eco=eco,
        route_display=ROUTE_DISPLAY,
        route_icon=ROUTE_ICON,
        existing_interest=existing_interest,
    )


# ── Edit listing ─────────────────────────────────────────────────────────────

@bp.route("/<int:listing_id>/edit", methods=["GET", "POST"])
@login_required
def edit(listing_id):
    listing = db.get_or_404(Listing, listing_id)

    # Ownership check (FLOW-02, FR-02)
    if not listing.owned_by(current_user.id) and not current_user.is_admin():
        abort(403)

    if listing.status in ("completed", "rejected"):
        flash("This listing cannot be edited in its current state.", "warning")
        return redirect(url_for("listings.detail", listing_id=listing_id))

    if request.method == "POST":
        listing.title              = request.form.get("title", listing.title).strip()
        listing.brand_model        = request.form.get("brand_model", "").strip() or None
        listing.defects            = request.form.get("defects", "").strip() or None
        listing.additional_notes   = request.form.get("additional_notes", "").strip() or None
        listing.asking_price       = _safe_float(request.form.get("asking_price"))

        from datetime import datetime, timezone
        listing.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        flash("Listing updated.", "success")
        return redirect(url_for("listings.detail", listing_id=listing_id))

    return render_template(
        "listings/edit.html",
        listing=listing,
        categories=FLAT_CATEGORIES,
    )


# ── Withdraw listing ─────────────────────────────────────────────────────────

@bp.route("/<int:listing_id>/withdraw", methods=["POST"])
@login_required
def withdraw(listing_id):
    listing = db.get_or_404(Listing, listing_id)

    if not listing.owned_by(current_user.id) and not current_user.is_admin():
        abort(403)

    if listing.status in ("withdrawn", "completed", "rejected"):
        flash("This listing cannot be withdrawn in its current state.", "warning")
    else:
        listing_service.change_status(listing, "withdrawn", current_user.id,
                                      note="Withdrawn by seller.")
        db.session.commit()
        flash("Listing withdrawn.", "info")

    return redirect(url_for("listings.my_listings"))


# ── Express interest ─────────────────────────────────────────────────────────

@bp.route("/<int:listing_id>/interest", methods=["POST"])
@login_required
def express_interest(listing_id):
    listing = db.get_or_404(Listing, listing_id)

    if not listing.is_public():
        abort(404)

    if listing.seller_id == current_user.id:
        flash("You cannot express interest in your own listing.", "warning")
        return redirect(url_for("listings.detail", listing_id=listing_id))

    if not current_user.can_express_interest():
        flash("Only buyers and recovery partners can express interest.", "warning")
        return redirect(url_for("listings.detail", listing_id=listing_id))

    # Prevent duplicate active interests (FLOW-03)
    existing = PartnerInterest.query.filter_by(
        listing_id=listing_id,
        user_id=current_user.id,
        status="pending",
    ).first()
    if existing:
        flash("You have already expressed interest in this listing.", "info")
        return redirect(url_for("listings.detail", listing_id=listing_id))

    message       = request.form.get("message", "").strip()
    interest_type = request.form.get("interest_type", "buy")
    interest = PartnerInterest(
        listing_id=listing_id,
        user_id=current_user.id,
        message=message or None,
        interest_type=interest_type,
        status="pending",
    )
    db.session.add(interest)
    db.session.commit()
    flash("Your interest has been recorded. The seller will be notified.", "success")
    return redirect(url_for("listings.detail", listing_id=listing_id))


# ── Classify image (AJAX endpoint) ───────────────────────────────────────────

@bp.route("/classify", methods=["POST"])
@login_required
def classify_image():
    """
    Accepts a multipart image upload and returns classification JSON.
    Called by the multi-step form via fetch().
    """
    file = request.files.get("image")
    if not file or file.filename == "":
        return jsonify({"error": "No image provided."}), 400

    try:
        temp_name = listing_service.save_upload(file)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    full_path = os.path.join(current_app.config["UPLOAD_FOLDER"], temp_name)

    classifier = get_classifier()
    if not classifier:
        # Remove temp file
        _try_remove(full_path)
        return jsonify({
            "inference_status": "fallback",
            "message": "Classifier not initialised. Please select the category manually.",
            "temp_path": temp_name,
        })

    result = classifier.classify(full_path)

    return jsonify({
        "predicted_category":   result.predicted_category,
        "predicted_label":      result.predicted_label,
        "confidence":           result.confidence,
        "model_version":        result.model_version,
        "inference_status":     result.inference_status,
        "message":              result.message,
        "requires_confirmation": result.requires_confirmation,
        "safety_sensitive":     result.safety_sensitive,
        "detected_components":  result.detected_components,
        "visual_anomalies":     result.visual_anomalies,
        "diagnostic_questions": result.diagnostic_questions,
        "temp_path":            temp_name,
    })


@bp.route("/evaluate", methods=["POST"])
@login_required
def evaluate_preview():
    """AJAX endpoint for evaluating recovery assessment in Step 4 before creation."""
    data = request.get_json(silent=True) or request.form

    category           = data.get("category_confirmed") or data.get("category") or data.get("category_select", "")
    working_status     = data.get("working_status", "")
    physical_condition = data.get("physical_condition", "fair")
    defects            = data.get("defects", "")
    repair_history     = data.get("repair_history", "")
    repair_cost        = _safe_float(data.get("estimated_repair_cost"))
    resale_value       = _safe_float(data.get("estimated_resale_value"))
    asking_price       = _safe_float(data.get("asking_price"))
    age_years          = _safe_float(data.get("age_years"))

    safety_flags_raw = data.get("safety_flags", [])
    if isinstance(safety_flags_raw, str):
        try:
            safety_flags = json.loads(safety_flags_raw)
        except Exception:
            safety_flags = []
    else:
        safety_flags = safety_flags_raw

    diagnostic_answers_raw = data.get("diagnostic_answers", {})
    if isinstance(diagnostic_answers_raw, str):
        try:
            diagnostic_answers = json.loads(diagnostic_answers_raw)
        except Exception:
            diagnostic_answers = {}
    else:
        diagnostic_answers = diagnostic_answers_raw or {}

    detected_components_raw = data.get("detected_components", [])
    if isinstance(detected_components_raw, str):
        try:
            detected_components = json.loads(detected_components_raw)
        except Exception:
            detected_components = []
    else:
        detected_components = detected_components_raw or []

    res = engine_evaluate(
        category=category,
        working_status=working_status,
        physical_condition=physical_condition,
        defects=defects,
        repair_history=repair_history,
        estimated_repair_cost=repair_cost,
        estimated_resale_value=resale_value,
        asking_price=asking_price,
        age_years=age_years,
        safety_flags=safety_flags,
        repair_ratio_threshold=current_app.config.get(
            "REPAIR_COST_RATIO_THRESHOLD", 0.60
        ),
        diagnostic_answers=diagnostic_answers,
        detected_components=detected_components,
    )

    return jsonify({
        "route":                    res.route,
        "route_title":              ROUTE_DISPLAY.get(res.route, res.route.replace("_", " ").title()),
        "route_icon":               ROUTE_ICON.get(res.route, "bi-box"),
        "suitability_score":        res.suitability_score,
        "reason_codes":             res.reason_codes,
        "explanation":              res.explanation,
        "safety_flag":              res.safety_flag,
        "manual_review_flag":       res.manual_review_flag,
        "missing_info":             res.missing_info,
        "salvageable_components":   res.salvageable_components,
        "repair_target_components": res.repair_target_components,
        "diagnostic_summary":       res.diagnostic_summary,
    })


@bp.route("/ecoimpact-preview", methods=["GET", "POST"])
def ecoimpact_preview():
    """AJAX endpoint for fetching EcoImpact knowledge in Step 5 before creation."""
    category    = request.values.get("category", "")
    route       = request.values.get("route", "manual_review")
    safety_flag = request.values.get("safety_flag", "false").lower() in ("true", "1", "yes")

    res = get_ecoimpact(category=category, route=route, safety_flag=safety_flag)
    return jsonify({
        "category":            res.category,
        "records_found":       res.records_found,
        "impacts":             res.impacts,
        "route_advice":        res.route_advice,
        "unavailable_message": res.unavailable_message,
    })


# ── Helpers ───────────────────────────────────────────────────────────────────

def _safe_float(val):
    if val is None or str(val).strip() == "":
        return None
    try:
        return float(val)
    except ValueError:
        return None


def _try_remove(path):
    try:
        os.remove(path)
    except OSError:
        pass
