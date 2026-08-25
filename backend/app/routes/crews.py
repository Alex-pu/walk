import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import func
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import Activity, Crew, CrewApplication, CrewMember, Session, SessionAttendance, UserReport
from app.services.permissions import current_user, can_manage_crew, is_platform_admin
from app.services.geo import distance_meters
from app.services.uploads import upload_folder
from app.routes.sessions import create_session_for_crew

crews_bp = Blueprint("crews", __name__)

VALID_ACTIVITY_TYPES = {"walk", "run", "mixed"}
VALID_VISIBILITY = {"public", "private"}
ALLOWED_SELFIE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}


def _current_user_id():
    return int(get_jwt_identity())


def _require_fields(data, fields):
    missing = [field for field in fields if data.get(field) in (None, "")]
    if missing:
        return f"Missing required fields: {', '.join(missing)}"
    return None


def _allowed_selfie(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_SELFIE_EXTENSIONS


def _save_selfie(file_storage):
    if not file_storage or not file_storage.filename:
        return None, "Selfie photo is required"
    if not _allowed_selfie(file_storage.filename):
        return None, "Selfie must be a JPG, PNG, or WEBP image"

    folder = upload_folder()
    os.makedirs(folder, exist_ok=True)
    extension = secure_filename(file_storage.filename).rsplit(".", 1)[1].lower()
    filename = f"{uuid4().hex}.{extension}"
    file_storage.save(os.path.join(folder, filename))
    return filename, None


@crews_bp.get("")
@jwt_required()
def list_crews():
    user = current_user()
    memberships = {
        member.crew_id: member.role
        for member in CrewMember.query.filter_by(user_id=user.id, status="active").all()
    }
    crews = Crew.query.order_by(Crew.created_at.desc()).all()
    results = []
    for crew in crews:
        item = crew.to_dict()
        role = memberships.get(crew.id)
        item["current_user_role"] = role
        item["can_create_sessions"] = is_platform_admin(user) or role == "organizer"
        item["can_manage_members"] = is_platform_admin(user)
        results.append(item)
    return jsonify({"crews": results})


@crews_bp.get("/nearby")
@jwt_required()
def nearby_crews():
    lat = request.args.get("latitude", type=float)
    lng = request.args.get("longitude", type=float)
    radius_km = request.args.get("radius_km", default=10, type=float)
    crews = Crew.query.filter_by(visibility="public").all()

    results = []
    for crew in crews:
        item = crew.to_dict()
        if lat is not None and lng is not None:
            distance = distance_meters(lat, lng, crew.meeting_latitude, crew.meeting_longitude)
            if distance > radius_km * 1000:
                continue
            item["distance_meters"] = round(distance)
        results.append(item)

    results.sort(key=lambda item: item.get("distance_meters", 0))
    return jsonify({"crews": results})


@crews_bp.post("")
@jwt_required()
def create_crew():
    if not is_platform_admin():
        return jsonify({"error": "Submit a crew application for admin approval before creating a crew"}), 403

    data = request.get_json(silent=True) or {}
    error = _require_fields(data, ["name", "activity_type", "meeting_point_name", "meeting_latitude", "meeting_longitude"])
    if error:
        return jsonify({"error": error}), 400
    if data["activity_type"] not in VALID_ACTIVITY_TYPES:
        return jsonify({"error": "Invalid activity_type"}), 400

    user_id = _current_user_id()
    crew = Crew(
        name=data["name"].strip(),
        description=data.get("description"),
        activity_type=data["activity_type"],
        visibility=data.get("visibility", "public"),
        meeting_point_name=data["meeting_point_name"].strip(),
        meeting_latitude=float(data["meeting_latitude"]),
        meeting_longitude=float(data["meeting_longitude"]),
        created_by=user_id,
    )
    if crew.visibility not in VALID_VISIBILITY:
        return jsonify({"error": "Invalid visibility"}), 400

    db.session.add(crew)
    db.session.flush()
    db.session.add(CrewMember(crew_id=crew.id, user_id=user_id, role="organizer"))
    db.session.commit()
    return jsonify({"crew": crew.to_dict(include_members=True)}), 201


@crews_bp.get("/applications/me")
@jwt_required()
def my_crew_applications():
    user_id = _current_user_id()
    applications = (
        CrewApplication.query.filter_by(applicant_user_id=user_id)
        .order_by(CrewApplication.created_at.desc())
        .all()
    )
    return jsonify({"applications": [application.to_dict() for application in applications]})


@crews_bp.post("/applications")
@jwt_required()
def submit_crew_application():
    data = request.form
    error = _require_fields(
        data,
        [
            "proposed_name",
            "activity_type",
            "meeting_point_name",
            "meeting_latitude",
            "meeting_longitude",
            "locality",
            "id_number",
        ],
    )
    if error:
        return jsonify({"error": error}), 400
    if data["activity_type"] not in VALID_ACTIVITY_TYPES:
        return jsonify({"error": "Invalid activity_type"}), 400
    visibility = data.get("visibility", "public")
    if visibility not in VALID_VISIBILITY:
        return jsonify({"error": "Invalid visibility"}), 400

    user_id = _current_user_id()
    existing_pending = CrewApplication.query.filter_by(applicant_user_id=user_id, status="pending").first()
    if existing_pending:
        return jsonify({"error": "You already have a pending crew application"}), 409

    try:
        meeting_latitude = float(data["meeting_latitude"])
        meeting_longitude = float(data["meeting_longitude"])
    except ValueError:
        return jsonify({"error": "Meeting latitude and longitude must be numbers"}), 400

    selfie_filename, selfie_error = _save_selfie(request.files.get("selfie"))
    if selfie_error:
        return jsonify({"error": selfie_error}), 400

    application = CrewApplication(
        applicant_user_id=user_id,
        proposed_name=data["proposed_name"].strip(),
        description=data.get("description"),
        activity_type=data["activity_type"],
        visibility=visibility,
        meeting_point_name=data["meeting_point_name"].strip(),
        meeting_latitude=meeting_latitude,
        meeting_longitude=meeting_longitude,
        locality=data["locality"].strip(),
        id_number=data["id_number"].strip(),
        selfie_filename=selfie_filename,
    )
    db.session.add(application)
    db.session.commit()
    return jsonify({"application": application.to_dict()}), 201


@crews_bp.get("/<int:crew_id>")
@jwt_required()
def get_crew(crew_id):
    crew = db.session.get(Crew, crew_id)
    if not crew:
        return jsonify({"error": "Crew not found"}), 404
    data = crew.to_dict(include_members=True)
    user = current_user()
    member = CrewMember.query.filter_by(crew_id=crew_id, user_id=user.id, status="active").first()
    data["current_user_role"] = member.role if member else None
    data["can_create_sessions"] = can_manage_crew(crew_id, user)
    data["can_manage_members"] = is_platform_admin(user)
    upcoming = (
        Session.query.filter_by(crew_id=crew_id, status="scheduled")
        .order_by(Session.scheduled_start.asc())
        .limit(5)
        .all()
    )
    data["sessions"] = [session.to_dict() for session in upcoming]
    return jsonify({"crew": data})


@crews_bp.get("/<int:crew_id>/reports")
@jwt_required()
def crew_reports(crew_id):
    crew = db.session.get(Crew, crew_id)
    if not crew:
        return jsonify({"error": "Crew not found"}), 404
    if not can_manage_crew(crew_id):
        return jsonify({"error": "Only organizers or admins can view crew reports"}), 403

    reports = UserReport.query.filter_by(crew_id=crew_id).order_by(UserReport.created_at.desc()).all()
    return jsonify({"reports": [report.to_dict() for report in reports]})


@crews_bp.patch("/<int:crew_id>/members/<int:user_id>/role")
@jwt_required()
def update_member_role(crew_id, user_id):
    if not is_platform_admin():
        return jsonify({"error": "Only platform admins can promote or demote crew members"}), 403
    data = request.get_json(silent=True) or {}
    role = data.get("role")
    if role not in {"member", "organizer"}:
        return jsonify({"error": "Role must be member or organizer"}), 400

    member = CrewMember.query.filter_by(crew_id=crew_id, user_id=user_id).first()
    if not member:
        return jsonify({"error": "Crew member not found"}), 404
    member.role = role
    member.status = "active"
    db.session.commit()
    return jsonify({"member": member.to_dict()})


@crews_bp.get("/<int:crew_id>/stats")
@jwt_required()
def crew_stats(crew_id):
    crew = db.session.get(Crew, crew_id)
    if not crew:
        return jsonify({"error": "Crew not found"}), 404

    month_start = datetime.now(timezone.utc) - timedelta(days=30)
    distance, duration, activities = (
        db.session.query(
            func.coalesce(func.sum(Activity.distance_meters), 0),
            func.coalesce(func.sum(Activity.duration_seconds), 0),
            func.count(Activity.id),
        )
        .join(Session, Activity.session_id == Session.id)
        .filter(Session.crew_id == crew_id, Activity.started_at >= month_start)
        .one()
    )
    completed_sessions = (
        db.session.query(func.count(func.distinct(SessionAttendance.session_id)))
        .join(Session, SessionAttendance.session_id == Session.id)
        .filter(Session.crew_id == crew_id, SessionAttendance.status == "completed")
        .scalar()
    )
    active_members = (
        db.session.query(func.count(func.distinct(Activity.user_id)))
        .join(Session, Activity.session_id == Session.id)
        .filter(Session.crew_id == crew_id, Activity.started_at >= month_start)
        .scalar()
    )
    participation = (
        db.session.query(SessionAttendance.user_id, func.count(SessionAttendance.id).label("sessions_completed"))
        .join(Session, SessionAttendance.session_id == Session.id)
        .filter(Session.crew_id == crew_id, SessionAttendance.status == "completed")
        .group_by(SessionAttendance.user_id)
        .order_by(func.count(SessionAttendance.id).desc())
        .limit(5)
        .all()
    )

    return jsonify(
        {
            "month": {
                "distance_meters": float(distance or 0),
                "duration_seconds": int(duration or 0),
                "activity_count": int(activities or 0),
                "completed_sessions": int(completed_sessions or 0),
                "active_members": int(active_members or 0),
                "participation": [
                    {"user_id": user_id, "sessions_completed": sessions_completed}
                    for user_id, sessions_completed in participation
                ],
            }
        }
    )


@crews_bp.post("/<int:crew_id>/join")
@jwt_required()
def join_crew(crew_id):
    crew = db.session.get(Crew, crew_id)
    if not crew:
        return jsonify({"error": "Crew not found"}), 404

    user_id = _current_user_id()
    member = CrewMember.query.filter_by(crew_id=crew_id, user_id=user_id).first()
    if member:
        member.status = "active"
    else:
        db.session.add(CrewMember(crew_id=crew_id, user_id=user_id))
    db.session.commit()
    return jsonify({"crew": crew.to_dict(include_members=True)})


@crews_bp.post("/<int:crew_id>/leave")
@jwt_required()
def leave_crew(crew_id):
    user_id = _current_user_id()
    member = CrewMember.query.filter_by(crew_id=crew_id, user_id=user_id).first()
    if not member:
        return jsonify({"error": "You are not a member of this crew"}), 404
    member.status = "left"
    db.session.commit()
    return jsonify({"status": "left"})


@crews_bp.post("/<int:crew_id>/sessions")
@jwt_required()
def create_session(crew_id):
    return create_session_for_crew(crew_id)
