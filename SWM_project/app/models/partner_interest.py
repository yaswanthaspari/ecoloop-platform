"""PartnerInterest model — buyer / recovery-partner interest in a listing."""
from datetime import datetime, timezone
from app import db


class PartnerInterest(db.Model):
    __tablename__ = "partner_interests"

    id         = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey("listings.id"), nullable=False)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"),    nullable=False)
    message    = db.Column(db.Text)
    interest_type = db.Column(
        db.Enum("buy", "recover", "partner", name="interest_type_enum"),
        default="buy",
    )
    status     = db.Column(
        db.Enum("pending", "accepted", "declined", "withdrawn", name="interest_status_enum"),
        nullable=False,
        default="pending",
    )
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Unique constraint: one active interest per user per listing (FLOW-03)
    __table_args__ = (
        db.Index("ix_partner_interests_listing_user", "listing_id", "user_id"),
    )

    def __repr__(self):
        return f"<PartnerInterest listing={self.listing_id} user={self.user_id}>"
