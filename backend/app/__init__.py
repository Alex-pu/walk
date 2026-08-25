from flask import Flask, jsonify

from .config import Config
from .extensions import cors, db, jwt, migrate
from .routes.activities import activities_bp
from .routes.admin import admin_bp
from .routes.auth import auth_bp
from .routes.crews import crews_bp
from .routes.forum import forum_bp
from .routes.safety import safety_bp
from .routes.sessions import sessions_bp
from .services.email import send_email


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config["FRONTEND_ORIGIN"]}})

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(crews_bp, url_prefix="/api/crews")
    app.register_blueprint(forum_bp, url_prefix="/api/forum")
    app.register_blueprint(sessions_bp, url_prefix="/api/sessions")
    app.register_blueprint(activities_bp, url_prefix="/api/activities")
    app.register_blueprint(safety_bp, url_prefix="/api/safety")

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    @app.cli.command("test-email")
    def test_email():
        """Send a test email to MAIL_USERNAME."""
        recipient = app.config.get("MAIL_USERNAME")
        if not recipient:
            raise RuntimeError("MAIL_USERNAME is not configured")
        sent = send_email(
            recipient,
            "Run Community Kenya SMTP test",
            "If you received this, SMTP is configured correctly.",
        )
        print("Email sent." if sent else "Email failed. Check the Flask logs above.")

    return app
