"""ListingStatusHistory model — audit trail for status changes (FLOW-04)."""
from datetime import datetime, timezone
from app import db


class ListingStatusHistory(db.Model):
    __tablename__ = "listing_status_history"

    id         = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey("listings.id"), nullable=False,
                           index=True)
    changed_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    old_status = db.Column(db.String(30))
    new_status = db.Column(db.String(30), nullable=False)
    note       = db.Column(db.Text)
    changed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship to user
    changer    = db.relationship("User", foreign_keys=[changed_by])

    def __repr__(self):
        return (
            f"<StatusHistory listing={self.listing_id} "
            f"{self.old_status}→{self.new_status}>"
        )
