from datetime import datetime, timezone

from flask import Blueprint, jsonify, request, send_from_directory
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models import Crew, CrewApplication, CrewMember, User, UserReport
from app.services.permissions import is_platform_admin
from app.services.uploads import upload_folder
from app.services.email import send_email

admin_bp = Blueprint("admin", __name__)


def _require_admin():
    if not is_platform_admin():
        return jsonify({"error": "Platform admin access required"}), 403
    return None


@admin_bp.get("/overview")
@jwt_required()
def overview():
    error = _require_admin()
    if error:
        return error

    users = User.query.order_by(User.created_at.desc()).all()
    crews = Crew.query.order_by(Crew.created_at.desc()).all()
    reports = UserReport.query.order_by(UserReport.created_at.desc()).limit(50).all()
    applications = CrewApplication.query.order_by(CrewApplication.created_at.desc()).limit(100).all()
    return jsonify(
        {
            "users": [user.to_dict(include_private_location=True) for user in users],
            "crews": [crew.to_dict() for crew in crews],
            "reports": [report.to_dict() for report in reports],
            "crew_applications": [application.to_dict(include_sensitive=True) for application in applications],
        }
    )


@admin_bp.patch("/users/<int:user_id>/role")
@jwt_required()
def update_platform_role(user_id):
    error = _require_admin()
    if error:
        return error

    data = request.get_json(silent=True) or {}
    role = data.get("platform_role")
    if role not in {"admin", "member"}:
        return jsonify({"error": "platform_role must be admin or member"}), 400

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    user.platform_role = role
    db.session.commit()
    return jsonify({"user": user.to_dict(include_private_location=True)})


@admin_bp.get("/memberships")
@jwt_required()
def memberships():
    error = _require_admin()
    if error:
        return error

    rows = CrewMember.query.order_by(CrewMember.joined_at.desc()).all()
    return jsonify({"memberships": [row.to_dict() for row in rows]})


@admin_bp.post("/broadcasts")
@jwt_required()
def send_broadcast():
    error = _require_admin()
    if error:
        return error

    data = request.get_json(silent=True) or {}
    subject = data.get("subject", "").strip()
    body = data.get("body", "").strip()
    if not subject or not body:
        return jsonify({"error": "Subject and body are required"}), 400

    users = User.query.order_by(User.created_at.asc()).all()
    sent = 0
    failed = 0
    for user in users:
        if send_email(user.email, subject, body):
            sent += 1
        else:
            failed += 1

    return jsonify({"message": "Broadcast processed", "sent": sent, "failed": failed, "recipient_count": len(users)})


@admin_bp.get("/crew-applications/<int:application_id>/selfie")
@jwt_required()
def crew_application_selfie(application_id):
    error = _require_admin()
    if error:
        return error

    application = db.session.get(CrewApplication, application_id)
    if not application or not application.selfie_filename:
        return jsonify({"error": "Crew application selfie not found"}), 404

    return send_from_directory(
        upload_folder(),
        application.selfie_filename,
        as_attachment=False,
    )


@admin_bp.patch("/crew-applications/<int:application_id>")
@jwt_required()
def review_crew_application(application_id):
    error = _require_admin()
    if error:
        return error

    data = request.get_json(silent=True) or {}
    status = data.get("status")
    if status not in {"approved", "denied"}:
        return jsonify({"error": "status must be approved or denied"}), 400

    application = db.session.get(CrewApplication, application_id)
    if not application:
        return jsonify({"error": "Crew application not found"}), 404
    if application.status != "pending":
        return jsonify({"error": "Crew application has already been reviewed"}), 409

    application.status = status
    application.admin_note = data.get("admin_note")
    application.reviewed_by = int(get_jwt_identity())
    application.reviewed_at = datetime.now(timezone.utc)

    crew = None
    if status == "approved":
        crew = Crew(
            name=application.proposed_name,
            description=application.description,
            activity_type=application.activity_type,
            visibility=application.visibility,
            meeting_point_name=application.meeting_point_name,
            meeting_latitude=application.meeting_latitude,
            meeting_longitude=application.meeting_longitude,
            created_by=application.applicant_user_id,
        )
        db.session.add(crew)
        db.session.flush()
        db.session.add(
            CrewMember(
                crew_id=crew.id,
                user_id=application.applicant_user_id,
                role="organizer",
                status="active",
            )
        )
        application.crew_id = crew.id

    db.session.commit()
    return jsonify(
        {
            "application": application.to_dict(include_sensitive=True),
            "crew": crew.to_dict(include_members=True) if crew else None,
        }
    )
