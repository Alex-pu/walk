import smtplib
from email.message import EmailMessage

from flask import current_app


def email_is_configured():
    return bool(current_app.config.get("MAIL_SERVER") and current_app.config.get("MAIL_DEFAULT_SENDER"))


def send_email(to_email, subject, body):
    if not email_is_configured():
        current_app.logger.info("Email skipped because SMTP is not configured: %s", subject)
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = current_app.config["MAIL_DEFAULT_SENDER"]
    message["To"] = to_email
    message.set_content(body)

    server = current_app.config["MAIL_SERVER"]
    port = current_app.config["MAIL_PORT"]
    username = current_app.config.get("MAIL_USERNAME")
    password = current_app.config.get("MAIL_PASSWORD")

    smtp_class = smtplib.SMTP_SSL if current_app.config.get("MAIL_USE_SSL") else smtplib.SMTP
    try:
        with smtp_class(server, port, timeout=20) as smtp:
            if current_app.config.get("MAIL_USE_TLS") and not current_app.config.get("MAIL_USE_SSL"):
                smtp.starttls()
            if username and password:
                smtp.login(username, password)
            smtp.send_message(message)
    except Exception as error:
        current_app.logger.exception("Email failed: %s", error)
        return False

    return True


def send_welcome_email(user):
    app_url = current_app.config.get("APP_PUBLIC_URL", "http://localhost:5173").rstrip("/")
    body = f"""Hi {user.name},

Welcome to Run Community Kenya.

You can discover crews, join nearby sessions, and track your walks or runs here:
{app_url}

Stay safe,
Run Community Kenya
"""
    return send_email(user.email, "Welcome to Run Community Kenya", body)


def send_password_reset_email(user, token):
    app_url = current_app.config.get("APP_PUBLIC_URL", "http://localhost:5173").rstrip("/")
    reset_url = f"{app_url}/reset-password?token={token}"
    body = f"""Hi {user.name},

Use this link to reset your password:
{reset_url}

This link expires in 1 hour. If you did not request it, you can ignore this email.

Run Community Kenya
"""
    return send_email(user.email, "Reset your Run Community Kenya password", body)
