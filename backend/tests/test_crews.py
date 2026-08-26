from datetime import datetime, timezone

from app import create_app
from app.extensions import db
from app.models import Activity, Crew, CrewMember, Session, User


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
            "name": "Crew Tester",
            "email": "crew@example.com",
            "password": "password123",
            "neighborhood": "Ruiru",
        },
    )
    return response.get_json()["access_token"]


def test_crew_detail_includes_upcoming_sessions_and_stats():
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        db.create_all()

    token = _register(client)

    with app.app_context():
        user = User.query.filter_by(email="crew@example.com").first()
        crew = Crew(
            name="Stats Crew",
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
            title="Stats Walk",
            activity_type="walk",
            scheduled_start=datetime.now(timezone.utc),
            meeting_point_name=crew.meeting_point_name,
            meeting_latitude=crew.meeting_latitude,
            meeting_longitude=crew.meeting_longitude,
            created_by=user.id,
        )
        db.session.add(session)
        db.session.flush()
        db.session.add(
            Activity(
                user_id=user.id,
                session_id=session.id,
                activity_type="walk",
                started_at=datetime.now(timezone.utc),
                finished_at=datetime.now(timezone.utc),
                duration_seconds=1200,
                distance_meters=2100,
                source="web_gps",
            )
        )
        db.session.commit()
        crew_id = crew.id

    detail = client.get(f"/api/crews/{crew_id}", headers={"Authorization": f"Bearer {token}"})
    assert detail.status_code == 200
    assert detail.get_json()["crew"]["sessions"][0]["title"] == "Stats Walk"

    stats = client.get(f"/api/crews/{crew_id}/stats", headers={"Authorization": f"Bearer {token}"})
    assert stats.status_code == 200
    body = stats.get_json()["month"]
    assert body["distance_meters"] == 2100
    assert body["activity_count"] == 1
    assert body["active_members"] == 1


def test_create_session_rejects_negative_distance():
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        db.create_all()

    token = _register(client)

    with app.app_context():
        user = User.query.filter_by(email="crew@example.com").first()
        crew = Crew(
            name="Validation Crew",
            activity_type="walk",
            visibility="public",
            meeting_point_name="Park Gate",
            meeting_latitude=-1.1452,
            meeting_longitude=36.9561,
            created_by=user.id,
        )
        db.session.add(crew)
        db.session.flush()
        db.session.add(CrewMember(crew_id=crew.id, user_id=user.id, role="organizer"))
        db.session.commit()
        crew_id = crew.id

    response = client.post(
        f"/api/crews/{crew_id}/sessions",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Bad Walk",
            "activity_type": "walk",
            "scheduled_start": datetime.now(timezone.utc).isoformat(),
            "expected_distance_m": -100,
        },
    )

    assert response.status_code == 400


def test_only_organizer_can_create_session():
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        db.create_all()

    organizer_token = _register(client)
    member_response = client.post(
        "/api/auth/register",
        json={
            "name": "Member User",
            "email": "member@example.com",
            "password": "password123",
            "neighborhood": "Ruiru",
        },
    )
    member_token = member_response.get_json()["access_token"]

    with app.app_context():
        organizer = User.query.filter_by(email="crew@example.com").first()
        member = User.query.filter_by(email="member@example.com").first()
        crew = Crew(
            name="Organizer Crew",
            activity_type="walk",
            visibility="public",
            meeting_point_name="Park Gate",
            meeting_latitude=-1.1452,
            meeting_longitude=36.9561,
            created_by=organizer.id,
        )
        db.session.add(crew)
        db.session.flush()
        db.session.add(CrewMember(crew_id=crew.id, user_id=organizer.id, role="organizer"))
        db.session.add(CrewMember(crew_id=crew.id, user_id=member.id, role="member"))
        db.session.commit()
        crew_id = crew.id

    payload = {
        "title": "Organizer Only",
        "activity_type": "walk",
        "scheduled_start": datetime.now(timezone.utc).isoformat(),
    }
    blocked = client.post(f"/api/crews/{crew_id}/sessions", headers={"Authorization": f"Bearer {member_token}"}, json=payload)
    assert blocked.status_code == 403

    allowed = client.post(f"/api/crews/{crew_id}/sessions", headers={"Authorization": f"Bearer {organizer_token}"}, json=payload)
    assert allowed.status_code == 201


def test_join_crew_creates_membership_for_invited_user():
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        db.create_all()

    organizer_token = _register(client)
    member_response = client.post(
        "/api/auth/register",
        json={
            "name": "Invited User",
            "email": "invited@example.com",
            "password": "password123",
            "neighborhood": "Ruiru",
        },
    )
    member_token = member_response.get_json()["access_token"]

    with app.app_context():
        organizer = User.query.filter_by(email="crew@example.com").first()
        crew = Crew(
            name="Invite Crew",
            activity_type="walk",
            visibility="public",
            meeting_point_name="Park Gate",
            meeting_latitude=-1.1452,
            meeting_longitude=36.9561,
            created_by=organizer.id,
        )
        db.session.add(crew)
        db.session.flush()
        db.session.add(CrewMember(crew_id=crew.id, user_id=organizer.id, role="organizer"))
        db.session.commit()
        crew_id = crew.id

    response = client.post(f"/api/crews/{crew_id}/join", headers={"Authorization": f"Bearer {member_token}"})

    assert response.status_code == 200
    members = response.get_json()["crew"]["members"]
    assert any(member["name"] == "Invited User" for member in members)
