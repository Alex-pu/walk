from datetime import datetime, timezone

from app import create_app
from app.extensions import db
from app.models import Crew, CrewMember, Session, SessionAttendance, User


class TestConfig:
    SECRET_KEY = "test"
    JWT_SECRET_KEY = "test-jwt"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FRONTEND_ORIGIN = "http://localhost:5173"


def _register(client, email):
    response = client.post(
        "/api/auth/register",
        json={
            "name": email.split("@")[0],
            "email": email,
            "password": "password123",
            "neighborhood": "Ruiru",
        },
    )
    data = response.get_json()
    return data["access_token"], data["user"]["id"]


def _session_fixture(client):
    organizer_token, organizer_id = _register(client, "organizer@example.com")
    member_token, member_id = _register(client, "walker@example.com")
    with client.application.app_context():
        crew = Crew(
            name="Session Crew",
            activity_type="walk",
            visibility="public",
            meeting_point_name="Park Gate",
            meeting_latitude=-1.1452,
            meeting_longitude=36.9561,
            created_by=organizer_id,
        )
        db.session.add(crew)
        db.session.flush()
        db.session.add(CrewMember(crew_id=crew.id, user_id=organizer_id, role="organizer"))
        db.session.add(CrewMember(crew_id=crew.id, user_id=member_id, role="member"))
        session = Session(
            crew_id=crew.id,
            title="Stateful Walk",
            activity_type="walk",
            scheduled_start=datetime.now(timezone.utc),
            meeting_point_name=crew.meeting_point_name,
            meeting_latitude=crew.meeting_latitude,
            meeting_longitude=crew.meeting_longitude,
            created_by=organizer_id,
        )
        db.session.add(session)
        db.session.commit()
        return organizer_token, member_token, member_id, session.id


def test_session_detail_includes_current_user_attendance():
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        db.create_all()

    _, member_token, _, session_id = _session_fixture(client)

    joined = client.post(f"/api/sessions/{session_id}/join", headers={"Authorization": f"Bearer {member_token}"})
    assert joined.status_code == 200

    detail = client.get(f"/api/sessions/{session_id}", headers={"Authorization": f"Bearer {member_token}"})
    body = detail.get_json()["session"]
    assert body["current_user_attendance"]["status"] == "going"
    assert body["can_manage_session"] is False


def test_organizer_can_complete_session_and_mark_no_shows():
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        db.create_all()

    organizer_token, member_token, member_id, session_id = _session_fixture(client)
    client.post(f"/api/sessions/{session_id}/join", headers={"Authorization": f"Bearer {member_token}"})

    no_show = client.post(
        f"/api/sessions/{session_id}/attendees/{member_id}/no-show",
        headers={"Authorization": f"Bearer {organizer_token}"},
    )
    assert no_show.status_code == 200
    assert no_show.get_json()["session"]["attendees"][0]["status"] == "no_show"

    completed = client.post(f"/api/sessions/{session_id}/complete", headers={"Authorization": f"Bearer {organizer_token}"})
    assert completed.status_code == 200
    assert completed.get_json()["session"]["status"] == "completed"


def test_member_cannot_cancel_session():
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        db.create_all()

    _, member_token, _, session_id = _session_fixture(client)
    response = client.post(f"/api/sessions/{session_id}/cancel", headers={"Authorization": f"Bearer {member_token}"})

    assert response.status_code == 403
