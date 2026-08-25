from io import BytesIO

from app import create_app
from app.extensions import db
from app.models import Crew, CrewApplication, CrewMember, User


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


def test_platform_admin_can_promote_user_and_crew_member():
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        db.create_all()

    admin_token, admin_id = _register(client, "admin@example.com")
    _, member_id = _register(client, "member@example.com")

    with app.app_context():
        admin = db.session.get(User, admin_id)
        admin.platform_role = "admin"
        crew = Crew(
            name="Admin Crew",
            activity_type="walk",
            visibility="public",
            meeting_point_name="Park Gate",
            meeting_latitude=-1.1452,
            meeting_longitude=36.9561,
            created_by=admin_id,
        )
        db.session.add(crew)
        db.session.flush()
        db.session.add(CrewMember(crew_id=crew.id, user_id=member_id, role="member"))
        db.session.commit()
        crew_id = crew.id

    promoted_user = client.patch(
        f"/api/admin/users/{member_id}/role",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"platform_role": "admin"},
    )
    assert promoted_user.status_code == 200
    assert promoted_user.get_json()["user"]["platform_role"] == "admin"

    promoted_member = client.patch(
        f"/api/crews/{crew_id}/members/{member_id}/role",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"role": "organizer"},
    )
    assert promoted_member.status_code == 200
    assert promoted_member.get_json()["member"]["role"] == "organizer"


def test_non_admin_cannot_view_admin_overview():
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        db.create_all()

    token, _ = _register(client, "regular@example.com")
    response = client.get("/api/admin/overview", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403


def test_admin_can_approve_crew_application(tmp_path):
    app = create_app(TestConfig)
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    client = app.test_client()

    with app.app_context():
        db.create_all()

    admin_token, admin_id = _register(client, "admin@example.com")
    applicant_token, applicant_id = _register(client, "applicant@example.com")

    with app.app_context():
        admin = db.session.get(User, admin_id)
        admin.platform_role = "admin"
        db.session.commit()

    response = client.post(
        "/api/crews/applications",
        headers={"Authorization": f"Bearer {applicant_token}"},
        data={
            "proposed_name": "Ruiru Sunrise Walkers",
            "activity_type": "walk",
            "visibility": "public",
            "meeting_point_name": "Ruiru Stadium",
            "meeting_latitude": "-1.1452",
            "meeting_longitude": "36.9561",
            "locality": "Ruiru",
            "id_number": "12345678",
            "selfie": (BytesIO(b"fake-image"), "selfie.jpg"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 201
    application_id = response.get_json()["application"]["id"]

    overview = client.get("/api/admin/overview", headers={"Authorization": f"Bearer {admin_token}"})
    assert overview.status_code == 200
    applications = overview.get_json()["crew_applications"]
    assert applications[0]["id_number"] == "12345678"

    selfie = client.get(
        f"/api/admin/crew-applications/{application_id}/selfie",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert selfie.status_code == 200

    approved = client.patch(
        f"/api/admin/crew-applications/{application_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "approved"},
    )

    assert approved.status_code == 200
    body = approved.get_json()
    assert body["crew"]["name"] == "Ruiru Sunrise Walkers"

    with app.app_context():
        application = db.session.get(CrewApplication, application_id)
        member = CrewMember.query.filter_by(crew_id=application.crew_id, user_id=applicant_id).first()
        assert application.status == "approved"
        assert member.role == "organizer"


def test_admin_can_send_broadcast(monkeypatch):
    app = create_app(TestConfig)
    client = app.test_client()
    sent = []

    with app.app_context():
        db.create_all()

    admin_token, admin_id = _register(client, "admin@example.com")
    _register(client, "member@example.com")

    with app.app_context():
        admin = db.session.get(User, admin_id)
        admin.platform_role = "admin"
        db.session.commit()

    def fake_send_email(to_email, subject, body):
        sent.append((to_email, subject, body))
        return True

    monkeypatch.setattr("app.routes.admin.send_email", fake_send_email)
    response = client.post(
        "/api/admin/broadcasts",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"subject": "Saturday walk", "body": "Meet at 7am."},
    )

    assert response.status_code == 200
    assert response.get_json()["sent"] == 2
    assert len(sent) == 2
