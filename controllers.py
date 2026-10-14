import re
import sqlite3
import uuid
from functools import wraps
from io import BytesIO
from pathlib import Path

from flask import Blueprint, current_app, g, jsonify, render_template, request, send_from_directory, session
from google.auth.exceptions import InvalidValue, TransportError
from google.oauth2 import id_token
from google.auth.transport.requests import Request
from PIL import Image, UnidentifiedImageError
from werkzeug.security import check_password_hash, generate_password_hash

from models import (
    create_course,
    create_user,
    delete_course,
    find_user_by_email,
    find_user_by_google_id,
    get_course_by_id,
    get_database,
    get_user_by_id,
    list_accounts,
    list_courses,
    normalize_email,
    public_account,
    update_course,
    valid_email,
    validate_course,
)


page_routes = Blueprint("pages", __name__)
api_routes = Blueprint("api", __name__)
STATIC_EXTENSIONS = {
    ".css", ".gif", ".html", ".ico", ".jpeg", ".jpg", ".jfif", ".js",
    ".png", ".svg", ".webmanifest", ".webp",
}
IMAGE_EXTENSIONS = {"PNG": ".png", "JPEG": ".jpg", "GIF": ".gif", "WEBP": ".webp"}
MAX_UPLOAD_SIZE = 5 * 1024 * 1024
MAX_IMAGE_PIXELS = 25_000_000


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            return api_error("Vui lòng đăng nhập.", 401)
        user = get_user_by_id(user_id)
        if not user:
            session.clear()
            return api_error("Vui lòng đăng nhập.", 401)
        g.current_user = user
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if g.current_user["role"] != "admin":
            return api_error("Bạn không có quyền quản trị.", 403)
        return view(*args, **kwargs)

    return wrapped


@api_routes.get("/api/auth/me")
@login_required
def current_account():
    return jsonify(public_account(g.current_user))


@api_routes.get("/api/auth/google-config")
def google_config():
    return jsonify({"client_id": current_app.config.get("GOOGLE_CLIENT_ID", "")})


@api_routes.post("/api/auth/register")
def register():
    data = json_payload()
    name = str(data.get("name", "")).strip()
    email = normalize_email(data.get("email", ""))
    password = str(data.get("password", ""))
    if not name or len(name) > 80:
        return api_error("Họ tên cần có từ 1 đến 80 ký tự.", 400)
    if not valid_email(email):
        return api_error("Email không hợp lệ.", 400)
    if len(password) < 8:
        return api_error("Mật khẩu cần có ít nhất 8 ký tự.", 400)

    try:
        user_id = create_user(name, email, generate_password_hash(password), "user")
    except sqlite3.IntegrityError:
        return api_error("Email này đã được sử dụng.", 409)

    user = get_user_by_id(user_id)
    session.clear()
    session.permanent = True
    session["user_id"] = user["id"]
    return jsonify(public_account(user)), 201


@api_routes.post("/api/auth/login")
def login():
    data = json_payload()
    email = normalize_email(data.get("email", ""))
    password = str(data.get("password", ""))
    user = find_user_by_email(email)
    if not user or not check_password_hash(user["password_hash"], password):
        return api_error("Email hoặc mật khẩu không chính xác.", 401)

    session.clear()
    session.permanent = True
    session["user_id"] = user["id"]
    return jsonify(public_account(user))


def verify_google_id_token(credential):
    client_id = current_app.config.get("GOOGLE_CLIENT_ID", "").strip()
    if not client_id:
        return None
    try:
        return id_token.verify_oauth2_token(
            credential,
            Request(),
            audience=client_id,
        )
    except (InvalidValue, TransportError, ValueError):
        return None


@api_routes.post("/api/auth/google")
def google_login():
    data = json_payload()
    credential = str(data.get("credential", "")).strip()
    google_user = verify_google_id_token(credential)
    if not google_user:
        return api_error("Xác thực Google không thành công.", 401)

    google_id = str(google_user.get("sub", ""))
    email = normalize_email(google_user.get("email", ""))
    name = str(google_user.get("name", "")).strip() or email.split("@", 1)[0]
    if not google_id or not valid_email(email):
        return api_error("Google trả về thông tin tài khoản không hợp lệ.", 401)

    user = find_user_by_google_id(google_id)
    if not user:
        user = find_user_by_email(email)
        if user:
            get_database().execute(
                "UPDATE users SET google_id = ?, name = ? WHERE id = ?",
                (google_id, name, user["id"]),
            )
            get_database().commit()
            user = get_user_by_id(user["id"])
        else:
            user_id = create_user(name, email, generate_password_hash(google_id), "user")
            get_database().execute(
                "UPDATE users SET google_id = ? WHERE id = ?", (google_id, user_id)
            )
            get_database().commit()
            user = get_user_by_id(user_id)

    session.clear()
    session.permanent = True
    session["user_id"] = user["id"]
    return jsonify(public_account(user))


@api_routes.post("/api/auth/logout")
def logout():
    session.clear()
    return jsonify({"message": "Đã đăng xuất."})


@api_routes.get("/api/courses")
def courses():
    return jsonify([dict(course) for course in list_courses()])


@api_routes.post("/api/admin/uploads")
@admin_required
def upload_course_image():
    uploaded_file = request.files.get("image")
    if uploaded_file is None or not uploaded_file.filename:
        return api_error("Chọn một file ảnh để tải lên.", 400)

    image_data = uploaded_file.stream.read(MAX_UPLOAD_SIZE + 1)
    if len(image_data) > MAX_UPLOAD_SIZE:
        return api_error("Ảnh không được vượt quá 5 MB.", 413)
    try:
        with Image.open(BytesIO(image_data)) as image:
            extension = IMAGE_EXTENSIONS.get(image.format)
            if extension is None:
                return api_error("Chỉ hỗ trợ ảnh PNG, JPG, GIF hoặc WebP.", 400)
            if image.width * image.height > MAX_IMAGE_PIXELS:
                return api_error("Kích thước ảnh vượt quá giới hạn cho phép.", 400)
            image.verify()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        return api_error("File tải lên không phải ảnh hợp lệ.", 400)

    upload_folder = Path(current_app.config["UPLOAD_FOLDER"])
    upload_folder.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{extension}"
    (upload_folder / filename).write_bytes(image_data)
    return jsonify({"image_url": f"/uploads/{filename}"}), 201


@api_routes.post("/api/courses")
@admin_required
def create_course_route():
    data, error = validate_course(json_payload())
    if error:
        return api_error(error, 400)
    course_id = create_course(data)
    return jsonify(dict(get_course_by_id(course_id))), 201


@api_routes.put("/api/courses/<int:course_id>")
@admin_required
def update_course_route(course_id):
    data, error = validate_course(json_payload())
    if error:
        return api_error(error, 400)
    if not update_course(course_id, data):
        return api_error("Không tìm thấy khóa học.", 404)
    return jsonify(dict(get_course_by_id(course_id)))


@api_routes.delete("/api/courses/<int:course_id>")
@admin_required
def delete_course_route(course_id):
    if not delete_course(course_id):
        return api_error("Không tìm thấy khóa học.", 404)
    return jsonify({"message": "Đã xóa khóa học."})


@api_routes.get("/api/admin/users")
@admin_required
def admin_accounts():
    return jsonify([dict(user) for user in list_accounts()])


@api_routes.post("/api/admin/users")
@admin_required
def create_admin():
    data = json_payload()
    name = str(data.get("name", "")).strip()
    email = normalize_email(data.get("email", ""))
    password = str(data.get("password", ""))
    if not name or len(name) > 80:
        return api_error("Họ tên cần có từ 1 đến 80 ký tự.", 400)
    if not valid_email(email):
        return api_error("Email không hợp lệ.", 400)
    if len(password) < 8:
        return api_error("Mật khẩu cần có ít nhất 8 ký tự.", 400)
    try:
        user_id = create_user(name, email, generate_password_hash(password), "admin")
    except sqlite3.IntegrityError:
        return api_error("Email này đã được sử dụng.", 409)
    return jsonify(public_account(get_user_by_id(user_id))), 201


@page_routes.get("/")
def homepage():
    return render_template("index.html")


@page_routes.get("/auth.html")
def auth_page():
    return render_template("auth.html", google_client_id=current_app.config.get("GOOGLE_CLIENT_ID", ""))


@page_routes.get("/uploads/<path:filename>")
def uploaded_image(filename):
    path = Path(filename)
    if path.name != filename or path.suffix.lower() not in set(IMAGE_EXTENSIONS.values()):
        return api_error("Không tìm thấy ảnh.", 404)
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename, max_age=3600)


@page_routes.get("/<path:filename>")
def view_or_static_file(filename):
    path = Path(filename)
    if any(part.startswith(".") for part in path.parts):
        return api_error("Không tìm thấy trang.", 404)
    if path.suffix.lower() not in STATIC_EXTENSIONS:
        return api_error("Không tìm thấy trang.", 404)
    if path.suffix.lower() == ".html":
        return render_template(filename)
    return send_from_directory(current_app.config["PROJECT_ROOT"], filename)


def json_payload():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def api_error(message, status):
    return jsonify({"error": message}), status