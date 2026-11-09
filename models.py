import re
import sqlite3
from pathlib import Path
from urllib.parse import urlsplit

from flask import current_app, g
from werkzeug.security import check_password_hash, generate_password_hash


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

DEFAULT_BOOKS = [
    (
        "Clean Code: A Handbook of Agile Software Craftsmanship",
        "Robert C. Martin (Uncle Bob)",
        "https://images.unsplash.com/photo-1544947950-fa07a98d237f?auto=format&fit=crop&w=600&q=80",
        "Khác / Best Practices",
        "Cuốn sách kinh điển hướng dẫn cách viết mã nguồn sạch, dễ đọc, dễ bảo trì và tối ưu cho lập trình viên.",
        "https://www.oreilly.com/library/view/clean-code-a/9780132350884/",
    ),
    (
        "The C++ Programming Language (4th Edition)",
        "Bjarne Stroustrup",
        "https://images.unsplash.com/photo-1512820790803-83ca734da794?auto=format&fit=crop&w=600&q=80",
        "C++",
        "Cuốn sách đầy đủ và chính thống nhất về ngôn ngữ C++ do chính cha đẻ Bjarne Stroustrup biên soạn.",
        "https://www.stroustrup.com/4th.html",
    ),
    (
        "Python Crash Course: A Hands-On, Project-Based Introduction to Programming",
        "Eric Matthes",
        "https://images.unsplash.com/photo-1532012197267-da84d127e765?auto=format&fit=crop&w=600&q=80",
        "Python",
        "Cuốn sách bán chạy nhất thế giới dành cho người mới bắt đầu học Python qua các dự án thực tế.",
        "https://nostarch.com/pythoncrashcourse2e",
    ),
    (
        "Effective Java (3rd Edition)",
        "Joshua Bloch",
        "https://images.unsplash.com/photo-1519682337058-a94d519337bc?auto=format&fit=crop&w=600&q=80",
        "Java",
        "Cẩm nang không thể thiếu dành cho các Java Developer muốn nâng cao tư duy thiết kế và tối ưu mã nguồn Java.",
        "https://www.oreilly.com/library/view/effective-java-3rd/9780134686097/",
    ),
    (
        "Eloquent JavaScript: A Modern Introduction to Programming",
        "Marijn Haverbeke",
        "https://images.unsplash.com/photo-1543002588-bfa74002ed7e?auto=format&fit=crop&w=600&q=80",
        "Web Development",
        "Cuốn sách tuyệt vời về ngôn ngữ JavaScript hiện đại, từ tư duy lập trình căn bản đến các ứng dụng web phức tạp.",
        "https://eloquentjavascript.net/",
    ),
    (
        "Head First Design Patterns",
        "Eric Freeman & Elisabeth Robson",
        "https://images.unsplash.com/photo-1516979187457-637abb4f9353?auto=format&fit=crop&w=600&q=80",
        "Khác / Architecture",
        "Hướng dẫn trực quan, sinh động về các mẫu thiết kế phần mềm (Design Patterns) phổ biến trong công nghiệp.",
        "https://www.oreilly.com/library/view/head-first-design/9781492077992/",
    ),
]


def seed_books(connection):
    if connection.execute("SELECT COUNT(*) FROM books").fetchone()[0] != 0:
        return
    connection.executemany(
        "INSERT INTO books (title, author, cover_image, category, description, document_url) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        DEFAULT_BOOKS,
    )


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
            role TEXT NOT NULL CHECK (role IN ('user', 'admin')),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            image_url TEXT NOT NULL DEFAULT '',
            course_url TEXT NOT NULL,
            details TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            cover_image TEXT NOT NULL DEFAULT '',
            category TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            details TEXT NOT NULL DEFAULT '',
            document_url TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS quiz_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            exam_id TEXT NOT NULL,
            exam_title TEXT NOT NULL,
            subject TEXT NOT NULL,
            correct_count INTEGER NOT NULL,
            total_questions INTEGER NOT NULL,
            score INTEGER NOT NULL,
            duration_seconds INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS quiz_monthly_aggregates (
            period_month TEXT NOT NULL,
            exam_id TEXT NOT NULL,
            exam_title TEXT NOT NULL,
            subject TEXT NOT NULL,
            attempts INTEGER NOT NULL,
            score_total INTEGER NOT NULL,
            correct_count INTEGER NOT NULL,
            total_questions INTEGER NOT NULL,
            best_score INTEGER NOT NULL,
            PRIMARY KEY (period_month, exam_id, exam_title, subject)
        );
        CREATE TABLE IF NOT EXISTS auth_rate_limit_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            client_key TEXT NOT NULL,
            created_at INTEGER NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_auth_rate_limit_events_client
            ON auth_rate_limit_events(action, client_key, created_at);
        CREATE INDEX IF NOT EXISTS idx_auth_rate_limit_events_created_at
            ON auth_rate_limit_events(created_at);
        CREATE INDEX IF NOT EXISTS idx_quiz_attempts_created_at
            ON quiz_attempts(created_at DESC, id DESC);
        CREATE INDEX IF NOT EXISTS idx_quiz_attempts_exam_id
            ON quiz_attempts(exam_id);
        """
    )
    course_columns = {row["name"] for row in connection.execute("PRAGMA table_info(courses)")}
    if "details" not in course_columns:
        connection.execute("ALTER TABLE courses ADD COLUMN details TEXT NOT NULL DEFAULT ''")
    book_columns = {row["name"] for row in connection.execute("PRAGMA table_info(books)")}
    if "details" not in book_columns:
        connection.execute("ALTER TABLE books ADD COLUMN details TEXT NOT NULL DEFAULT ''")
    if connection.execute("SELECT COUNT(*) FROM courses").fetchone()[0] == 0:
        connection.executemany(
            "INSERT INTO courses (title, description, image_url, course_url) VALUES (?, ?, ?, ?)",
            DEFAULT_COURSES,
        )
    seed_books(connection)

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
            print(f"Admin account initialized: {admin_email}")
    connection.commit()
    connection.close()


def normalize_email(value):
    return str(value).strip().lower()


def hash_password(password):
    return generate_password_hash(password)


def verify_password(password_hash, password):
    return check_password_hash(password_hash, password)


def valid_email(email):
    return len(email) <= 254 and re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email) is not None


def public_account(user):
    return {"id": user["id"], "name": user["name"], "email": user["email"], "role": user["role"]}


def validate_course(data):
    fields = ("title", "description", "details", "image_url", "course_url")
    if any(not isinstance(data.get(field, ""), str) for field in fields):
        return None, "Các trường khóa học phải có giá trị dạng chuỗi."

    title = data.get("title", "").strip()
    description = data.get("description", "").strip()
    details = data.get("details", "").strip()
    image_url = data.get("image_url", "").strip()
    course_url = data.get("course_url", "").strip()
    if not title or len(title) > 150:
        return None, "Tên khóa học cần có từ 1 đến 150 ký tự."
    if len(description) > 1200:
        return None, "Mô tả không được vượt quá 1200 ký tự."
    if len(details) > 5000:
        return None, "Nội dung chi tiết không được vượt quá 5000 ký tự."
    try:
        parsed_course_url = urlsplit(course_url)
        _ = parsed_course_url.port
    except ValueError:
        return None, "Liên kết khóa học không hợp lệ."
    if parsed_course_url.scheme not in {"http", "https"} or not parsed_course_url.hostname:
        return None, "Liên kết khóa học phải bắt đầu bằng http:// hoặc https://."
    if image_url:
        is_local_image = image_url.startswith("images/") and ".." not in Path(image_url).parts
        is_uploaded_image = re.fullmatch(r"/uploads/[a-f0-9]{32}\.(?:png|jpg|gif|webp)", image_url) is not None
        try:
            parsed_image_url = urlsplit(image_url)
            _ = parsed_image_url.port
            is_external_image = (
                parsed_image_url.scheme in {"http", "https"}
                and bool(parsed_image_url.hostname)
            )
        except ValueError:
            is_external_image = False
        if not (is_local_image or is_uploaded_image or is_external_image):
            return None, "Ảnh cần là đường dẫn images/ hoặc URL http(s)."
    return {
        "title": title,
        "description": description,
        "details": details,
        "image_url": image_url,
        "course_url": course_url,
    }, None


def find_user_by_email(email):
    return get_database().execute(
        "SELECT * FROM users WHERE email = ? COLLATE NOCASE", (email,)
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


def count_admin_accounts():
    return get_database().execute(
        "SELECT COUNT(*) FROM users WHERE role = 'admin'"
    ).fetchone()[0]


def get_account_data(user_id):
    database = get_database()
    account = database.execute(
        "SELECT id, name, email, role, created_at FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    attempts = database.execute(
        "SELECT exam_title, subject, correct_count, total_questions, score, "
        "duration_seconds, created_at FROM quiz_attempts "
        "WHERE user_id = ? ORDER BY created_at DESC, id DESC",
        (user_id,),
    ).fetchall()
    return {"account": dict(account), "quiz_attempts": [dict(row) for row in attempts]}


def _archive_quiz_attempts(database, where_clause, parameters):
    grouped_attempts = database.execute(
        "SELECT strftime('%Y-%m', created_at) AS period_month, exam_id, exam_title, "
        "subject, COUNT(*) AS attempts, SUM(score) AS score_total, "
        "SUM(correct_count) AS correct_count, SUM(total_questions) AS total_questions, "
        "MAX(score) AS best_score FROM quiz_attempts WHERE "
        + where_clause
        + " GROUP BY period_month, exam_id, exam_title, subject",
        parameters,
    ).fetchall()
    for row in grouped_attempts:
        database.execute(
            "INSERT INTO quiz_monthly_aggregates "
            "(period_month, exam_id, exam_title, subject, attempts, score_total, "
            "correct_count, total_questions, best_score) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(period_month, exam_id, exam_title, subject) DO UPDATE SET "
            "attempts = attempts + excluded.attempts, "
            "score_total = score_total + excluded.score_total, "
            "correct_count = correct_count + excluded.correct_count, "
            "total_questions = total_questions + excluded.total_questions, "
            "best_score = MAX(best_score, excluded.best_score)",
            tuple(row),
        )
    return database.execute(
        "DELETE FROM quiz_attempts WHERE " + where_clause, parameters
    ).rowcount


def archive_expired_quiz_attempts(cutoff):
    database = get_database()
    deleted = _archive_quiz_attempts(database, "created_at < ?", (cutoff,))
    database.commit()
    return deleted


def delete_user_and_archive_attempts(user_id):
    database = get_database()
    archived_attempts = _archive_quiz_attempts(database, "user_id = ?", (user_id,))
    database.execute("DELETE FROM users WHERE id = ?", (user_id,))
    database.commit()
    return archived_attempts


def create_quiz_attempt(data, user_id=None):
    score = round(data["correct_count"] / data["total_questions"] * 100)
    cursor = get_database().execute(
        "INSERT INTO quiz_attempts "
        "(user_id, exam_id, exam_title, subject, correct_count, total_questions, score, duration_seconds) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            user_id,
            data["exam_id"],
            data["exam_title"],
            data["subject"],
            data["correct_count"],
            data["total_questions"],
            score,
            data["duration_seconds"],
        ),
    )
    get_database().commit()
    return cursor.lastrowid


def get_quiz_statistics():
    database = get_database()
    live_summary = database.execute(
        "SELECT COUNT(*) AS attempts, COALESCE(SUM(score), 0) AS score_total, "
        "COUNT(DISTINCT user_id) AS learners, "
        "COALESCE(SUM(correct_count), 0) AS correct_count, "
        "COALESCE(SUM(total_questions), 0) AS total_questions "
        "FROM quiz_attempts"
    ).fetchone()
    archived_summary = database.execute(
        "SELECT COALESCE(SUM(attempts), 0) AS attempts, "
        "COALESCE(SUM(score_total), 0) AS score_total, "
        "COALESCE(SUM(correct_count), 0) AS correct_count, "
        "COALESCE(SUM(total_questions), 0) AS total_questions "
        "FROM quiz_monthly_aggregates"
    ).fetchone()
    attempt_count = live_summary["attempts"] + archived_summary["attempts"]
    score_total = live_summary["score_total"] + archived_summary["score_total"]
    summary = {
        "attempts": attempt_count,
        "average_score": int(score_total / attempt_count + 0.5) if attempt_count else 0,
        "learners": live_summary["learners"],
        "correct_count": live_summary["correct_count"] + archived_summary["correct_count"],
        "total_questions": live_summary["total_questions"] + archived_summary["total_questions"],
    }

    exam_rows = database.execute(
        "SELECT exam_id, exam_title, subject, COUNT(*) AS attempts, "
        "SUM(score) AS score_total, MAX(score) AS best_score "
        "FROM quiz_attempts GROUP BY exam_id, exam_title, subject "
        "UNION ALL "
        "SELECT exam_id, exam_title, subject, SUM(attempts) AS attempts, "
        "SUM(score_total) AS score_total, MAX(best_score) AS best_score "
        "FROM quiz_monthly_aggregates GROUP BY exam_id, exam_title, subject"
    ).fetchall()
    exams_by_key = {}
    for row in exam_rows:
        key = (row["exam_id"], row["exam_title"], row["subject"])
        exam = exams_by_key.setdefault(key, {
            "exam_id": row["exam_id"],
            "exam_title": row["exam_title"],
            "subject": row["subject"],
            "attempts": 0,
            "score_total": 0,
            "best_score": 0,
        })
        exam["attempts"] += row["attempts"]
        exam["score_total"] += row["score_total"]
        exam["best_score"] = max(exam["best_score"], row["best_score"])
    exams = [
        {
            "exam_id": exam["exam_id"],
            "exam_title": exam["exam_title"],
            "subject": exam["subject"],
            "attempts": exam["attempts"],
            "average_score": int(exam["score_total"] / exam["attempts"] + 0.5),
            "best_score": exam["best_score"],
        }
        for exam in exams_by_key.values()
    ]
    exams.sort(key=lambda exam: (-exam["attempts"], exam["exam_title"].casefold()))
    recent = database.execute(
        "SELECT quiz_attempts.exam_title, quiz_attempts.subject, "
        "quiz_attempts.correct_count, quiz_attempts.total_questions, quiz_attempts.score, "
        "quiz_attempts.created_at, "
        "CASE WHEN quiz_attempts.user_id IS NULL THEN 'Khách' ELSE 'Học viên' END AS learner "
        "FROM quiz_attempts "
        "ORDER BY quiz_attempts.id DESC LIMIT 20"
    ).fetchall()
    return {
        "summary": summary,
        "exams": exams,
        "recent": [dict(attempt) for attempt in recent],
    }


def list_courses():
    return get_database().execute("SELECT * FROM courses ORDER BY id ASC").fetchall()


def get_course_by_id(course_id):
    return get_database().execute("SELECT * FROM courses WHERE id = ?", (course_id,)).fetchone()


def create_course(data):
    cursor = get_database().execute(
        "INSERT INTO courses (title, description, image_url, course_url, details) VALUES (?, ?, ?, ?, ?)",
        (data["title"], data["description"], data["image_url"], data["course_url"], data["details"]),
    )
    get_database().commit()
    return cursor.lastrowid


def update_course(course_id, data):
    cursor = get_database().execute(
        "UPDATE courses SET title = ?, description = ?, image_url = ?, course_url = ?, details = ? WHERE id = ?",
        (data["title"], data["description"], data["image_url"], data["course_url"], data["details"], course_id),
    )
    if cursor.rowcount:
        get_database().commit()
    return cursor.rowcount > 0


def delete_course(course_id):
    cursor = get_database().execute("DELETE FROM courses WHERE id = ?", (course_id,))
    if cursor.rowcount:
        get_database().commit()
    return cursor.rowcount > 0


def validate_book(data):
    title = str(data.get("title", "")).strip()
    author = str(data.get("author", "")).strip()
    cover_image = str(data.get("cover_image", "")).strip()
    category = str(data.get("category", "")).strip()
    description = str(data.get("description", "")).strip()
    details = str(data.get("details", "")).strip()
    document_url = str(data.get("document_url", "")).strip()

    if not title or len(title) > 200:
        return None, "Tên sách cần có từ 1 đến 200 ký tự."
    if not author or len(author) > 120:
        return None, "Tên tác giả cần có từ 1 đến 120 ký tự."
    if not category or len(category) > 80:
        return None, "Danh mục cần có từ 1 đến 80 ký tự."
    if len(description) > 2000:
        return None, "Mô tả không được vượt quá 2000 ký tự."
    if len(details) > 5000:
        return None, "Nội dung chi tiết không được vượt quá 5000 ký tự."
    try:
        parsed_document_url = urlsplit(document_url)
        parsed_document_url.port
    except ValueError:
        return None, "Liên kết tài liệu không hợp lệ."
    if parsed_document_url.scheme not in {"http", "https"} or not parsed_document_url.hostname:
        return None, "Liên kết tài liệu phải bắt đầu bằng http:// hoặc https://."
    if cover_image and not re.fullmatch(r"/static/uploads/books/[a-f0-9]{32}\.(?:png|jpg|gif|webp)", cover_image):
        return None, "Ảnh bìa không hợp lệ."

    return {
        "title": title,
        "author": author,
        "cover_image": cover_image,
        "category": category,
        "description": description,
        "details": details,
        "document_url": document_url,
    }, None


def list_books():
    return get_database().execute("SELECT * FROM books ORDER BY created_at DESC, id DESC").fetchall()


def count_books():
    return get_database().execute("SELECT COUNT(*) FROM books").fetchone()[0]


def get_book_by_id(book_id):
    return get_database().execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()


def create_book(data):
    cursor = get_database().execute(
        "INSERT INTO books (title, author, cover_image, category, description, details, document_url) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            data["title"],
            data["author"],
            data["cover_image"],
            data["category"],
            data["description"],
            data.get("details", ""),
            data["document_url"],
        ),
    )
    get_database().commit()
    return cursor.lastrowid


def update_book(book_id, data):
    cursor = get_database().execute(
        "UPDATE books SET title = ?, author = ?, cover_image = ?, category = ?, "
        "description = ?, details = ?, document_url = ? WHERE id = ?",
        (
            data["title"],
            data["author"],
            data["cover_image"],
            data["category"],
            data["description"],
            data.get("details", ""),
            data["document_url"],
            book_id,
        ),
    )
    if cursor.rowcount:
        get_database().commit()
    return cursor.rowcount > 0


def delete_book(book_id):
    cursor = get_database().execute("DELETE FROM books WHERE id = ?", (book_id,))
    if cursor.rowcount:
        get_database().commit()
    return cursor.rowcount > 0
