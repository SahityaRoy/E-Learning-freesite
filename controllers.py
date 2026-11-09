import hashlib
import hmac
import re
import secrets
import sqlite3
import time
import uuid
import warnings
from functools import wraps
from io import BytesIO
from pathlib import Path

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from PIL import Image, UnidentifiedImageError
from models import (
    create_course,
    create_book,
    create_user,
    count_books,
    count_admin_accounts,
    create_quiz_attempt,
    delete_book,
    delete_course,
    delete_user_and_archive_attempts,
    find_user_by_email,
    get_account_data,
    get_book_by_id,
    get_course_by_id,
    get_database,
    get_quiz_statistics,
    get_user_by_id,
    hash_password,
    list_accounts,
    list_books,
    list_courses,
    normalize_email,
    public_account,
    update_book,
    update_course,
    valid_email,
    validate_book,
    validate_course,
    verify_password,
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


def auth_rate_limited(action, limit_config, window_config):
    """Apply a persistent rolling-window limit keyed by action and client IP."""
    def decorate(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if request.method != "POST":
                return view(*args, **kwargs)
            now = int(time.time())
            window = int(current_app.config[window_config])
            limit = int(current_app.config[limit_config])
            client_ip = request.remote_addr or "unknown"
            client_key = hmac.new(
                str(current_app.config["SECRET_KEY"]).encode("utf-8"),
                client_ip.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
            database = get_database()
            database.execute("BEGIN IMMEDIATE")
            database.execute(
                "DELETE FROM auth_rate_limit_events WHERE created_at <= ?",
                (now - max(window, 24 * 60 * 60),),
            )
            rows = database.execute(
                "SELECT created_at FROM auth_rate_limit_events "
                "WHERE action = ? AND client_key = ? AND created_at > ? "
                "ORDER BY created_at ASC",
                (action, client_key, now - window),
            ).fetchall()
            if len(rows) >= limit:
                retry_after = max(1, rows[0]["created_at"] + window - now)
                database.commit()
                if request.path == "/login":
                    flash("Bạn đã thử đăng nhập quá nhiều lần. Vui lòng thử lại sau.", "error")
                    response = render_template("admin_login.html"), 429
                    response = current_app.make_response(response)
                else:
                    response = current_app.make_response(
                        api_error("Bạn đã gửi quá nhiều yêu cầu. Vui lòng thử lại sau.", 429)
                    )
                response.headers["Retry-After"] = str(retry_after)
                return response

            database.execute(
                "INSERT INTO auth_rate_limit_events (action, client_key, created_at) "
                "VALUES (?, ?, ?)",
                (action, client_key, now),
            )
            database.commit()
            return view(*args, **kwargs)
        return wrapped
    return decorate


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


def admin_page_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            return redirect(url_for("pages.login_page"))
        user = get_user_by_id(user_id)
        if not user:
            session.clear()
            return redirect(url_for("pages.login_page"))
        if user["role"] != "admin":
            abort(403)
        g.current_user = user
        return view(*args, **kwargs)

    return wrapped


@page_routes.route("/login", methods=["GET", "POST"])
@auth_rate_limited("login", "AUTH_LOGIN_RATE_LIMIT", "AUTH_LOGIN_RATE_WINDOW")
def login_page():
    if request.method == "GET":
        user_id = session.get("user_id")
        user = get_user_by_id(user_id) if user_id else None
        if user and user["role"] == "admin":
            return redirect(url_for("pages.admin_books"))
        return render_template("admin_login.html")

    email = normalize_email(request.form.get("email", ""))
    password = request.form.get("password", "")
    user = find_user_by_email(email)
    if (
        not user
        or user["role"] != "admin"
        or not verify_password(user["password_hash"], password)
    ):
        flash("Email hoặc mật khẩu không chính xác.", "error")
        return render_template("admin_login.html"), 401

    session.clear()
    session.permanent = True
    session["user_id"] = user["id"]
    return redirect(url_for("pages.admin_books"))


@page_routes.post("/logout")
@admin_page_required
def admin_logout():
    session.clear()
    return redirect(url_for("pages.login_page"))


@page_routes.get("/admin/books")
@admin_page_required
def admin_books():
    return render_template("admin_books.html", books=list_books(), admin=g.current_user)


def validate_image_upload(uploaded_file):
    image_data = uploaded_file.stream.read(MAX_UPLOAD_SIZE + 1)
    if len(image_data) > MAX_UPLOAD_SIZE:
        return None, None, "Ảnh không được vượt quá 5 MB.", 413

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(image_data)) as image:
                extension = IMAGE_EXTENSIONS.get(image.format)
                if extension is None:
                    return None, None, "Chỉ hỗ trợ ảnh PNG, JPG, GIF hoặc WebP.", 400
                if image.width * image.height > MAX_IMAGE_PIXELS:
                    return None, None, "Kích thước ảnh vượt quá giới hạn cho phép.", 400
                image.verify()

            with Image.open(BytesIO(image_data)) as image:
                image.load()
    except (
        UnidentifiedImageError,
        OSError,
        SyntaxError,
        ValueError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ):
        return None, None, "File tải lên không phải ảnh hợp lệ.", 400

    return image_data, extension, None, None


def save_uploaded_image(image_data, extension, folder):
    filename = f"{uuid.uuid4().hex}{extension}"
    upload_folder = Path(folder)
    upload_folder.mkdir(parents=True, exist_ok=True)
    (upload_folder / filename).write_bytes(image_data)
    return filename


@page_routes.route("/admin/books/add", methods=["GET", "POST"])
@admin_page_required
def add_book():
    if request.method == "GET":
        return render_template("admin_book_form.html", book=None, admin=g.current_user)

    data, error = validate_book(request.form)
    if error:
        flash(error, "error")
        return render_template("admin_book_form.html", book=request.form, admin=g.current_user), 400

    cover_file = request.files.get("cover_image")
    if not cover_file or not cover_file.filename:
        flash("Vui lòng chọn ảnh bìa cho sách.", "error")
        return render_template("admin_book_form.html", book=request.form, admin=g.current_user), 400

    image_data, extension, error, status_code = validate_image_upload(cover_file)
    if error:
        flash(error, "error")
        return render_template("admin_book_form.html", book=request.form, admin=g.current_user), status_code

    filename = save_uploaded_image(image_data, extension, current_app.config["BOOK_UPLOAD_FOLDER"])
    data["cover_image"] = f"/static/uploads/books/{filename}"

    create_book(data)
    flash("Đã thêm sách mới.", "success")
    return redirect(url_for("pages.admin_books"))


@page_routes.route("/admin/books/edit/<int:book_id>", methods=["GET", "POST"])
@admin_page_required
def edit_book(book_id):
    book = get_book_by_id(book_id)
    if not book:
        abort(404)
    if request.method == "GET":
        return render_template("admin_book_form.html", book=book, admin=g.current_user)

    data, error = validate_book(request.form)
    if error:
        flash(error, "error")
        return render_template("admin_book_form.html", book={**dict(book), **request.form}, admin=g.current_user), 400

    cover_file = request.files.get("cover_image")
    image_data = None
    extension = None
    if cover_file and cover_file.filename:
        image_data, extension, error, status_code = validate_image_upload(cover_file)
        if error:
            flash(error, "error")
            return render_template("admin_book_form.html", book={**dict(book), **request.form}, admin=g.current_user), status_code

    old_cover = book["cover_image"]
    if image_data is not None and extension is not None:
        filename = save_uploaded_image(image_data, extension, current_app.config["BOOK_UPLOAD_FOLDER"])
        data["cover_image"] = f"/static/uploads/books/{filename}"
    else:
        data["cover_image"] = old_cover

    update_book(book_id, data)
    if data["cover_image"] != old_cover:
        remove_book_cover(old_cover)
    flash("Đã cập nhật thông tin sách.", "success")
    return redirect(url_for("pages.admin_books"))


@page_routes.post("/admin/books/delete/<int:book_id>")
@admin_page_required
def remove_book(book_id):
    book = get_book_by_id(book_id)
    if not book:
        abort(404)
    delete_book(book_id)
    remove_book_cover(book["cover_image"])
    flash("Đã xóa sách.", "success")
    return redirect(url_for("pages.admin_books"))


def remove_book_cover(cover_image):
    filename = re.fullmatch(
        r"/static/uploads/books/([a-f0-9]{32}\.(?:png|jpg|gif|webp))",
        str(cover_image or ""),
    )
    if filename:
        (Path(current_app.config["BOOK_UPLOAD_FOLDER"]) / filename.group(1)).unlink(missing_ok=True)


@api_routes.get("/api/auth/me")
@login_required
def current_account():
    return jsonify(public_account(g.current_user))


@api_routes.get("/api/csrf-token")
def csrf_token():
    token_key = current_app.config["CSRF_TOKEN_SESSION_KEY"]
    token = session.get(token_key)
    if not token:
        token = secrets.token_urlsafe(32)
        session[token_key] = token
    return jsonify({"csrf_token": token})


@api_routes.get("/api/auth/me/data")
@login_required
def current_account_data():
    return jsonify(get_account_data(g.current_user["id"]))


@api_routes.delete("/api/auth/me")
@login_required
def delete_current_account():
    user = g.current_user
    if user["role"] == "admin":
        if user["email"] == current_app.config["BOOTSTRAP_ADMIN_EMAIL"]:
            return api_error(
                "Hãy đổi cấu hình BOOTSTRAP_ADMIN_EMAIL trước khi xóa tài khoản bootstrap.",
                409,
            )
        if count_admin_accounts() <= 1:
            return api_error(
                "Cần có ít nhất một quản trị viên khác trước khi xóa tài khoản này.",
                409,
            )

    archived_attempts = delete_user_and_archive_attempts(user["id"])
    session.clear()
    return jsonify({
        "message": "Tài khoản đã được xóa; kết quả quiz đã chuyển thành số liệu tổng hợp.",
        "archived_attempts": archived_attempts,
    })


@api_routes.post("/api/auth/register")
@auth_rate_limited("register", "AUTH_REGISTER_RATE_LIMIT", "AUTH_REGISTER_RATE_WINDOW")
def register():
    data = json_payload()
    name = data.get("name", "")
    email = data.get("email", "")
    password = data.get("password", "")
    if not all(isinstance(value, str) for value in (name, email, password)):
        return api_error("Họ tên, email và mật khẩu phải có giá trị dạng chuỗi.", 400)
    name = name.strip()
    email = normalize_email(email)
    if not name or len(name) > 80:
        return api_error("Họ tên cần có từ 1 đến 80 ký tự.", 400)
    if not valid_email(email):
        return api_error("Email không hợp lệ.", 400)
    if len(password) < 8:
        return api_error("Mật khẩu cần có ít nhất 8 ký tự.", 400)

    try:
        user_id = create_user(name, email, hash_password(password), "user")
    except sqlite3.IntegrityError:
        return api_error("Email này đã được sử dụng.", 409)

    user = get_user_by_id(user_id)
    session.clear()
    session.permanent = True
    session["user_id"] = user["id"]
    return jsonify(public_account(user)), 201


@api_routes.post("/api/auth/login")
@auth_rate_limited("login", "AUTH_LOGIN_RATE_LIMIT", "AUTH_LOGIN_RATE_WINDOW")
def login():
    data = json_payload()
    email = data.get("email", "")
    password = data.get("password", "")
    if not isinstance(email, str) or not isinstance(password, str):
        return api_error("Email và mật khẩu phải có giá trị dạng chuỗi.", 400)
    email = normalize_email(email)
    if not email or not password or not valid_email(email):
        return api_error("Email hoặc mật khẩu không hợp lệ.", 400)
    user = find_user_by_email(email)
    if not user or not verify_password(user["password_hash"], password):
        return api_error("Email hoặc mật khẩu không chính xác.", 401)

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

    image_data, extension, error, status_code = validate_image_upload(uploaded_file)
    if error:
        return api_error(error, status_code)

    filename = save_uploaded_image(image_data, extension, current_app.config["UPLOAD_FOLDER"])
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


@api_routes.get("/api/admin/books/count")
@admin_required
def admin_book_count():
    return jsonify({"count": count_books()})


@api_routes.get("/api/admin/quiz/statistics")
@admin_required
def admin_quiz_statistics():
    return jsonify(get_quiz_statistics())


@api_routes.post("/api/quiz/attempts")
def save_quiz_attempt():
    data = json_payload()
    exam_id = str(data.get("examId", "")).strip()
    exam_title = str(data.get("title", "")).strip()
    subject = str(data.get("subject", "")).strip()
    correct_count = data.get("correct")
    total_questions = data.get("total")
    duration_seconds = data.get("duration")

    if not exam_id or len(exam_id) > 100:
        return api_error("Mã đề thi không hợp lệ.", 400)
    if not exam_title or len(exam_title) > 100 or not subject or len(subject) > 60:
        return api_error("Thông tin đề thi không hợp lệ.", 400)
    if type(total_questions) is not int or not 1 <= total_questions <= 200:
        return api_error("Số câu hỏi không hợp lệ.", 400)
    if type(correct_count) is not int or not 0 <= correct_count <= total_questions:
        return api_error("Số câu đúng không hợp lệ.", 400)
    if type(duration_seconds) is not int or not 0 <= duration_seconds <= 18000:
        return api_error("Thời gian làm bài không hợp lệ.", 400)

    user_id = session.get("user_id")
    if user_id and not get_user_by_id(user_id):
        user_id = None
    attempt_id = create_quiz_attempt({
        "exam_id": exam_id,
        "exam_title": exam_title,
        "subject": subject,
        "correct_count": correct_count,
        "total_questions": total_questions,
        "duration_seconds": duration_seconds,
    }, user_id)
    return jsonify({"id": attempt_id, "message": "Đã lưu kết quả bài thi."}), 201


@api_routes.post("/api/admin/users")
@admin_required
def create_admin():
    data = json_payload()
    name = data.get("name", "")
    email = data.get("email", "")
    password = data.get("password", "")
    if not all(isinstance(value, str) for value in (name, email, password)):
        return api_error("Họ tên, email và mật khẩu phải có giá trị dạng chuỗi.", 400)
    name = name.strip()
    email = normalize_email(email)
    if not name or len(name) > 80:
        return api_error("Họ tên cần có từ 1 đến 80 ký tự.", 400)
    if not valid_email(email):
        return api_error("Email không hợp lệ.", 400)
    if len(password) < 8:
        return api_error("Mật khẩu cần có ít nhất 8 ký tự.", 400)
    try:
        user_id = create_user(name, email, hash_password(password), "admin")
    except sqlite3.IntegrityError:
        return api_error("Email này đã được sử dụng.", 409)
    return jsonify(public_account(get_user_by_id(user_id))), 201


@page_routes.get("/")
def homepage():
    return render_template("index.html", books=list_books())


@page_routes.get("/courses/<int:course_id>")
def course_detail_page(course_id):
    course = get_course_by_id(course_id)
    if not course:
        abort(404)
    return render_template("course-detail.html", course=course)


@page_routes.get("/books/<int:book_id>")
def book_detail_page(book_id):
    book = get_book_by_id(book_id)
    if not book:
        abort(404)
    return render_template("book-detail.html", book=book)


@page_routes.get("/uploads/<path:filename>")
def uploaded_image(filename):
    if re.fullmatch(r"[a-f0-9]{32}\.(?:png|jpg|gif|webp)", filename) is None:
        return api_error("Không tìm thấy ảnh.", 404)
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename, max_age=3600)


@page_routes.get("/static/uploads/books/<path:filename>")
def uploaded_book_cover(filename):
    if re.fullmatch(r"[a-f0-9]{32}\.(?:png|jpg|gif|webp)", filename) is None:
        return api_error("Không tìm thấy ảnh bìa.", 404)
    return send_from_directory(current_app.config["BOOK_UPLOAD_FOLDER"], filename, max_age=3600)


@page_routes.get("/<path:filename>")
def view_or_static_file(filename):
    path = Path(filename)
    if any(part.startswith(".") for part in path.parts):
        return api_error("Không tìm thấy trang.", 404)
    if path.suffix.lower() not in STATIC_EXTENSIONS:
        return api_error("Không tìm thấy trang.", 404)
    if path.suffix.lower() == ".html":
        if path.as_posix() == "index.html":
            return render_template("index.html", books=list_books())
        return render_template(filename)
    return send_from_directory(current_app.config["PROJECT_ROOT"], filename)


def json_payload():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def api_error(message, status):
    return jsonify({"error": message}), status
