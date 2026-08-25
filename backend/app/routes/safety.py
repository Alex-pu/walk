from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models import CrewMember, User, UserBlock, UserReport
from app.services.permissions import current_user, is_platform_admin

safety_bp = Blueprint("safety", __name__)

VALID_REPORT_REASONS = {"harassment", "unsafe_behavior", "spam", "fake_profile", "other"}


def _current_user_id():
    return int(get_jwt_identity())


@safety_bp.post("/reports")
@jwt_required()
def create_report():
    data = request.get_json(silent=True) or {}
    reported_user_id = data.get("reported_user_id")
    reason = data.get("reason")
    if not reported_user_id or not reason:
        return jsonify({"error": "reported_user_id and reason are required"}), 400
    if reason not in VALID_REPORT_REASONS:
        return jsonify({"error": "Invalid report reason"}), 400

    reporter_user_id = _current_user_id()
    if int(reported_user_id) == reporter_user_id:
        return jsonify({"error": "You cannot report yourself"}), 400
    if not db.session.get(User, int(reported_user_id)):
        return jsonify({"error": "Reported user not found"}), 404

    report = UserReport(
        reporter_user_id=reporter_user_id,
        reported_user_id=int(reported_user_id),
        crew_id=data.get("crew_id"),
        session_id=data.get("session_id"),
        reason=reason,
        details=data.get("details"),
    )
    db.session.add(report)
    db.session.commit()
    return jsonify({"report": report.to_dict()}), 201


@safety_bp.post("/blocks")
@jwt_required()
def block_user():
    data = request.get_json(silent=True) or {}
    blocked_user_id = data.get("blocked_user_id")
    if not blocked_user_id:
        return jsonify({"error": "blocked_user_id is required"}), 400

    blocker_user_id = _current_user_id()
    if int(blocked_user_id) == blocker_user_id:
        return jsonify({"error": "You cannot block yourself"}), 400
    if not db.session.get(User, int(blocked_user_id)):
        return jsonify({"error": "Blocked user not found"}), 404

    block = UserBlock.query.filter_by(blocker_user_id=blocker_user_id, blocked_user_id=int(blocked_user_id)).first()
    if not block:
        block = UserBlock(blocker_user_id=blocker_user_id, blocked_user_id=int(blocked_user_id))
        db.session.add(block)
        db.session.commit()
    return jsonify({"block": block.to_dict()}), 201


@safety_bp.get("/blocks")
@jwt_required()
def list_blocks():
    blocks = UserBlock.query.filter_by(blocker_user_id=_current_user_id()).order_by(UserBlock.created_at.desc()).all()
    return jsonify({"blocks": [block.to_dict() for block in blocks]})


@safety_bp.get("/reports")
@jwt_required()
def list_reports():
    user = current_user()
    if is_platform_admin(user):
        reports = UserReport.query.order_by(UserReport.created_at.desc()).all()
        return jsonify({"reports": [report.to_dict() for report in reports]})

    organizer_crew_ids = [
        row.crew_id
        for row in CrewMember.query.filter_by(user_id=user.id, role="organizer", status="active").all()
    ]
    if not organizer_crew_ids:
        return jsonify({"error": "Only organizers or admins can view reports"}), 403

    reports = (
        UserReport.query.filter(UserReport.crew_id.in_(organizer_crew_ids))
        .order_by(UserReport.created_at.desc())
        .all()
    )
    return jsonify({"reports": [report.to_dict() for report in reports]})
