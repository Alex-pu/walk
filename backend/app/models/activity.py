from datetime import datetime, timezone

from app.extensions import db


class Activity(db.Model):
    __tablename__ = "activities"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey("sessions.id"))
    activity_type = db.Column(db.String(20), nullable=False)
    started_at = db.Column(db.DateTime(timezone=True), nullable=False)
    finished_at = db.Column(db.DateTime(timezone=True), nullable=False)
    duration_seconds = db.Column(db.Integer, nullable=False)
    distance_meters = db.Column(db.Float, nullable=False)
    source = db.Column(db.String(40), nullable=False, default="web_gps")
    start_latitude = db.Column(db.Float)
    start_longitude = db.Column(db.Float)
    end_latitude = db.Column(db.Float)
    end_longitude = db.Column(db.Float)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = db.relationship("User")
    session = db.relationship("Session")
    route_points = db.relationship("ActivityRoutePoint", back_populates="activity", cascade="all, delete-orphan")

    def to_dict(self, include_route=False):
        data = {
            "id": self.id,
            "session_id": self.session_id,
            "activity_type": self.activity_type,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "duration_seconds": self.duration_seconds,
            "distance_meters": self.distance_meters,
            "source": self.source,
        }
        if include_route:
            data["route_points"] = [point.to_dict() for point in self.route_points]
        return data


class ActivityRoutePoint(db.Model):
    __tablename__ = "activity_route_points"

    id = db.Column(db.Integer, primary_key=True)
    activity_id = db.Column(db.Integer, db.ForeignKey("activities.id"), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    accuracy = db.Column(db.Float)
    recorded_at = db.Column(db.DateTime(timezone=True), nullable=False)
    sequence_number = db.Column(db.Integer, nullable=False)

    activity = db.relationship("Activity", back_populates="route_points")

    def to_dict(self):
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "accuracy": self.accuracy,
            "recorded_at": self.recorded_at.isoformat(),
            "sequence_number": self.sequence_number,
        }

