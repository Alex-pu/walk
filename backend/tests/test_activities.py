from datetime import datetime, timezone

from app import create_app
from app.extensions import db
from app.models import Crew, Session, SessionAttendance, User


class TestConfig:
    SECRET_KEY = "test"
    JWT_SECRET_KEY = "test-jwt"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FRONTEND_ORIGIN = "http://localhost:5173"


def _register(client):
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Test User",
            "email": "runner@example.com",
            "password": "password123",
            "neighborhood": "Ruiru",
        },
    )
    return response.get_json()["access_token"]


def test_create_activity_and_stats():
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        db.create_all()

    token = _register(client)
    now = datetime.now(timezone.utc).isoformat()
    response = client.post(
        "/api/activities",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_type": "walk",
            "started_at": now,
            "finished_at": now,
            "duration_seconds": 1800,
            "distance_meters": 2500,
            "route_points": [
                {"latitude": -1.1452, "longitude": 36.9561, "accuracy": 8, "timestamp": now}
            ],
        },
    )

    assert response.status_code == 201

    stats = client.get("/api/activities/me/stats", headers={"Authorization": f"Bearer {token}"})
    assert stats.status_code == 200
    body = stats.get_json()
    assert body["week"]["distance_meters"] == 2500
    assert body["best"]["longest_distance_meters"] == 2500
    assert body["best"]["fastest_pace_seconds_per_km"] == 720
    assert len(body["recent"]) == 1


def test_create_session_activity_marks_attendance_completed():
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        db.create_all()

    token = _register(client)

    with app.app_context():
        user = User.query.filter_by(email="runner@example.com").first()
        crew = Crew(
            name="Test Crew",
            activity_type="walk",
            visibility="public",
            meeting_point_name="Park Gate",
            meeting_latitude=-1.1452,
            meeting_longitude=36.9561,
            created_by=user.id,
        )
        db.session.add(crew)
        db.session.flush()
        session = Session(
            crew_id=crew.id,
            title="Morning Loop",
            activity_type="walk",
            scheduled_start=datetime.now(timezone.utc),
            meeting_point_name=crew.meeting_point_name,
            meeting_latitude=crew.meeting_latitude,
            meeting_longitude=crew.meeting_longitude,
            created_by=user.id,
        )
        db.session.add(session)
        db.session.commit()
        session_id = session.id

    now = datetime.now(timezone.utc).isoformat()
    response = client.post(
        "/api/activities",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "session_id": session_id,
            "activity_type": "walk",
            "started_at": now,
            "finished_at": now,
            "duration_seconds": 900,
            "distance_meters": 1200,
        },
    )

    assert response.status_code == 201

    with app.app_context():
        attendance = SessionAttendance.query.filter_by(session_id=session_id).first()
        assert attendance.status == "completed"
        assert attendance.checked_out_at is not None


def test_user_can_delete_only_own_activity():
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        db.create_all()

    owner_token = _register(client)
    other_response = client.post(
        "/api/auth/register",
        json={
            "name": "Other User",
            "email": "other@example.com",
            "password": "password123",
            "neighborhood": "Ruiru",
        },
    )
    other_token = other_response.get_json()["access_token"]

    now = datetime.now(timezone.utc).isoformat()
    created = client.post(
        "/api/activities",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "activity_type": "walk",
            "started_at": now,
            "finished_at": now,
            "duration_seconds": 600,
            "distance_meters": 1000,
        },
    )
    activity_id = created.get_json()["activity"]["id"]

    blocked = client.delete(f"/api/activities/{activity_id}", headers={"Authorization": f"Bearer {other_token}"})
    assert blocked.status_code == 404

    deleted = client.delete(f"/api/activities/{activity_id}", headers={"Authorization": f"Bearer {owner_token}"})
    assert deleted.status_code == 200

    missing = client.get(f"/api/activities/{activity_id}", headers={"Authorization": f"Bearer {owner_token}"})
    assert missing.status_code == 404


def test_get_activity_returns_route_points_for_owner():
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        db.create_all()

    token = _register(client)
    now = datetime.now(timezone.utc).isoformat()
    created = client.post(
        "/api/activities",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_type": "walk",
            "started_at": now,
            "finished_at": now,
            "duration_seconds": 600,
            "distance_meters": 1000,
            "route_points": [
                {"latitude": -1.1452, "longitude": 36.9561, "accuracy": 8, "timestamp": now},
                {"latitude": -1.1462, "longitude": 36.9571, "accuracy": 9, "timestamp": now},
            ],
        },
    )
    activity_id = created.get_json()["activity"]["id"]

    response = client.get(f"/api/activities/{activity_id}", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert len(response.get_json()["activity"]["route_points"]) == 2


def test_create_manual_activity_without_route_points():
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        db.create_all()

    token = _register(client)
    started = datetime.now(timezone.utc)
    finished = started
    response = client.post(
        "/api/activities",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_type": "walk",
            "started_at": started.isoformat(),
            "finished_at": finished.isoformat(),
            "duration_seconds": 1800,
            "distance_meters": 2600,
            "source": "manual",
        },
    )

    assert response.status_code == 201
    body = response.get_json()["activity"]
    assert body["source"] == "manual"
    assert body["route_points"] == []


def test_create_activity_rejects_invalid_metrics():
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        db.create_all()

    token = _register(client)
    now = datetime.now(timezone.utc).isoformat()
    response = client.post(
        "/api/activities",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_type": "walk",
            "started_at": now,
            "finished_at": now,
            "duration_seconds": 0,
            "distance_meters": -1,
            "source": "manual",
        },
    )

    assert response.status_code == 400
