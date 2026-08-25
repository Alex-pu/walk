from app import create_app
from app.extensions import db
from app.models import PasswordResetToken, User


class TestConfig:
    SECRET_KEY = "test"
    JWT_SECRET_KEY = "test-jwt"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FRONTEND_ORIGIN = "http://localhost:5173"


def test_register_and_me_flow():
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        db.create_all()

    response = client.post(
        "/api/auth/register",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "password123",
            "neighborhood": "Ruiru",
        },
    )

    assert response.status_code == 201
    token = response.get_json()["access_token"]

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.get_json()["user"]["email"] == "test@example.com"


def test_update_me_sets_private_location():
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        db.create_all()

    response = client.post(
        "/api/auth/register",
        json={
            "name": "Test User",
            "email": "location@example.com",
            "password": "password123",
            "neighborhood": "Ruiru",
        },
    )
    token = response.get_json()["access_token"]

    updated = client.patch(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Location User",
            "neighborhood": "Membley",
            "latitude": -1.1742,
            "longitude": 36.9318,
            "phone": "0700000000",
        },
    )

    assert updated.status_code == 200
    user = updated.get_json()["user"]
    assert user["neighborhood"] == "Membley"
    assert user["latitude"] == -1.1742
    assert user["longitude"] == 36.9318


def test_update_me_rejects_bad_coordinates():
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        db.create_all()

    response = client.post(
        "/api/auth/register",
        json={
            "name": "Test User",
            "email": "badcoords@example.com",
            "password": "password123",
            "neighborhood": "Ruiru",
        },
    )
    token = response.get_json()["access_token"]

    updated = client.patch(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"latitude": "near here"},
    )

    assert updated.status_code == 400


def test_password_reset_flow():
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        db.create_all()

    client.post(
        "/api/auth/register",
        json={
            "name": "Reset User",
            "email": "reset@example.com",
            "password": "password123",
            "neighborhood": "Ruiru",
        },
    )

    forgot = client.post("/api/auth/forgot-password", json={"email": "reset@example.com"})
    assert forgot.status_code == 200

    with app.app_context():
        user = User.query.filter_by(email="reset@example.com").first()
        reset = PasswordResetToken.query.filter_by(user_id=user.id).first()
        token = reset.token

    changed = client.post("/api/auth/reset-password", json={"token": token, "password": "newpassword123"})
    assert changed.status_code == 200

    login = client.post("/api/auth/login", json={"email": "reset@example.com", "password": "newpassword123"})
    assert login.status_code == 200
