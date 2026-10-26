"""Main / public routes — landing page."""
from flask import Blueprint, render_template
from app.models.listing import Listing

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    # Show up to 6 recent available listings for the homepage
    recent = (
        Listing.query
        .filter_by(status="available")
        .order_by(Listing.created_at.desc())
        .limit(6)
        .all()
    )
    return render_template("main/index.html", recent_listings=recent)


@bp.route("/about")
def about():
    return render_template("main/about.html")
