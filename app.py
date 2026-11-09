import os
import re
import secrets
from datetime import timedelta
from pathlib import Path

from flask import Flask, g

from controllers import api_routes, page_routes
from models import initialize_database


BASE_DIR = Path(__file__).resolve().parent
SCRIPT_TAG_PATTERN = re.compile(r"<script\b(?![^>]*\bnonce\s*=)([^>]*)>", re.IGNORECASE)


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
        PERMANENT_SESSION_LIFETIME=timedelta(days=30),
        AUTH_LOGIN_RATE_LIMIT=int(os.environ.get("AUTH_LOGIN_RATE_LIMIT", "10")),
        AUTH_LOGIN_RATE_WINDOW=int(os.environ.get("AUTH_LOGIN_RATE_WINDOW", str(15 * 60))),
        AUTH_REGISTER_RATE_LIMIT=int(os.environ.get("AUTH_REGISTER_RATE_LIMIT", "5")),
        AUTH_REGISTER_RATE_WINDOW=int(os.environ.get("AUTH_REGISTER_RATE_WINDOW", str(60 * 60))),
    )
    if test_config:
        app.config.update(test_config)

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

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers["X-Frame-Options"] = "DENY"

        nonce = g.get("csp_nonce") or secrets.token_urlsafe(16)
        if response.mimetype == "text/html":
            response.direct_passthrough = False
            html = response.get_data(as_text=True)
            response.set_data(
                SCRIPT_TAG_PATTERN.sub(
                    lambda match: f'<script nonce="{nonce}"{match.group(1)}>',
                    html,
                )
            )

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

    app.register_blueprint(api_routes)
    app.register_blueprint(page_routes)
    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=False)
