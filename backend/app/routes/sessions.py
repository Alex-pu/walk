from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models import Crew, CrewMember, Session, SessionAttendance, User
from app.services.geo import distance_meters
from app.services.permissions import is_platform_admin

sessions_bp = Blueprint("sessions", __name__)

VALID_ACTIVITY_TYPES = {"walk", "run", "mixed"}
SESSION_ACTIONABLE_STATUSES = {"scheduled", "active"}


def _current_user_id():
    return int(get_jwt_identity())


def _parse_datetime(value):
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def _parse_optional_distance(value):
    if value in (None, ""):
        return None
    distance = int(value)
    if distance < 0:
        raise ValueError("expected_distance_m cannot be negative")
    return distance


def _can_manage_session(session, user_id):
    user = db.session.get(User, user_id)
    if is_platform_admin(user):
        return True
    member = CrewMember.query.filter_by(crew_id=session.crew_id, user_id=user_id, status="active").first()
    return bool(member and member.role in {"organizer", "admin"})


def _serialize_session(session, include_attendees=False):
    user_id = _current_user_id()
    data = session.to_dict(include_attendees=include_attendees)
    attendance = SessionAttendance.query.filter_by(session_id=session.id, user_id=user_id).first()
    data["current_user_attendance"] = attendance.to_dict() if attendance else None
    data["can_manage_session"] = _can_manage_session(session, user_id)
    return data


def _require_manage_session(session):
    if not _can_manage_session(session, _current_user_id()):
        return jsonify({"error": "Only crew organizers can manage this session"}), 403
    return None


@sessions_bp.get("/nearby")
@jwt_required()
def nearby_sessions():
    lat = request.args.get("latitude", type=float)
    lng = request.args.get("longitude", type=float)
    radius_km = request.args.get("radius_km", default=10, type=float)
    sessions = Session.query.filter(Session.status == "scheduled").order_by(Session.scheduled_start.asc()).all()

    results = []
    for session in sessions:
        item = _serialize_session(session)
        if lat is not None and lng is not None:
            distance = distance_meters(lat, lng, session.meeting_latitude, session.meeting_longitude)
            if distance > radius_km * 1000:
                continue
            item["distance_meters"] = round(distance)
        results.append(item)

    return jsonify({"sessions": results})


@sessions_bp.get("/<int:session_id>")
@jwt_required()
def get_session(session_id):
    session = db.session.get(Session, session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
    return jsonify({"session": _serialize_session(session, include_attendees=True)})


@sessions_bp.post("/<int:session_id>/join")
@jwt_required()
def join_session(session_id):
    session = db.session.get(Session, session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
    if session.status not in SESSION_ACTIONABLE_STATUSES:
        return jsonify({"error": "This session is no longer open for joining"}), 400

    user_id = _current_user_id()
    attendance = SessionAttendance.query.filter_by(session_id=session_id, user_id=user_id).first()
    if attendance:
        attendance.status = "going"
    else:
        db.session.add(SessionAttendance(session_id=session_id, user_id=user_id))
    db.session.commit()
    return jsonify({"session": _serialize_session(session, include_attendees=True)})


@sessions_bp.post("/<int:session_id>/check-in")
@jwt_required()
def check_in(session_id):
    attendance = _get_or_create_attendance(session_id)
    if not attendance:
        return jsonify({"error": "Session not found"}), 404
    if attendance.session.status not in SESSION_ACTIONABLE_STATUSES:
        return jsonify({"error": "This session is not open for check-in"}), 400
    attendance.status = "checked_in"
    attendance.checked_in_at = datetime.now(timezone.utc)
    attendance.session.status = "active"
    db.session.commit()
    return jsonify({"session": _serialize_session(attendance.session, include_attendees=True)})


@sessions_bp.post("/<int:session_id>/check-out")
@jwt_required()
def check_out(session_id):
    attendance = _get_or_create_attendance(session_id)
    if not attendance:
        return jsonify({"error": "Session not found"}), 404
    if attendance.status not in {"checked_in", "going"}:
        return jsonify({"error": "Only going or checked-in attendees can check out"}), 400
    attendance.status = "completed"
    attendance.checked_out_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify({"session": _serialize_session(attendance.session, include_attendees=True)})


@sessions_bp.post("/<int:session_id>/cancel")
@jwt_required()
def cancel_session(session_id):
    session = db.session.get(Session, session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
    error = _require_manage_session(session)
    if error:
        return error

    session.status = "cancelled"
    for attendance in session.attendance:
        if attendance.status in {"going", "checked_in"}:
            attendance.status = "cancelled"
    db.session.commit()
    return jsonify({"session": _serialize_session(session, include_attendees=True)})


@sessions_bp.post("/<int:session_id>/complete")
@jwt_required()
def complete_session(session_id):
    session = db.session.get(Session, session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
    error = _require_manage_session(session)
    if error:
        return error

    now = datetime.now(timezone.utc)
    session.status = "completed"
    for attendance in session.attendance:
        if attendance.status == "checked_in":
            attendance.status = "completed"
            attendance.checked_out_at = attendance.checked_out_at or now
        elif attendance.status == "going":
            attendance.status = "no_show"
    db.session.commit()
    return jsonify({"session": _serialize_session(session, include_attendees=True)})


@sessions_bp.post("/<int:session_id>/attendees/<int:user_id>/no-show")
@jwt_required()
def mark_no_show(session_id, user_id):
    session = db.session.get(Session, session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
    error = _require_manage_session(session)
    if error:
        return error

    attendance = SessionAttendance.query.filter_by(session_id=session_id, user_id=user_id).first()
    if not attendance:
        return jsonify({"error": "Attendance not found"}), 404
    attendance.status = "no_show"
    db.session.commit()
    return jsonify({"session": _serialize_session(session, include_attendees=True)})


def create_session_for_crew(crew_id):
    data = request.get_json(silent=True) or {}
    required = ["title", "activity_type", "scheduled_start"]
    missing = [field for field in required if not data.get(field)]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400
    if data["activity_type"] not in VALID_ACTIVITY_TYPES:
        return jsonify({"error": "Invalid activity_type"}), 400

    crew = db.session.get(Crew, crew_id)
    if not crew:
        return jsonify({"error": "Crew not found"}), 404
    if is_platform_admin():
        member = True
    else:
        member = CrewMember.query.filter_by(crew_id=crew_id, user_id=_current_user_id(), status="active").first()
    if not member or (member is not True and member.role not in {"organizer", "admin"}):
        return jsonify({"error": "Only crew organizers can create sessions"}), 403

    try:
        scheduled_start = _parse_datetime(data["scheduled_start"])
        expected_distance_m = _parse_optional_distance(data.get("expected_distance_m"))
        meeting_latitude = float(data.get("meeting_latitude") or crew.meeting_latitude)
        meeting_longitude = float(data.get("meeting_longitude") or crew.meeting_longitude)
    except (TypeError, ValueError) as exc:
        return jsonify({"error": str(exc) or "Invalid session field"}), 400

    if not scheduled_start:
        return jsonify({"error": "Invalid scheduled_start"}), 400

    session = Session(
        crew_id=crew_id,
        title=data["title"].strip(),
        activity_type=data["activity_type"],
        scheduled_start=scheduled_start,
        expected_distance_m=expected_distance_m,
        meeting_point_name=data.get("meeting_point_name") or crew.meeting_point_name,
        meeting_latitude=meeting_latitude,
        meeting_longitude=meeting_longitude,
        difficulty=data.get("difficulty"),
        created_by=_current_user_id(),
    )
    db.session.add(session)
    db.session.commit()
    return jsonify({"session": _serialize_session(session, include_attendees=True)}), 201


def _get_or_create_attendance(session_id):
    session = db.session.get(Session, session_id)
    if not session:
        return None
    user_id = _current_user_id()
    attendance = SessionAttendance.query.filter_by(session_id=session_id, user_id=user_id).first()
    if attendance:
        return attendance
    attendance = SessionAttendance(session_id=session_id, user_id=user_id)
    db.session.add(attendance)
    db.session.flush()
    return attendance
