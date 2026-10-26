"""Listing model."""
from datetime import datetime, timezone
from app import db


class Listing(db.Model):
    __tablename__ = "listings"

    # Valid status values (FLOW-01)
    VALID_STATUSES = (
        "draft", "pending_review", "available", "reserved",
        "completed", "withdrawn", "rejected",
    )

    id                    = db.Column(db.Integer, primary_key=True)
    seller_id             = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title                 = db.Column(db.String(200), nullable=False)
    category_confirmed    = db.Column(db.String(100), nullable=False, index=True)
    brand_model           = db.Column(db.String(200))
    age_years             = db.Column(db.Float)
    working_status        = db.Column(
        db.Enum("working", "not_working", "partially_working", name="working_status_enum"),
        nullable=False,
    )
    physical_condition    = db.Column(
        db.Enum("excellent", "good", "fair", "poor", name="physical_condition_enum"),
        nullable=False,
        default="fair",
    )
    defects               = db.Column(db.Text)
    repair_history        = db.Column(db.Text)
    estimated_repair_cost = db.Column(db.Float)
    estimated_resale_value = db.Column(db.Float)
    asking_price          = db.Column(db.Float)
    additional_notes      = db.Column(db.Text)
    image_path            = db.Column(db.String(500))
    status                = db.Column(db.String(30), nullable=False,
                                      default="draft", index=True)
    category_source       = db.Column(
        db.Enum("model", "user", name="category_source_enum"),
        default="user",
    )
    created_at            = db.Column(db.DateTime,
                                      default=lambda: datetime.now(timezone.utc))
    updated_at            = db.Column(db.DateTime,
                                      default=lambda: datetime.now(timezone.utc),
                                      onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    image_assessment = db.relationship(
        "ImageAssessment", backref="listing", uselist=False, cascade="all, delete-orphan"
    )
    recommendation = db.relationship(
        "Recommendation", backref="listing", uselist=False, cascade="all, delete-orphan"
    )
    interests = db.relationship(
        "PartnerInterest", backref="listing", lazy="dynamic", cascade="all, delete-orphan"
    )
    status_history = db.relationship(
        "ListingStatusHistory", backref="listing", lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def is_public(self) -> bool:
        """Listings visible in the public marketplace."""
        return self.status == "available"

    def owned_by(self, user_id: int) -> bool:
        return self.seller_id == user_id

    def __repr__(self):
        return f"<Listing {self.id}: {self.title} [{self.status}]>"
