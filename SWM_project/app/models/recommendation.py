"""Recommendation model — stores recovery engine output."""
from datetime import datetime, timezone
from app import db


class Recommendation(db.Model):
    __tablename__ = "recommendations"

    VALID_ROUTES = (
        "reuse_resale",
        "repair",
        "refurbishment",
        "parts_recovery",
        "recycling",
        "manual_review",
        "safety_review",
    )

    id               = db.Column(db.Integer, primary_key=True)
    listing_id       = db.Column(db.Integer, db.ForeignKey("listings.id"),
                                 nullable=False, unique=True)
    route            = db.Column(db.String(50), nullable=False)
    suitability_score = db.Column(db.Integer)          # 0–100, rule-based only
    reason_codes     = db.Column(db.Text)               # JSON-serialised list
    explanation      = db.Column(db.Text)
    safety_flag      = db.Column(db.Boolean, default=False)
    manual_review_flag = db.Column(db.Boolean, default=False)
    missing_info     = db.Column(db.Text)               # JSON list of missing fields
    created_at       = db.Column(db.DateTime,
                                 default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Recommendation listing={self.listing_id} route={self.route}>"
