import os
import secrets
from datetime import timedelta
from pathlib import Path

from flask import Flask, g

from controllers import api_routes, page_routes
from models import initialize_database


BASE_DIR = Path(__file__).resolve().parent


def load_secret_key(instance_directory=None):
    configured_key = os.environ.get("SECRET_KEY")
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
    configured_key = os.environ.get("SECRET_KEY") or (test_config or {}).get("SECRET_KEY")
    app = Flask(
        __name__,
        static_folder=None,
        template_folder=str(BASE_DIR / "templates"),
    )
    app.config.from_mapping(
        SECRET_KEY=configured_key or load_secret_key(),
        DATABASE=os.environ.get("DATABASE_PATH", str(BASE_DIR / "instance" / "elearning.sqlite3")),
        UPLOAD_FOLDER=os.environ.get("UPLOAD_FOLDER", str(BASE_DIR / "instance" / "uploads")),
        PROJECT_ROOT=str(BASE_DIR),
        MAX_CONTENT_LENGTH=6 * 1024 * 1024,
        BOOTSTRAP_ADMIN_EMAIL=os.environ.get("ADMIN_EMAIL", "").strip().lower(),
        BOOTSTRAP_ADMIN_PASSWORD=os.environ.get("ADMIN_PASSWORD", ""),
        GOOGLE_CLIENT_ID=os.environ.get("GOOGLE_CLIENT_ID", "").strip(),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "").lower() == "true",
        PERMANENT_SESSION_LIFETIME=timedelta(days=30),
    )
    if test_config:
        app.config.update(test_config)

    with app.app_context():
        initialize_database(app)

    @app.teardown_appcontext
    def close_database(_error=None):
        connection = g.pop("database", None)
        if connection is not None:
            connection.close()

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        return response

    app.register_blueprint(api_routes)
    app.register_blueprint(page_routes)
    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=False)
