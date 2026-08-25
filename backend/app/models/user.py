from datetime import datetime, timezone

from secrets import token_urlsafe
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(50))
    profile_photo = db.Column(db.String(500))
    neighborhood = db.Column(db.String(120), nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    platform_role = db.Column(db.String(20), nullable=False, default="member")
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self, include_private_location=False):
        data = {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "profile_photo": self.profile_photo,
            "neighborhood": self.neighborhood,
            "platform_role": self.platform_role,
            "created_at": self.created_at.isoformat(),
        }
        if include_private_location:
            data["latitude"] = self.latitude
            data["longitude"] = self.longitude
        return data


class PasswordResetToken(db.Model):
    __tablename__ = "password_reset_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    token = db.Column(db.String(160), nullable=False, unique=True, index=True)
    used_at = db.Column(db.DateTime(timezone=True))
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = db.relationship("User")

    @classmethod
    def create(cls, user_id, expires_at):
        return cls(user_id=user_id, token=token_urlsafe(48), expires_at=expires_at)

    def is_usable(self):
        expires_at = self.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return self.used_at is None and expires_at > datetime.now(timezone.utc)
