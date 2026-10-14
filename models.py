import re
import sqlite3
from pathlib import Path
from urllib.parse import urlsplit

from flask import current_app, g
from werkzeug.security import generate_password_hash


DEFAULT_COURSES = [
    ("C++ From Basic To Advance", "Getting started with CPP", "images/picture/card-1.png", "https://www.youtube.com/watch?v=z9bZufPHFLU&list=PLfqMhTWNBTe0b2nM6JHVCnAkhQRGiZMSJ"),
    ("Java", "Kickstart your journey in Java", "images/picture/card-2.png", "https://www.youtube.com/watch?v=WOUpjal8ee4&list=PLsyeobzWxl7oZ-fxDYkOToURHhMuWD1BK"),
    ("C Programming", "Kickstart your coding journey with C", "images/picture/card-3.png", "https://www.youtube.com/watch?v=MoqYPc43ssk&list=PLXthElPLs7ZaGXGI-_ToQ670nr1RAtjRB"),
    ("Python Programming", "Getting started with Python", "images/picture/card-4.png", "https://www.youtube.com/watch?v=kqtD5dpn9C8"),
    ("Django Framework", "Master Django skills", "images/picture/card-5.png", "https://www.youtube.com/watch?v=UmljXZIypDc&list=PL-osiE80TeTtoQCKZ03TU5fNfx2UY6U4p"),
    ("HTML", "Learn HTML to create amazing web pages", "images/picture/card-6.png", "https://www.youtube.com/watch?v=dD2EISBDjWM&list=PLr6-GrHUlVf_ZNmuQSXdS197Oyr1L9sPB"),
    ("CSS", "Design amazing web pages with CSS", "images/picture/card-7.png", "https://www.youtube.com/watch?v=qKoajPPWpmo&list=PLr6-GrHUlVf8JIgLcu3sHigvQjTw_aC9C"),
    ("JavaScript", "Kickstart your coding journey in scripting", "images/picture/card-8.png", "https://www.youtube.com/watch?v=2md4HQNRqJA&list=PLRAV69dS1uWSxUIk5o3vQY2-_VKsOpXLD"),
    ("React JS", "Learn an amazing front-end framework", "images/picture/card-9.png", "https://www.youtube.com/watch?v=QFaFIcGhPoM&list=PLC3y8-rFHvwgg3vaYJgHGnModB54rxOk3"),
    ("Kotlin", "Kickstart your coding journey in Kotlin", "images/picture/card-11.png", "https://www.youtube.com/watch?v=VEqhzCFmEQI&list=PLlxmoA0rQ-LwgK1JsnMsakYNACYGa1cjR"),
    ("Angular", "Head for Google's framework", "images/picture/card-10.png", "https://www.youtube.com/watch?v=0eWrpsCLMJQ&list=PLC3y8-rFHvwhBRAgFinJR8KHIrCdTkZcZ"),
    ("SQL", "Start understanding databases", "images/picture/card-12.png", "https://www.youtube.com/watch?v=7GVFYt6_ZFM&list=PL08903FB7ACA1C2FB"),
    ("Flutter", "Kickstart your coding journey in Flutter", "images/picture/card-14.png", "https://www.youtube.com/watch?v=VPvVD8t02U8"),
    ("PyTorch", "Explore machine learning with PyTorch", "images/picture/card-13.jpg", "https://www.youtube.com/watch?v=V_xro1bcAuA"),
    ("PHP", "Create dynamic websites with PHP", "images/picture/card-15.jfif", "https://www.youtube.com/watch?v=7GVFYt6_ZFM&list=PL08903FB7ACA1C2FB"),
    ("Nest.js", "Create a REST API", "images/picture/card-16.jpg", "https://www.youtube.com/watch?v=GHTA143_b-s"),
    ("Tailwind CSS", "Responsive web designs with Tailwind CSS", "images/picture/card-17.png", "https://www.youtube.com/watch?v=lZp4salRFFc"),
    ("Bootstrap", "Create interactive websites with Bootstrap", "images/picture/card-18.png", "https://www.youtube.com/watch?v=-qfEOE4vtxE"),
]


def get_database():
    if "database" not in g:
        connection = sqlite3.connect(current_app.config["DATABASE"])
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        g.database = connection
    return g.database


def initialize_database(app):
    database_path = Path(app.config["DATABASE"])
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            google_id TEXT UNIQUE,
            role TEXT NOT NULL CHECK (role IN ('user', 'admin')),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            image_url TEXT NOT NULL DEFAULT '',
            course_url TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    if connection.execute("SELECT COUNT(*) FROM courses").fetchone()[0] == 0:
        connection.executemany(
            "INSERT INTO courses (title, description, image_url, course_url) VALUES (?, ?, ?, ?)",
            DEFAULT_COURSES,
        )

    user_columns = {
        row[1] for row in connection.execute("PRAGMA table_info(users)")
    }
    if "google_id" not in user_columns:
        connection.execute("ALTER TABLE users ADD COLUMN google_id TEXT")
    connection.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id)"
    )

    admin_email = app.config["BOOTSTRAP_ADMIN_EMAIL"]
    admin_password = app.config["BOOTSTRAP_ADMIN_PASSWORD"]
    if bool(admin_email) != bool(admin_password):
        connection.close()
        raise RuntimeError("Set both ADMIN_EMAIL and ADMIN_PASSWORD to bootstrap the first admin.")
    if admin_email:
        existing = connection.execute(
            "SELECT role FROM users WHERE email = ? COLLATE NOCASE", (admin_email,)
        ).fetchone()
        if existing and existing["role"] != "admin":
            connection.close()
            raise RuntimeError("The bootstrap admin email already belongs to a user account.")
        if not existing:
            connection.execute(
                "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, 'admin')",
                ("Quản trị viên", admin_email, generate_password_hash(admin_password)),
            )
    connection.commit()
    connection.close()


def normalize_email(value):
    return str(value).strip().lower()


def valid_email(email):
    return len(email) <= 254 and re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email) is not None


def public_account(user):
    return {"id": user["id"], "name": user["name"], "email": user["email"], "role": user["role"]}


def validate_course(data):
    title = str(data.get("title", "")).strip()
    description = str(data.get("description", "")).strip()
    image_url = str(data.get("image_url", "")).strip()
    course_url = str(data.get("course_url", "")).strip()
    if not title or len(title) > 150:
        return None, "Tên khóa học cần có từ 1 đến 150 ký tự."
    if len(description) > 1200:
        return None, "Mô tả không được vượt quá 1200 ký tự."
    parsed_course_url = urlsplit(course_url)
    if parsed_course_url.scheme not in {"http", "https"} or not parsed_course_url.netloc:
        return None, "Liên kết khóa học phải bắt đầu bằng http:// hoặc https://."
    if image_url:
        parsed_image_url = urlsplit(image_url)
        is_local_image = image_url.startswith("images/") and ".." not in Path(image_url).parts
        is_uploaded_image = re.fullmatch(r"/uploads/[a-f0-9]{32}\.(?:png|jpg|gif|webp)", image_url) is not None
        is_external_image = parsed_image_url.scheme in {"http", "https"} and bool(parsed_image_url.netloc)
        if not (is_local_image or is_uploaded_image or is_external_image):
            return None, "Ảnh cần là đường dẫn images/ hoặc URL http(s)."
    return {
        "title": title,
        "description": description,
        "image_url": image_url,
        "course_url": course_url,
    }, None


def find_user_by_email(email):
    return get_database().execute(
        "SELECT * FROM users WHERE email = ? COLLATE NOCASE", (email,)
    ).fetchone()


def find_user_by_google_id(google_id):
    return get_database().execute(
        "SELECT * FROM users WHERE google_id = ?", (google_id,)
    ).fetchone()


def get_user_by_id(user_id):
    return get_database().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def create_user(name, email, password_hash, role):
    cursor = get_database().execute(
        "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
        (name, email, password_hash, role),
    )
    get_database().commit()
    return cursor.lastrowid


def list_accounts():
    return get_database().execute(
        "SELECT id, name, email, role, created_at FROM users ORDER BY role DESC, id"
    ).fetchall()


def list_courses():
    return get_database().execute("SELECT * FROM courses ORDER BY id ASC").fetchall()


def get_course_by_id(course_id):
    return get_database().execute("SELECT * FROM courses WHERE id = ?", (course_id,)).fetchone()


def create_course(data):
    cursor = get_database().execute(
        "INSERT INTO courses (title, description, image_url, course_url) VALUES (?, ?, ?, ?)",
        (data["title"], data["description"], data["image_url"], data["course_url"]),
    )
    get_database().commit()
    return cursor.lastrowid


def update_course(course_id, data):
    cursor = get_database().execute(
        "UPDATE courses SET title = ?, description = ?, image_url = ?, course_url = ? WHERE id = ?",
        (data["title"], data["description"], data["image_url"], data["course_url"], course_id),
    )
    if cursor.rowcount:
        get_database().commit()
    return cursor.rowcount > 0


def delete_course(course_id):
    cursor = get_database().execute("DELETE FROM courses WHERE id = ?", (course_id,))
    if cursor.rowcount:
        get_database().commit()
    return cursor.rowcount > 0