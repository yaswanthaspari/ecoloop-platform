"""Marketplace routes — browse, search, filter listings."""
from flask import Blueprint, render_template, request
from app.models.listing import Listing
from app.models.recommendation import Recommendation
from app.services.recovery_engine import ROUTE_DISPLAY, ROUTE_ICON

bp = Blueprint("marketplace", __name__)


@bp.route("/")
def index():
    # ── Filters from query string ─────────────────────────────────────────
    q_title    = request.args.get("q", "").strip()
    q_category = request.args.get("category", "").strip()
    q_working  = request.args.get("working_status", "").strip()
    q_route    = request.args.get("route", "").strip()
    q_min      = request.args.get("price_min", "").strip()
    q_max      = request.args.get("price_max", "").strip()
    sort_by    = request.args.get("sort", "newest")
    page       = request.args.get("page", 1, type=int)

    query = Listing.query.filter_by(status="available")

    if q_title:
        query = query.filter(Listing.title.ilike(f"%{q_title}%"))
    if q_category:
        query = query.filter(Listing.category_confirmed == q_category)
    if q_working:
        query = query.filter(Listing.working_status == q_working)
    if q_min:
        try:
            query = query.filter(Listing.asking_price >= float(q_min))
        except ValueError:
            pass
    if q_max:
        try:
            query = query.filter(Listing.asking_price <= float(q_max))
        except ValueError:
            pass

    # Route filter requires join with recommendations
    if q_route:
        query = query.join(Recommendation).filter(Recommendation.route == q_route)

    # Sorting
    if sort_by == "price_asc":
        query = query.order_by(Listing.asking_price.asc())
    elif sort_by == "price_desc":
        query = query.order_by(Listing.asking_price.desc())
    else:
        query = query.order_by(Listing.created_at.desc())

    pagination = query.paginate(page=page, per_page=12, error_out=False)

    from app.services.image_classifier import FLAT_CATEGORIES
    from app.models.recommendation import Recommendation as Rec

    available_routes = [r for r in Rec.VALID_ROUTES if r not in ("manual_review", "safety_review")]

    return render_template(
        "marketplace/index.html",
        pagination=pagination,
        listings=pagination.items,
        categories=FLAT_CATEGORIES,
        available_routes=available_routes,
        route_display=ROUTE_DISPLAY,
        route_icon=ROUTE_ICON,
        filters={
            "q": q_title, "category": q_category,
            "working_status": q_working, "route": q_route,
            "price_min": q_min, "price_max": q_max, "sort": sort_by,
        },
    )
