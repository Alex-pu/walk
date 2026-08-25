from app import create_app
from app.extensions import db


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


def test_report_and_block_user():
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        db.create_all()

    token, _ = _register(client, "reporter@example.com")
    _, reported_user_id = _register(client, "reported@example.com")

    report = client.post(
        "/api/safety/reports",
        headers={"Authorization": f"Bearer {token}"},
        json={"reported_user_id": reported_user_id, "reason": "unsafe_behavior", "details": "Did not check out."},
    )
    assert report.status_code == 201
    assert report.get_json()["report"]["reason"] == "unsafe_behavior"

    block = client.post(
        "/api/safety/blocks",
        headers={"Authorization": f"Bearer {token}"},
        json={"blocked_user_id": reported_user_id},
    )
    assert block.status_code == 201

    blocks = client.get("/api/safety/blocks", headers={"Authorization": f"Bearer {token}"})
    assert blocks.status_code == 200
    assert len(blocks.get_json()["blocks"]) == 1


def test_organizer_can_view_crew_reports():
    from app.models import Crew, CrewMember, User

    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        db.create_all()

    organizer_token, organizer_id = _register(client, "organizer@example.com")
    reporter_token, _ = _register(client, "reporter2@example.com")
    _, reported_user_id = _register(client, "reported2@example.com")

    with app.app_context():
        crew = Crew(
            name="Safety Crew",
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
        db.session.commit()
        crew_id = crew.id

    client.post(
        "/api/safety/reports",
        headers={"Authorization": f"Bearer {reporter_token}"},
        json={"reported_user_id": reported_user_id, "crew_id": crew_id, "reason": "unsafe_behavior"},
    )

    reports = client.get(f"/api/crews/{crew_id}/reports", headers={"Authorization": f"Bearer {organizer_token}"})
    assert reports.status_code == 200
    assert len(reports.get_json()["reports"]) == 1
