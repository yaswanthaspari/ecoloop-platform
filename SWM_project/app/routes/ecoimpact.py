"""EcoImpact public awareness page."""
from flask import Blueprint, render_template, request
from app.models.environmental_impact import EnvironmentalImpact
from app.services.image_classifier import FLAT_CATEGORIES

bp = Blueprint("ecoimpact", __name__)


@bp.route("/")
def index():
    q_category = request.args.get("category", "").strip()
    q_hazard   = request.args.get("hazard", "").strip()

    query = EnvironmentalImpact.query.filter_by(review_status="reviewed")

    if q_category:
        query = query.filter_by(category=q_category)
    if q_hazard:
        query = query.filter(EnvironmentalImpact.hazard_type.ilike(f"%{q_hazard}%"))

    records = query.order_by(EnvironmentalImpact.category).all()

    # Group by category
    by_category = {}
    for rec in records:
        by_category.setdefault(rec.category, []).append(rec)

    return render_template(
        "ecoimpact/index.html",
        by_category=by_category,
        categories=FLAT_CATEGORIES,
        filters={"category": q_category, "hazard": q_hazard},
        total_records=len(records),
    )
