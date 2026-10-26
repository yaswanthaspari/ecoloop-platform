"""ImageAssessment model — stores classifier output per listing."""
from datetime import datetime, timezone
from app import db


class ImageAssessment(db.Model):
    __tablename__ = "image_assessments"

    id                 = db.Column(db.Integer, primary_key=True)
    listing_id         = db.Column(db.Integer, db.ForeignKey("listings.id"),
                                   nullable=False, unique=True)
    predicted_category = db.Column(db.String(100))
    confidence         = db.Column(db.Float)
    model_version      = db.Column(db.String(50))
    inference_status   = db.Column(
        db.Enum("success", "fallback", "failed", name="inference_status_enum"),
        default="fallback",
    )
    detected_components = db.Column(db.Text)   # JSON list of detected components
    diagnostic_answers  = db.Column(db.Text)   # JSON dict of user answers to diagnostic questions
    created_at         = db.Column(db.DateTime,
                                   default=lambda: datetime.now(timezone.utc))

    @property
    def components_list(self):
        import json
        if not self.detected_components:
            return []
        try:
            return json.loads(self.detected_components)
        except Exception:
            return []

    @property
    def answers_dict(self):
        import json
        if not self.diagnostic_answers:
            return {}
        try:
            return json.loads(self.diagnostic_answers)
        except Exception:
            return {}

    def __repr__(self):
        return (
            f"<ImageAssessment listing={self.listing_id} "
            f"cat={self.predicted_category} conf={self.confidence}>"
        )
