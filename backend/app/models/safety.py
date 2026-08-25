from datetime import datetime, timezone

from app.extensions import db


class UserReport(db.Model):
    __tablename__ = "user_reports"

    id = db.Column(db.Integer, primary_key=True)
    reporter_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    reported_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    crew_id = db.Column(db.Integer, db.ForeignKey("crews.id"))
    session_id = db.Column(db.Integer, db.ForeignKey("sessions.id"))
    reason = db.Column(db.String(80), nullable=False)
    details = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False, default="open")
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    reporter = db.relationship("User", foreign_keys=[reporter_user_id])
    reported = db.relationship("User", foreign_keys=[reported_user_id])
    crew = db.relationship("Crew")

    def to_dict(self):
        return {
            "id": self.id,
            "reporter_user_id": self.reporter_user_id,
            "reporter_name": self.reporter.name if self.reporter else None,
            "reported_user_id": self.reported_user_id,
            "reported_name": self.reported.name if self.reported else None,
            "crew_id": self.crew_id,
            "crew_name": self.crew.name if self.crew else None,
            "session_id": self.session_id,
            "reason": self.reason,
            "details": self.details,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }


class UserBlock(db.Model):
    __tablename__ = "user_blocks"
    __table_args__ = (db.UniqueConstraint("blocker_user_id", "blocked_user_id", name="uq_user_block"),)

    id = db.Column(db.Integer, primary_key=True)
    blocker_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    blocked_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    blocker = db.relationship("User", foreign_keys=[blocker_user_id])
    blocked = db.relationship("User", foreign_keys=[blocked_user_id])

    def to_dict(self):
        return {
            "id": self.id,
            "blocked_user_id": self.blocked_user_id,
            "created_at": self.created_at.isoformat(),
        }
