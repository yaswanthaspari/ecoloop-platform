"""EnvironmentalImpact model — EcoImpact knowledge base."""
from datetime import datetime, timezone
from app import db


class EnvironmentalImpact(db.Model):
    __tablename__ = "environmental_impacts"

    id                       = db.Column(db.Integer, primary_key=True)
    category                 = db.Column(db.String(100), nullable=False, index=True)
    hazard_type              = db.Column(db.String(100))
    improper_disposal_effect = db.Column(db.Text)
    environmental_consequence = db.Column(db.Text)
    recommended_action       = db.Column(db.Text)
    source_title             = db.Column(db.String(300))
    source_organization      = db.Column(db.String(200))
    source_url               = db.Column(db.String(500))
    reviewed_at              = db.Column(db.Date)
    review_status            = db.Column(
        db.Enum("pending", "reviewed", "inactive", name="review_status_enum"),
        nullable=False,
        default="pending",
        index=True,
    )
    created_at               = db.Column(db.DateTime,
                                         default=lambda: datetime.now(timezone.utc))
    updated_at               = db.Column(db.DateTime,
                                         default=lambda: datetime.now(timezone.utc),
                                         onupdate=lambda: datetime.now(timezone.utc))

    def is_active(self) -> bool:
        return self.review_status == "reviewed"

    def __repr__(self):
        return f"<EnvironmentalImpact {self.category} [{self.review_status}]>"
