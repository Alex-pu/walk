from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import func

from app.extensions import db
from app.models import Activity, ActivityRoutePoint, Session, SessionAttendance

activities_bp = Blueprint("activities", __name__)

VALID_ACTIVITY_TYPES = {"walk", "run", "mixed"}
VALID_SOURCES = {"web_gps", "manual"}
MAX_ROUTE_POINTS = 10000


def _parse_datetime(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


@activities_bp.get("/me")
@jwt_required()
def my_activities():
    user_id = int(get_jwt_identity())
    activities = Activity.query.filter_by(user_id=user_id).order_by(Activity.started_at.desc()).all()
    return jsonify({"activities": [activity.to_dict() for activity in activities]})


@activities_bp.get("/me/stats")
@jwt_required()
def my_activity_stats():
    user_id = int(get_jwt_identity())
    now = datetime.now(timezone.utc)
    week_start = now - timedelta(days=7)
    month_start = now - timedelta(days=30)

    def totals_since(start):
        distance, duration, count = (
            db.session.query(
                func.coalesce(func.sum(Activity.distance_meters), 0),
                func.coalesce(func.sum(Activity.duration_seconds), 0),
                func.count(Activity.id),
            )
            .filter(Activity.user_id == user_id, Activity.started_at >= start)
            .one()
        )
        attended_sessions = (
            SessionAttendance.query.filter(
                SessionAttendance.user_id == user_id,
                SessionAttendance.status == "completed",
                SessionAttendance.checked_out_at >= start,
            ).count()
        )
        return {
            "distance_meters": float(distance or 0),
            "duration_seconds": int(duration or 0),
            "activity_count": int(count or 0),
            "sessions_attended": int(attended_sessions or 0),
        }

    longest = (
        Activity.query.filter_by(user_id=user_id)
        .order_by(Activity.distance_meters.desc())
        .first()
    )
    pace_activity = (
        Activity.query.filter(Activity.user_id == user_id, Activity.distance_meters > 0)
        .order_by((Activity.duration_seconds / (Activity.distance_meters / 1000)).asc())
        .first()
    )
    recent = (
        Activity.query.filter_by(user_id=user_id)
        .order_by(Activity.started_at.desc())
        .limit(5)
        .all()
    )

    return jsonify(
        {
            "week": totals_since(week_start),
            "month": totals_since(month_start),
            "best": {
                "longest_distance_meters": float(longest.distance_meters) if longest else 0,
                "fastest_pace_seconds_per_km": round(
                    pace_activity.duration_seconds / (pace_activity.distance_meters / 1000)
                )
                if pace_activity else None,
            },
            "recent": [activity.to_dict() for activity in recent],
        }
    )


@activities_bp.get("/<int:activity_id>")
@jwt_required()
def get_activity(activity_id):
    user_id = int(get_jwt_identity())
    activity = Activity.query.filter_by(id=activity_id, user_id=user_id).first()
    if not activity:
        return jsonify({"error": "Activity not found"}), 404
    return jsonify({"activity": activity.to_dict(include_route=True)})


@activities_bp.delete("/<int:activity_id>")
@jwt_required()
def delete_activity(activity_id):
    user_id = int(get_jwt_identity())
    activity = Activity.query.filter_by(id=activity_id, user_id=user_id).first()
    if not activity:
        return jsonify({"error": "Activity not found"}), 404

    db.session.delete(activity)
    db.session.commit()
    return jsonify({"status": "deleted"})


@activities_bp.post("")
@jwt_required()
def create_activity():
    data = request.get_json(silent=True) or {}
    required = ["activity_type", "started_at", "finished_at", "duration_seconds", "distance_meters"]
    missing = [field for field in required if data.get(field) in (None, "")]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    user_id = int(get_jwt_identity())
    activity_type = data["activity_type"]
    source = data.get("source", "web_gps")
    if activity_type not in VALID_ACTIVITY_TYPES:
        return jsonify({"error": "Invalid activity_type"}), 400
    if source not in VALID_SOURCES:
        return jsonify({"error": "Invalid activity source"}), 400

    try:
        started_at = _parse_datetime(data["started_at"])
        finished_at = _parse_datetime(data["finished_at"])
        duration_seconds = int(data["duration_seconds"])
        distance_meters = float(data["distance_meters"])
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid activity metrics or timestamps"}), 400

    if duration_seconds <= 0:
        return jsonify({"error": "duration_seconds must be greater than zero"}), 400
    if distance_meters < 0:
        return jsonify({"error": "distance_meters cannot be negative"}), 400
    if finished_at < started_at:
        return jsonify({"error": "finished_at cannot be before started_at"}), 400

    session_id = data.get("session_id")
    if session_id and not db.session.get(Session, int(session_id)):
        return jsonify({"error": "Session not found"}), 404

    route_points = data.get("route_points") or []
    if len(route_points) > MAX_ROUTE_POINTS:
        return jsonify({"error": "Too many route points"}), 400

    activity = Activity(
        user_id=user_id,
        session_id=session_id,
        activity_type=activity_type,
        started_at=started_at,
        finished_at=finished_at,
        duration_seconds=duration_seconds,
        distance_meters=distance_meters,
        source=source,
        start_latitude=route_points[0]["latitude"] if route_points else None,
        start_longitude=route_points[0]["longitude"] if route_points else None,
        end_latitude=route_points[-1]["latitude"] if route_points else None,
        end_longitude=route_points[-1]["longitude"] if route_points else None,
    )
    db.session.add(activity)
    db.session.flush()

    for index, point in enumerate(route_points):
        db.session.add(
            ActivityRoutePoint(
                activity_id=activity.id,
                latitude=float(point["latitude"]),
                longitude=float(point["longitude"]),
                accuracy=point.get("accuracy"),
                recorded_at=_parse_datetime(point["timestamp"]) if isinstance(point.get("timestamp"), str) else datetime.fromtimestamp(point["timestamp"] / 1000, timezone.utc),
                sequence_number=index,
            )
        )

    if session_id:
        attendance = SessionAttendance.query.filter_by(session_id=session_id, user_id=user_id).first()
        if not attendance:
            attendance = SessionAttendance(session_id=session_id, user_id=user_id)
            db.session.add(attendance)
        attendance.status = "completed"
        if not attendance.checked_in_at:
            attendance.checked_in_at = activity.started_at
        attendance.checked_out_at = activity.finished_at

    db.session.commit()
    return jsonify({"activity": activity.to_dict(include_route=True)}), 201
