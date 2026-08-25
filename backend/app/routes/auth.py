from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required

from app.extensions import db
from app.models import PasswordResetToken, User
from app.services.email import send_password_reset_email, send_welcome_email

auth_bp = Blueprint("auth", __name__)


def _required(data, fields):
    missing = [field for field in fields if not data.get(field)]
    if missing:
        return f"Missing required fields: {', '.join(missing)}"
    return None


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    error = _required(data, ["name", "email", "password", "neighborhood"])
    if error:
        return jsonify({"error": error}), 400

    email = data["email"].strip().lower()
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email is already registered"}), 409

    user = User(
        name=data["name"].strip(),
        email=email,
        neighborhood=data["neighborhood"].strip(),
        latitude=data.get("latitude"),
        longitude=data.get("longitude"),
        phone=data.get("phone"),
    )
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()
    send_welcome_email(user)

    token = create_access_token(identity=str(user.id))
    return jsonify({"access_token": token, "user": user.to_dict()}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    error = _required(data, ["email", "password"])
    if error:
        return jsonify({"error": error}), 400

    user = User.query.filter_by(email=data["email"].strip().lower()).first()
    if not user or not user.check_password(data["password"]):
        return jsonify({"error": "Invalid email or password"}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify({"access_token": token, "user": user.to_dict()})


@auth_bp.post("/forgot-password")
def forgot_password():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    if not email:
        return jsonify({"error": "Email is required"}), 400

    user = User.query.filter_by(email=email).first()
    if user:
        reset = PasswordResetToken.create(user.id, datetime.now(timezone.utc) + timedelta(hours=1))
        db.session.add(reset)
        db.session.commit()
        send_password_reset_email(user, reset.token)

    return jsonify({"message": "If that email is registered, a password reset link has been sent."})


@auth_bp.post("/reset-password")
def reset_password():
    data = request.get_json(silent=True) or {}
    error = _required(data, ["token", "password"])
    if error:
        return jsonify({"error": error}), 400
    if len(data["password"]) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    reset = PasswordResetToken.query.filter_by(token=data["token"]).first()
    if not reset or not reset.is_usable():
        return jsonify({"error": "Reset link is invalid or expired"}), 400

    reset.user.set_password(data["password"])
    reset.used_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify({"message": "Password updated. You can now log in."})


@auth_bp.get("/me")
@jwt_required()
def me():
    user = db.session.get(User, int(get_jwt_identity()))
    return jsonify({"user": user.to_dict(include_private_location=True)})


@auth_bp.patch("/me")
@jwt_required()
def update_me():
    user = db.session.get(User, int(get_jwt_identity()))
    data = request.get_json(silent=True) or {}

    if "name" in data and data["name"]:
        user.name = data["name"].strip()
    if "phone" in data:
        user.phone = data["phone"] or None
    if "neighborhood" in data and data["neighborhood"]:
        user.neighborhood = data["neighborhood"].strip()

    try:
        if "latitude" in data:
            user.latitude = float(data["latitude"]) if data["latitude"] not in (None, "") else None
        if "longitude" in data:
            user.longitude = float(data["longitude"]) if data["longitude"] not in (None, "") else None
    except (TypeError, ValueError):
        return jsonify({"error": "Latitude and longitude must be valid numbers"}), 400

    db.session.commit()
    return jsonify({"user": user.to_dict(include_private_location=True)})
