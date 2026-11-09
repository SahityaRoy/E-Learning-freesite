import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path

import click
from flask import Flask, g, jsonify, request, session

from controllers import api_routes, page_routes
from models import archive_expired_quiz_attempts, initialize_database


BASE_DIR = Path(__file__).resolve().parent
SCRIPT_TAG_PATTERN = re.compile(r"<script\b(?![^>]*\bnonce\s*=)([^>]*)>", re.IGNORECASE)
HTML_HEAD_CLOSE_PATTERN = re.compile(r"</head\s*>", re.IGNORECASE)


def load_secret_key(instance_directory=None):
    configured_key = os.environ.get("SECRET_KEY", "").strip()
    if configured_key:
        return configured_key

    secret_directory = Path(instance_directory or BASE_DIR / "instance")
    secret_directory.mkdir(parents=True, exist_ok=True)
    secret_path = secret_directory / "secret_key"
    try:
        with secret_path.open("x", encoding="utf-8") as secret_file:
            secret_file.write(secrets.token_hex(32))
    except FileExistsError:
        pass
    return secret_path.read_text(encoding="utf-8").strip()


def create_app(test_config=None):
    app_environment = str(
        (test_config or {}).get("APP_ENV", os.environ.get("APP_ENV", "development"))
    ).strip().lower()
    environment_key = os.environ.get("SECRET_KEY", "").strip()
    if app_environment == "production" and not environment_key:
        raise RuntimeError(
            "SECRET_KEY must be set in the environment before starting in production."
        )

    configured_key = environment_key or (test_config or {}).get("SECRET_KEY")
    app = Flask(
        __name__,
        static_folder=None,
        template_folder=str(BASE_DIR / "templates"),
    )
    app.config.from_mapping(
        APP_ENV=app_environment,
        SECRET_KEY=configured_key or load_secret_key(),
        DATABASE=os.environ.get("DATABASE_PATH", str(BASE_DIR / "instance" / "elearning.sqlite3")),
        UPLOAD_FOLDER=os.environ.get("UPLOAD_FOLDER", str(BASE_DIR / "instance" / "uploads")),
        BOOK_UPLOAD_FOLDER=os.environ.get(
            "BOOK_UPLOAD_FOLDER", str(BASE_DIR / "instance" / "uploads" / "books")
        ),
        PROJECT_ROOT=str(BASE_DIR),
        MAX_CONTENT_LENGTH=6 * 1024 * 1024,
        BOOTSTRAP_ADMIN_EMAIL=os.environ.get(
            "ADMIN_EMAIL", "" if app_environment == "production" else "admin@eschool.com"
        ).strip().lower(),
        BOOTSTRAP_ADMIN_PASSWORD=os.environ.get(
            "ADMIN_PASSWORD", "" if app_environment == "production" else "admin123"
        ),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=(
            app_environment == "production"
            or os.environ.get("SESSION_COOKIE_SECURE", "").lower() == "true"
        ),
        HSTS_ENABLED=os.environ.get("HSTS_ENABLED", "").lower() == "true",
        CSRF_ENABLED=True,
        CSRF_TOKEN_SESSION_KEY="_csrf_token",
        QUIZ_ATTEMPT_RETENTION_DAYS=int(
            os.environ.get("QUIZ_ATTEMPT_RETENTION_DAYS", "365")
        ),
        PERMANENT_SESSION_LIFETIME=timedelta(days=30),
        AUTH_LOGIN_RATE_LIMIT=int(os.environ.get("AUTH_LOGIN_RATE_LIMIT", "10")),
        AUTH_LOGIN_RATE_WINDOW=int(os.environ.get("AUTH_LOGIN_RATE_WINDOW", str(15 * 60))),
        AUTH_REGISTER_RATE_LIMIT=int(os.environ.get("AUTH_REGISTER_RATE_LIMIT", "5")),
        AUTH_REGISTER_RATE_WINDOW=int(os.environ.get("AUTH_REGISTER_RATE_WINDOW", str(60 * 60))),
    )
    if test_config:
        app.config.update(test_config)
    if app.config["QUIZ_ATTEMPT_RETENTION_DAYS"] < 1:
        raise ValueError("QUIZ_ATTEMPT_RETENTION_DAYS must be a positive integer.")

    Path(app.config["BOOK_UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

    with app.app_context():
        initialize_database(app)

    @app.teardown_appcontext
    def close_database(_error=None):
        connection = g.pop("database", None)
        if connection is not None:
            connection.close()

    @app.before_request
    def create_content_security_nonce():
        g.csp_nonce = secrets.token_urlsafe(16)
        if request.method in {"GET", "HEAD", "OPTIONS"}:
            return None

        if not app.config["CSRF_ENABLED"]:
            return None

        expected_token = session.get(app.config["CSRF_TOKEN_SESSION_KEY"])
        supplied_token = request.headers.get("X-CSRF-Token")
        if supplied_token is None:
            supplied_token = request.form.get("_csrf_token")
        if (
            not expected_token
            or not supplied_token
            or not secrets.compare_digest(expected_token, supplied_token)
        ):
            message = "CSRF token is missing or invalid."
            if request.path.startswith("/api/"):
                return jsonify({"error": message}), 400
            return message, 400

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers["X-Frame-Options"] = "DENY"

        nonce = g.get("csp_nonce") or secrets.token_urlsafe(16)
        is_html = response.mimetype == "text/html"
        should_issue_csrf_token = (
            is_html
            or request.path == "/api/csrf-token"
            or (
                request.path.startswith("/api/")
                and request.method not in {"GET", "HEAD", "OPTIONS"}
            )
        )
        csrf_token = None
        if should_issue_csrf_token:
            csrf_token = session.get(app.config["CSRF_TOKEN_SESSION_KEY"])
            if not csrf_token:
                csrf_token = secrets.token_urlsafe(32)
                session[app.config["CSRF_TOKEN_SESSION_KEY"]] = csrf_token
            response.headers["X-CSRF-Token"] = csrf_token
            response.vary.add("Cookie")

        if is_html:
            response.direct_passthrough = False
            html = response.get_data(as_text=True)
            csrf_meta_tag = (
                f'<meta name="csrf-token" content="{escape(csrf_token, quote=True)}">'
            )
            html = HTML_HEAD_CLOSE_PATTERN.sub(
                lambda match: f"{csrf_meta_tag}\n{match.group(0)}",
                html,
                count=1,
            )
            response.set_data(
                SCRIPT_TAG_PATTERN.sub(
                    lambda match: f'<script nonce="{nonce}"{match.group(1)}>',
                    html,
                )
            )

        if request.path == "/api/csrf-token":
            response.headers["Cache-Control"] = "no-store"

        response.headers["Content-Security-Policy"] = "; ".join((
            "default-src 'self'",
            "base-uri 'self'",
            "object-src 'none'",
            "frame-ancestors 'none'",
            "form-action 'self'",
            (
                "script-src 'self' "
                f"'nonce-{nonce}' "
                "https://ajax.googleapis.com https://cdn.jsdelivr.net "
                "https://cdn.tailwindcss.com https://code.jquery.com "
                "https://stackpath.bootstrapcdn.com https://use.fontawesome.com"
            ),
            (
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com "
                "https://cdnjs.cloudflare.com https://stackpath.bootstrapcdn.com "
                "https://maxcdn.bootstrapcdn.com https://use.fontawesome.com"
            ),
            (
                "font-src 'self' data: https://fonts.gstatic.com "
                "https://cdnjs.cloudflare.com https://use.fontawesome.com"
            ),
            "img-src 'self' data: https:",
            "connect-src 'self'",
        ))
        if app.config["HSTS_ENABLED"]:
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        return response

    @app.cli.command("archive-expired-quiz-attempts")
    @click.option("--retention-days", type=click.IntRange(min=1), default=None)
    def archive_expired_quiz_attempts_command(retention_days):
        days = retention_days or app.config["QUIZ_ATTEMPT_RETENTION_DAYS"]
        cutoff = (
            datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
        ).strftime("%Y-%m-%d %H:%M:%S")
        count = archive_expired_quiz_attempts(cutoff)
        click.echo(
            f"Archived {count} expired quiz attempts into monthly aggregates "
            f"using a {days}-day retention period."
        )

    @app.context_processor
    def inject_csrf_token():
        token = session.get(app.config["CSRF_TOKEN_SESSION_KEY"])
        if not token:
            token = secrets.token_urlsafe(32)
            session[app.config["CSRF_TOKEN_SESSION_KEY"]] = token
        return {"csrf_token": token}

    app.register_blueprint(api_routes)
    app.register_blueprint(page_routes)
    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=False)
