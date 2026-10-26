"""User model."""
from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id           = db.Column(db.Integer, primary_key=True)
    name         = db.Column(db.String(120), nullable=False)
    email        = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role         = db.Column(
        db.Enum("seller", "buyer", "recovery_partner", "admin", name="user_role"),
        nullable=False,
        default="seller",
    )
    contact      = db.Column(db.String(255))
    is_active_account = db.Column(db.Boolean, default=True, nullable=False)
    created_at   = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    listings     = db.relationship("Listing", backref="seller", lazy="dynamic",
                                   foreign_keys="Listing.seller_id")
    interests    = db.relationship("PartnerInterest", backref="interested_user",
                                   lazy="dynamic", foreign_keys="PartnerInterest.user_id")

    # ── Flask-Login requires is_active property ──────────────────────────────
    @property
    def is_active(self):
        return self.is_active_account

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def is_admin(self) -> bool:
        return self.role == "admin"

    def can_express_interest(self) -> bool:
        return self.role in ("buyer", "recovery_partner")

    def __repr__(self):
        return f"<User {self.email} [{self.role}]>"
