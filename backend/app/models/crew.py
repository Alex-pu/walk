from datetime import datetime, timezone

from app.extensions import db


class Crew(db.Model):
    __tablename__ = "crews"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text)
    activity_type = db.Column(db.String(20), nullable=False, default="walk")
    visibility = db.Column(db.String(20), nullable=False, default="public")
    meeting_point_name = db.Column(db.String(180), nullable=False)
    meeting_latitude = db.Column(db.Float, nullable=False)
    meeting_longitude = db.Column(db.Float, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    creator = db.relationship("User")
    members = db.relationship("CrewMember", back_populates="crew", cascade="all, delete-orphan")
    sessions = db.relationship("Session", back_populates="crew", cascade="all, delete-orphan")

    def to_dict(self, include_members=False):
        data = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "activity_type": self.activity_type,
            "visibility": self.visibility,
            "meeting_point_name": self.meeting_point_name,
            "meeting_latitude": self.meeting_latitude,
            "meeting_longitude": self.meeting_longitude,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "member_count": len(self.members),
        }
        if include_members:
            data["members"] = [member.to_dict() for member in self.members]
        return data


class CrewMember(db.Model):
    __tablename__ = "crew_members"
    __table_args__ = (db.UniqueConstraint("crew_id", "user_id", name="uq_crew_member"),)

    id = db.Column(db.Integer, primary_key=True)
    crew_id = db.Column(db.Integer, db.ForeignKey("crews.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="member")
    status = db.Column(db.String(20), nullable=False, default="active")
    joined_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    crew = db.relationship("Crew", back_populates="members")
    user = db.relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "crew_id": self.crew_id,
            "user_id": self.user_id,
            "name": self.user.name if self.user else None,
            "role": self.role,
            "status": self.status,
            "joined_at": self.joined_at.isoformat(),
        }


class CrewApplication(db.Model):
    __tablename__ = "crew_applications"

    id = db.Column(db.Integer, primary_key=True)
    applicant_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    crew_id = db.Column(db.Integer, db.ForeignKey("crews.id"))
    proposed_name = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text)
    activity_type = db.Column(db.String(20), nullable=False, default="walk")
    visibility = db.Column(db.String(20), nullable=False, default="public")
    meeting_point_name = db.Column(db.String(180), nullable=False)
    meeting_latitude = db.Column(db.Float, nullable=False)
    meeting_longitude = db.Column(db.Float, nullable=False)
    locality = db.Column(db.String(120), nullable=False)
    id_number = db.Column(db.String(80), nullable=False)
    selfie_filename = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending")
    admin_note = db.Column(db.Text)
    reviewed_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    reviewed_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    applicant = db.relationship("User", foreign_keys=[applicant_user_id])
    reviewer = db.relationship("User", foreign_keys=[reviewed_by])
    crew = db.relationship("Crew")

    def to_dict(self, include_sensitive=False):
        data = {
            "id": self.id,
            "applicant_user_id": self.applicant_user_id,
            "applicant_name": self.applicant.name if self.applicant else None,
            "applicant_email": self.applicant.email if self.applicant else None,
            "crew_id": self.crew_id,
            "proposed_name": self.proposed_name,
            "description": self.description,
            "activity_type": self.activity_type,
            "visibility": self.visibility,
            "meeting_point_name": self.meeting_point_name,
            "meeting_latitude": self.meeting_latitude,
            "meeting_longitude": self.meeting_longitude,
            "locality": self.locality,
            "status": self.status,
            "admin_note": self.admin_note,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "created_at": self.created_at.isoformat(),
        }
        if include_sensitive:
            data["id_number"] = self.id_number
            data["has_selfie"] = bool(self.selfie_filename)
        return data
