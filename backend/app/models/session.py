from datetime import datetime, timezone

from app.extensions import db


class Session(db.Model):
    __tablename__ = "sessions"

    id = db.Column(db.Integer, primary_key=True)
    crew_id = db.Column(db.Integer, db.ForeignKey("crews.id"), nullable=False)
    title = db.Column(db.String(160), nullable=False)
    activity_type = db.Column(db.String(20), nullable=False, default="walk")
    scheduled_start = db.Column(db.DateTime(timezone=True), nullable=False)
    expected_distance_m = db.Column(db.Integer)
    meeting_point_name = db.Column(db.String(180), nullable=False)
    meeting_latitude = db.Column(db.Float, nullable=False)
    meeting_longitude = db.Column(db.Float, nullable=False)
    difficulty = db.Column(db.String(40))
    status = db.Column(db.String(20), nullable=False, default="scheduled")
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    crew = db.relationship("Crew", back_populates="sessions")
    creator = db.relationship("User")
    attendance = db.relationship("SessionAttendance", back_populates="session", cascade="all, delete-orphan")

    def to_dict(self, include_attendees=False):
        data = {
            "id": self.id,
            "crew_id": self.crew_id,
            "crew_name": self.crew.name if self.crew else None,
            "title": self.title,
            "activity_type": self.activity_type,
            "scheduled_start": self.scheduled_start.isoformat(),
            "expected_distance_m": self.expected_distance_m,
            "meeting_point_name": self.meeting_point_name,
            "meeting_latitude": self.meeting_latitude,
            "meeting_longitude": self.meeting_longitude,
            "difficulty": self.difficulty,
            "status": self.status,
            "attendee_count": len(self.attendance),
        }
        if include_attendees:
            data["attendees"] = [item.to_dict() for item in self.attendance]
        return data


class SessionAttendance(db.Model):
    __tablename__ = "session_attendance"
    __table_args__ = (db.UniqueConstraint("session_id", "user_id", name="uq_session_attendance"),)

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("sessions.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="going")
    joined_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    checked_in_at = db.Column(db.DateTime(timezone=True))
    checked_out_at = db.Column(db.DateTime(timezone=True))

    session = db.relationship("Session", back_populates="attendance")
    user = db.relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "name": self.user.name if self.user else None,
            "status": self.status,
            "joined_at": self.joined_at.isoformat(),
            "checked_in_at": self.checked_in_at.isoformat() if self.checked_in_at else None,
            "checked_out_at": self.checked_out_at.isoformat() if self.checked_out_at else None,
        }

