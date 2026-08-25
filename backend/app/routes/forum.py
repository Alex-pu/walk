from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models import Crew, ForumReply, ForumThread
from app.services.permissions import can_manage_crew, crew_membership, current_user, is_platform_admin

forum_bp = Blueprint("forum", __name__)

VALID_CATEGORIES = {"issue", "question", "announcement", "general"}
VALID_STATUSES = {"open", "resolved", "closed"}


def _require_text(data, field, max_length=None):
    value = (data.get(field) or "").strip()
    if not value:
        return None, f"{field} is required"
    if max_length and len(value) > max_length:
        return None, f"{field} must be {max_length} characters or fewer"
    return value, None


def _reply_tree(replies):
    nodes = []
    lookup = {}
    for reply in sorted(replies, key=lambda item: item.created_at):
        item = reply.to_dict()
        item["children"] = []
        lookup[reply.id] = item
        nodes.append(item)

    roots = []
    for item in nodes:
        parent = lookup.get(item["parent_reply_id"])
        if parent:
            parent["children"].append(item)
        else:
            roots.append(item)
    return roots


def _can_view_thread(thread, user):
    if thread.scope_type == "platform":
        return True
    if is_platform_admin(user):
        return True
    return bool(crew_membership(thread.crew_id, user.id))


def _can_moderate_thread(thread, user):
    if thread.scope_type == "platform":
        return is_platform_admin(user)
    return can_manage_crew(thread.crew_id, user)


def _thread_or_404(thread_id):
    thread = db.session.get(ForumThread, thread_id)
    if not thread:
        return None, (jsonify({"error": "Thread not found"}), 404)
    return thread, None


def _create_thread(scope_type, crew_id=None):
    data = request.get_json(silent=True) or {}
    title, error = _require_text(data, "title", 180)
    if error:
        return jsonify({"error": error}), 400
    body, error = _require_text(data, "body")
    if error:
        return jsonify({"error": error}), 400

    category = data.get("category", "general")
    if category not in VALID_CATEGORIES:
        return jsonify({"error": "Invalid category"}), 400

    user = current_user()
    thread = ForumThread(
        scope_type=scope_type,
        crew_id=crew_id,
        author_id=user.id,
        title=title,
        body=body,
        category=category,
    )
    db.session.add(thread)
    db.session.commit()
    return jsonify({"thread": thread.to_dict()}), 201


@forum_bp.get("/threads")
@jwt_required()
def platform_threads():
    threads = (
        ForumThread.query.filter_by(scope_type="platform")
        .order_by(ForumThread.pinned.desc(), ForumThread.updated_at.desc())
        .all()
    )
    return jsonify({"threads": [thread.to_dict(include_body=False) for thread in threads]})


@forum_bp.post("/threads")
@jwt_required()
def create_platform_thread():
    return _create_thread("platform")


@forum_bp.get("/threads/<int:thread_id>")
@jwt_required()
def thread_detail(thread_id):
    user = current_user()
    thread, error = _thread_or_404(thread_id)
    if error:
        return error
    if not _can_view_thread(thread, user):
        return jsonify({"error": "You do not have access to this discussion"}), 403

    data = thread.to_dict()
    data["can_moderate"] = _can_moderate_thread(thread, user)
    data["replies"] = _reply_tree(thread.replies)
    return jsonify({"thread": data})


@forum_bp.post("/threads/<int:thread_id>/replies")
@jwt_required()
def create_reply(thread_id):
    user = current_user()
    thread, error = _thread_or_404(thread_id)
    if error:
        return error
    if not _can_view_thread(thread, user):
        return jsonify({"error": "You do not have access to this discussion"}), 403
    if thread.status == "closed":
        return jsonify({"error": "This discussion is closed"}), 400

    data = request.get_json(silent=True) or {}
    body, error = _require_text(data, "body")
    if error:
        return jsonify({"error": error}), 400

    parent_reply_id = data.get("parent_reply_id")
    if parent_reply_id:
        parent = db.session.get(ForumReply, int(parent_reply_id))
        if not parent or parent.thread_id != thread.id:
            return jsonify({"error": "Parent reply not found for this thread"}), 404

    reply = ForumReply(
        thread_id=thread.id,
        author_id=user.id,
        parent_reply_id=parent_reply_id,
        body=body,
    )
    db.session.add(reply)
    db.session.commit()
    return jsonify({"reply": reply.to_dict()}), 201


@forum_bp.patch("/threads/<int:thread_id>")
@jwt_required()
def update_thread(thread_id):
    user = current_user()
    thread, error = _thread_or_404(thread_id)
    if error:
        return error
    if not _can_moderate_thread(thread, user):
        return jsonify({"error": "Organizer or admin access required"}), 403

    data = request.get_json(silent=True) or {}
    if "status" in data:
        if data["status"] not in VALID_STATUSES:
            return jsonify({"error": "Invalid status"}), 400
        thread.status = data["status"]
    if "pinned" in data:
        thread.pinned = bool(data["pinned"])
    db.session.commit()
    return jsonify({"thread": thread.to_dict()})


@forum_bp.get("/crews/<int:crew_id>/threads")
@jwt_required()
def crew_threads(crew_id):
    user = current_user()
    crew = db.session.get(Crew, crew_id)
    if not crew:
        return jsonify({"error": "Crew not found"}), 404
    if not is_platform_admin(user) and not crew_membership(crew_id, user.id):
        return jsonify({"error": "Only crew members can view this forum"}), 403

    threads = (
        ForumThread.query.filter_by(scope_type="crew", crew_id=crew_id)
        .order_by(ForumThread.pinned.desc(), ForumThread.updated_at.desc())
        .all()
    )
    return jsonify({"threads": [thread.to_dict(include_body=False) for thread in threads]})


@forum_bp.post("/crews/<int:crew_id>/threads")
@jwt_required()
def create_crew_thread(crew_id):
    user = current_user()
    crew = db.session.get(Crew, crew_id)
    if not crew:
        return jsonify({"error": "Crew not found"}), 404
    if not is_platform_admin(user) and not crew_membership(crew_id, user.id):
        return jsonify({"error": "Only crew members can post in this forum"}), 403
    return _create_thread("crew", crew_id)
