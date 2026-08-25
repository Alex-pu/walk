from flask_jwt_extended import get_jwt_identity

from app.extensions import db
from app.models import CrewMember, User


def current_user():
    return db.session.get(User, int(get_jwt_identity()))


def current_user_id():
    return int(get_jwt_identity())


def is_platform_admin(user=None):
    user = user or current_user()
    return bool(user and user.platform_role == "admin")


def crew_membership(crew_id, user_id=None):
    return CrewMember.query.filter_by(
        crew_id=crew_id,
        user_id=user_id or current_user_id(),
        status="active",
    ).first()


def can_manage_crew(crew_id, user=None):
    if is_platform_admin(user):
        return True
    member = crew_membership(crew_id, user.id if user else None)
    return bool(member and member.role == "organizer")
