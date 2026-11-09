from io import BytesIO
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from app import create_app, load_secret_key


class AuthenticationAndCourseApiTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        database_path = Path(self.temp_dir.name) / "test.sqlite3"
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test-only-secret",
            "DATABASE": str(database_path),
            "BOOTSTRAP_ADMIN_EMAIL": "root@example.com",
            "BOOTSTRAP_ADMIN_PASSWORD": "RootPassword123",
            "UPLOAD_FOLDER": str(Path(self.temp_dir.name) / "uploads"),
            "BOOK_UPLOAD_FOLDER": str(Path(self.temp_dir.name) / "books"),
            "AUTH_LOGIN_RATE_LIMIT": 50,
            "AUTH_REGISTER_RATE_LIMIT": 50,
        })
        with self.app.app_context():
            from models import get_database

            get_database().execute("DELETE FROM books")
            get_database().commit()
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def register_user(self, email="student@example.com"):
        return self.client.post("/api/auth/register", json={
            "name": "Student",
            "email": email,
            "password": "StudentPassword123",
            "role": "admin",
        })

    def login_admin(self):
        return self.client.post("/api/auth/login", json={
            "email": "root@example.com",
            "password": "RootPassword123",
        })

    def test_public_registration_always_creates_user(self):
        response = self.register_user()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json["role"], "user")
        with self.client.session_transaction() as user_session:
            self.assertTrue(user_session.permanent)
            user_id = user_session["user_id"]
        self.assertEqual(response.json["id"], user_id)

        duplicate = self.client.post("/api/auth/register", json={
            "name": "Another Student",
            "email": "STUDENT@example.com",
            "password": "StudentPassword123",
        })
        self.assertEqual(duplicate.status_code, 409)

    def test_registration_rejects_invalid_input_and_accepts_field_boundaries(self):
        invalid_payloads = (
            {},
            {"email": "valid@example.com", "password": "Password123"},
            {"name": "Valid", "password": "Password123"},
            {"name": "Valid", "email": "valid@example.com"},
            {"name": "", "email": "valid@example.com", "password": "Password123"},
            {"name": "x" * 81, "email": "valid@example.com", "password": "Password123"},
            {"name": "Valid", "email": "not-an-email", "password": "Password123"},
            {"name": "Valid", "email": "x" * 250 + "@a.co", "password": "Password123"},
            {"name": "Valid", "email": "valid@example.com", "password": "short"},
            {"name": ["not", "text"], "email": "valid@example.com", "password": "Password123"},
            {"name": "Valid", "email": None, "password": "Password123"},
            {"name": "Valid", "email": 5, "password": "Password123"},
            {"name": "Valid", "email": "valid@example.com", "password": None},
            {"name": "Valid", "email": "valid@example.com", "password": {"value": "Password123"}},
        )
        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                response = self.client.post("/api/auth/register", json=payload)
                self.assertEqual(response.status_code, 400)
                self.assertIsInstance(response.json.get("error"), str)
                self.assertEqual(self.client.get("/api/auth/me").status_code, 401)

        self.login_admin()
        self.assertEqual(len(self.client.get("/api/admin/users").json), 1)

        accepted = self.client.post("/api/auth/register", json={
            "name": "x" * 80,
            "email": "x" * 249 + "@a.co",
            "password": "12345678",
        })
        self.assertEqual(accepted.status_code, 201)
        self.assertEqual(len(accepted.json["name"]), 80)
        self.assertEqual(len(accepted.json["email"]), 254)
        self.assertEqual(accepted.json["role"], "user")

    def test_login_rejects_missing_malformed_and_wrong_type_input(self):
        invalid_requests = (
            {"json": {}},
            {"json": {"email": "root@example.com"}},
            {"json": {"password": "RootPassword123"}},
            {"json": {"email": None, "password": "RootPassword123"}},
            {"json": {"email": "root@example.com", "password": ["not", "text"]}},
            {"json": {"email": "not-an-email", "password": "RootPassword123"}},
            {"json": {"email": "", "password": "RootPassword123"}},
            {"json": {"email": "root@example.com", "password": ""}},
            {"json": {"email": "x" * 250 + "@example.com", "password": "RootPassword123"}},
            {"data": "{broken", "content_type": "application/json"},
        )
        for request_args in invalid_requests:
            with self.subTest(request_args=request_args):
                response = self.client.post("/api/auth/login", **request_args)
                self.assertEqual(response.status_code, 400)
                self.assertIsInstance(response.json.get("error"), str)
                self.assertEqual(self.client.get("/api/auth/me").status_code, 401)

        wrong_password = self.client.post("/api/auth/login", json={
            "email": "root@example.com",
            "password": "WrongPassword123",
        })
        self.assertEqual(wrong_password.status_code, 401)
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)

    def test_admin_creation_rejects_invalid_input_without_creating_accounts(self):
        self.login_admin()
        baseline = self.client.get("/api/admin/users").json
        invalid_payloads = (
            {},
            {"email": "new@example.com", "password": "Password123"},
            {"name": "Valid", "password": "Password123"},
            {"name": "Valid", "email": "new@example.com"},
            {"name": "", "email": "new@example.com", "password": "Password123"},
            {"name": "x" * 81, "email": "new@example.com", "password": "Password123"},
            {"name": "Valid", "email": "not-an-email", "password": "Password123"},
            {"name": "Valid", "email": "new@example.com", "password": "short"},
            {"name": ["not", "text"], "email": "new@example.com", "password": "Password123"},
            {"name": "Valid", "email": None, "password": "Password123"},
            {"name": "Valid", "email": "new@example.com", "password": None},
        )
        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                response = self.client.post("/api/admin/users", json=payload)
                self.assertEqual(response.status_code, 400)
                self.assertIsInstance(response.json.get("error"), str)
                self.assertEqual(self.client.get("/api/admin/users").json, baseline)

    def test_login_restores_account_name_from_permanent_session(self):
        self.register_user()
        self.client.post("/api/auth/logout")

        response = self.client.post("/api/auth/login", json={
            "email": "student@example.com",
            "password": "StudentPassword123",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["name"], "Student")
        with self.client.session_transaction() as user_session:
            self.assertTrue(user_session.permanent)
            self.assertEqual(user_session["user_id"], response.json["id"])

        current_account = self.client.get("/api/auth/me")
        self.assertEqual(current_account.status_code, 200)
        self.assertEqual(current_account.json["name"], "Student")

    def test_default_session_signing_key_is_stable(self):
        with patch.dict(os.environ, {"SECRET_KEY": ""}):
            first_key = load_secret_key(self.temp_dir.name)
            second_key = load_secret_key(self.temp_dir.name)
        self.assertEqual(first_key, second_key)
        self.assertEqual(len(first_key), 64)

    def test_course_changes_require_admin_role(self):
        self.assertEqual(self.client.post("/api/courses", json={}).status_code, 401)
        self.register_user()
        self.assertEqual(self.client.post("/api/courses", json={}).status_code, 403)
        self.assertEqual(self.client.post("/api/admin/users", json={}).status_code, 403)

    def test_admin_can_create_edit_and_delete_courses(self):
        self.login_admin()
        created = self.client.post("/api/courses", json={
            "title": "Python",
            "description": "Python cơ bản",
            "details": "Nền tảng Python\nThực hành dự án",
            "image_url": "images/picture/card-1.png",
            "course_url": "https://example.com/python",
        })
        self.assertEqual(created.status_code, 201)
        course_id = created.json["id"]

        updated = self.client.put(f"/api/courses/{course_id}", json={
            "title": "Python nâng cao",
            "description": "Nội dung đã sửa",
            "details": "Nội dung chi tiết đã cập nhật",
            "image_url": "",
            "course_url": "https://example.com/advanced-python",
        })
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json["title"], "Python nâng cao")
        self.assertEqual(updated.json["details"], "Nội dung chi tiết đã cập nhật")
        detail_page = self.client.get(f"/courses/{course_id}")
        self.assertEqual(detail_page.status_code, 200)
        self.assertIn("Nội dung chi tiết đã cập nhật", detail_page.get_data(as_text=True))
        self.assertEqual(self.client.put("/api/courses/99999", json=updated.json).status_code, 404)
        self.assertEqual(self.client.delete(f"/api/courses/{course_id}").status_code, 200)
        self.assertEqual(self.client.delete(f"/api/courses/{course_id}").status_code, 404)
        self.assertEqual(self.client.get(f"/courses/{course_id}").status_code, 404)

    def test_admin_accounts_can_only_be_created_inside_admin_session(self):
        unauthorized = self.client.post("/api/admin/users", json={
            "name": "Second Admin",
            "email": "second@example.com",
            "password": "SecondPassword123",
        })
        self.assertEqual(unauthorized.status_code, 401)

        self.login_admin()
        created = self.client.post("/api/admin/users", json={
            "name": "Second Admin",
            "email": "second@example.com",
            "password": "SecondPassword123",
        })
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.json["role"], "admin")
        self.assertNotIn("password_hash", created.json)

    def test_quiz_attempts_are_saved_and_summarized_for_admin(self):
        attempt = {
            "examId": "javascript-basics",
            "title": "JavaScript căn bản",
            "subject": "JavaScript",
            "correct": 4,
            "total": 5,
            "duration": 95,
            "score": 100,
        }
        self.assertEqual(self.client.get("/api/admin/quiz/statistics").status_code, 401)
        saved = self.client.post("/api/quiz/attempts", json=attempt)
        self.assertEqual(saved.status_code, 201)
        self.login_admin()
        report = self.client.get("/api/admin/quiz/statistics")
        self.assertEqual(report.status_code, 200)
        self.assertEqual(report.json["summary"]["attempts"], 1)
        self.assertEqual(report.json["summary"]["average_score"], 80)
        self.assertEqual(report.json["summary"]["learners"], 0)
        self.assertEqual(report.json["exams"][0]["exam_title"], "JavaScript căn bản")
        self.assertEqual(report.json["recent"][0]["learner"], "Khách")
        self.assertEqual(report.json["recent"][0]["score"], 80)

    def test_account_data_export_contains_only_the_authenticated_users_data(self):
        self.assertEqual(self.register_user().status_code, 201)
        self.client.post("/api/quiz/attempts", json={
            "examId": "javascript-basics",
            "title": "JavaScript căn bản",
            "subject": "JavaScript",
            "correct": 4,
            "total": 5,
            "duration": 95,
        })
        other_client = self.app.test_client()
        other_client.post("/api/auth/register", json={
            "name": "Other Student",
            "email": "other@example.com",
            "password": "OtherPassword123",
        })
        other_client.post("/api/quiz/attempts", json={
            "examId": "html-foundations",
            "title": "Nền tảng HTML & CSS",
            "subject": "HTML & CSS",
            "correct": 5,
            "total": 5,
            "duration": 60,
        })

        response = self.client.get("/api/auth/me/data")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["account"]["email"], "student@example.com")
        self.assertNotIn("password", response.json["account"])
        self.assertNotIn("password_hash", response.json["account"])
        self.assertEqual(len(response.json["quiz_attempts"]), 1)
        self.assertEqual(
            set(response.json["quiz_attempts"][0]),
            {
                "exam_title", "subject", "correct_count", "total_questions",
                "score", "duration_seconds", "created_at",
            },
        )

    def test_quiz_report_excludes_learner_identity_and_unused_attempt_fields(self):
        self.assertEqual(self.register_user().status_code, 201)
        self.client.post("/api/quiz/attempts", json={
            "examId": "javascript-basics",
            "title": "JavaScript căn bản",
            "subject": "JavaScript",
            "correct": 4,
            "total": 5,
            "duration": 95,
        })
        self.login_admin()

        report = self.client.get("/api/admin/quiz/statistics")

        self.assertEqual(report.status_code, 200)
        recent = report.json["recent"][0]
        self.assertEqual(recent["learner"], "Học viên")
        self.assertNotIn("Student", str(report.json))
        self.assertNotIn("student@example.com", str(report.json))
        self.assertNotIn("duration_seconds", recent)
        self.assertNotIn("id", recent)

    def test_account_deletion_archives_quiz_results_and_clears_session(self):
        self.assertEqual(self.register_user().status_code, 201)
        self.client.post("/api/quiz/attempts", json={
            "examId": "javascript-basics",
            "title": "JavaScript căn bản",
            "subject": "JavaScript",
            "correct": 4,
            "total": 5,
            "duration": 95,
        })

        deleted = self.client.delete("/api/auth/me")

        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(deleted.json["archived_attempts"], 1)
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)
        self.login_admin()
        report = self.client.get("/api/admin/quiz/statistics")
        self.assertEqual(report.json["summary"]["attempts"], 1)
        self.assertEqual(report.json["summary"]["average_score"], 80)
        self.assertEqual(report.json["summary"]["correct_count"], 4)
        self.assertEqual(report.json["summary"]["total_questions"], 5)
        self.assertEqual(report.json["exams"][0]["attempts"], 1)
        self.assertEqual(report.json["exams"][0]["average_score"], 80)
        self.assertEqual(report.json["exams"][0]["best_score"], 80)
        self.assertEqual(report.json["recent"], [])
        with self.app.app_context():
            from models import get_database

            database = get_database()
            self.assertIsNone(database.execute(
                "SELECT id FROM users WHERE email = ?",
                ("student@example.com",),
            ).fetchone())
            self.assertEqual(
                database.execute("SELECT COUNT(*) FROM quiz_attempts").fetchone()[0],
                0,
            )
            self.assertEqual(
                database.execute(
                    "SELECT COUNT(*) FROM quiz_monthly_aggregates"
                ).fetchone()[0],
                1,
            )
            aggregate_columns = {
                row["name"] for row in database.execute(
                    "PRAGMA table_info(quiz_monthly_aggregates)"
                )
            }
            self.assertNotIn("user_id", aggregate_columns)
            self.assertNotIn("created_at", aggregate_columns)
            self.assertNotIn("duration_seconds", aggregate_columns)

    def test_expired_quiz_attempts_are_archived_by_the_retention_command(self):
        self.client.post("/api/quiz/attempts", json={
            "examId": "javascript-basics",
            "title": "JavaScript căn bản",
            "subject": "JavaScript",
            "correct": 4,
            "total": 5,
            "duration": 95,
        })
        with self.app.app_context():
            from models import get_database

            get_database().execute(
                "UPDATE quiz_attempts SET created_at = ?",
                ("2000-01-02 12:34:56",),
            )
            get_database().commit()

        result = self.app.test_cli_runner().invoke(
            args=["archive-expired-quiz-attempts"]
        )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("1", result.output)
        with self.app.app_context():
            from models import get_database

            database = get_database()
            self.assertEqual(
                database.execute("SELECT COUNT(*) FROM quiz_attempts").fetchone()[0],
                0,
            )
            self.assertEqual(
                database.execute(
                    "SELECT attempts FROM quiz_monthly_aggregates"
                ).fetchone()["attempts"],
                1,
            )

    def test_account_deletion_protects_the_last_or_bootstrap_admin(self):
        self.login_admin()

        response = self.client.delete("/api/auth/me")

        self.assertEqual(response.status_code, 409)
        self.assertEqual(self.client.get("/api/auth/me").status_code, 200)

    def test_privacy_notices_appear_when_account_or_quiz_data_is_collected(self):
        registration_page = self.client.get("/auth.html?view=register")
        quiz_page = self.client.get("/quiz.html")

        self.assertEqual(registration_page.status_code, 200)
        self.assertIn("xóa tài khoản", registration_page.get_data(as_text=True).lower())
        self.assertEqual(quiz_page.status_code, 200)
        self.assertIn("365 ngày", quiz_page.get_data(as_text=True))
        self.assertIn("lượt khách", quiz_page.get_data(as_text=True).lower())

    def test_quiz_attempt_validation_and_admin_access(self):
        invalid = self.client.post("/api/quiz/attempts", json={
            "examId": "quiz",
            "title": "Quiz",
            "subject": "Lập trình",
            "correct": 8,
            "total": 5,
            "duration": 60,
        })
        self.assertEqual(invalid.status_code, 400)
        self.register_user()
        self.assertEqual(self.client.get("/api/admin/quiz/statistics").status_code, 403)

    def test_default_admin_account_is_created_with_a_hashed_password(self):
        with tempfile.TemporaryDirectory() as temp_dir, patch.dict(os.environ, {
            "ADMIN_EMAIL": "admin@eschool.com",
            "ADMIN_PASSWORD": "admin123",
        }):
            app = create_app({
                "TESTING": True,
                "SECRET_KEY": "test-only-secret",
                "DATABASE": str(Path(temp_dir) / "default-admin.sqlite3"),
                "BOOK_UPLOAD_FOLDER": str(Path(temp_dir) / "books"),
            })
            client = app.test_client()
            self.assertEqual(app.config["APP_ENV"], "development")
            self.assertFalse(app.config["SESSION_COOKIE_SECURE"])
            response = client.post("/login", data={
                "email": "admin@eschool.com",
                "password": "admin123",
            })
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.headers["Location"], "/admin/books")
            with app.app_context():
                from models import find_user_by_email
                from werkzeug.security import check_password_hash

                admin = find_user_by_email("admin@eschool.com")
                self.assertEqual(admin["role"], "admin")
                self.assertNotEqual(admin["password_hash"], "admin123")
                self.assertTrue(check_password_hash(admin["password_hash"], "admin123"))

    def test_production_requires_secret_from_environment(self):
        with patch.dict(os.environ, {"APP_ENV": "production", "SECRET_KEY": ""}):
            with self.assertRaisesRegex(RuntimeError, "SECRET_KEY must be set"):
                create_app({
                    "TESTING": True,
                    "SECRET_KEY": "test-only-secret",
                })

    def test_production_requires_admin_credentials_and_rejects_default_password(self):
        with tempfile.TemporaryDirectory() as temp_dir, patch.dict(os.environ, {
            "APP_ENV": "production",
            "SECRET_KEY": "production-only-secret",
            "ADMIN_EMAIL": "",
            "ADMIN_PASSWORD": "",
        }):
            with self.assertRaisesRegex(RuntimeError, "Set ADMIN_EMAIL and ADMIN_PASSWORD"):
                create_app({
                    "TESTING": True,
                    "DATABASE": str(Path(temp_dir) / "missing-admin.sqlite3"),
                    "BOOK_UPLOAD_FOLDER": str(Path(temp_dir) / "missing-admin-books"),
                })

        with tempfile.TemporaryDirectory() as temp_dir, patch.dict(os.environ, {
            "APP_ENV": "production",
            "SECRET_KEY": "production-only-secret",
            "ADMIN_EMAIL": "admin@example.com",
            "ADMIN_PASSWORD": "admin123",
        }):
            with self.assertRaisesRegex(RuntimeError, "must not use the insecure default"):
                create_app({
                    "TESTING": True,
                    "DATABASE": str(Path(temp_dir) / "weak-admin.sqlite3"),
                    "BOOK_UPLOAD_FOLDER": str(Path(temp_dir) / "weak-admin-books"),
                })

        with tempfile.TemporaryDirectory() as temp_dir, patch.dict(os.environ, {
            "APP_ENV": "production",
            "SECRET_KEY": "production-only-secret",
            "ADMIN_EMAIL": "admin@example.com",
            "ADMIN_PASSWORD": "short",
        }):
            with self.assertRaisesRegex(RuntimeError, "at least 12 characters"):
                create_app({
                    "TESTING": True,
                    "DATABASE": str(Path(temp_dir) / "short-admin.sqlite3"),
                    "BOOK_UPLOAD_FOLDER": str(Path(temp_dir) / "short-admin-books"),
                })

    def test_production_uses_secure_session_cookie_with_explicit_secrets(self):
        with tempfile.TemporaryDirectory() as temp_dir, patch.dict(os.environ, {
            "APP_ENV": "production",
            "SECRET_KEY": "production-only-secret",
            "ADMIN_EMAIL": "admin@example.com",
            "ADMIN_PASSWORD": "A-unique-production-password",
        }):
            app = create_app({
                "TESTING": True,
                "DATABASE": str(Path(temp_dir) / "production.sqlite3"),
                "BOOK_UPLOAD_FOLDER": str(Path(temp_dir) / "production-books"),
            })
            response = app.test_client().post("/login", data={
                "email": "admin@example.com",
                "password": "A-unique-production-password",
            })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(app.config["SESSION_COOKIE_SECURE"])
        self.assertTrue(app.config["SESSION_COOKIE_HTTPONLY"])
        self.assertEqual(app.config["SESSION_COOKIE_SAMESITE"], "Lax")
        set_cookie = response.headers["Set-Cookie"]
        self.assertIn("Secure", set_cookie)
        self.assertIn("HttpOnly", set_cookie)
        self.assertIn("SameSite=Lax", set_cookie)

    def test_default_books_are_seeded_once_and_only_when_database_is_empty(self):
        database_path = Path(self.temp_dir.name) / "seeded.sqlite3"
        app_config = {
            "TESTING": True,
            "SECRET_KEY": "test-only-secret",
            "DATABASE": str(database_path),
            "BOOTSTRAP_ADMIN_EMAIL": "",
            "BOOTSTRAP_ADMIN_PASSWORD": "",
            "BOOK_UPLOAD_FOLDER": str(Path(self.temp_dir.name) / "seeded-books"),
        }
        app = create_app(app_config)
        with app.app_context():
            from models import list_books

            seeded_books = list_books()
            self.assertEqual(len(seeded_books), 6)
            self.assertEqual(
                {book["title"] for book in seeded_books},
                {
                    "Clean Code: A Handbook of Agile Software Craftsmanship",
                    "The C++ Programming Language (4th Edition)",
                    "Python Crash Course: A Hands-On, Project-Based Introduction to Programming",
                    "Effective Java (3rd Edition)",
                    "Eloquent JavaScript: A Modern Introduction to Programming",
                    "Head First Design Patterns",
                },
            )
            self.assertTrue(all(book["cover_image"].startswith("https://images.unsplash.com/") for book in seeded_books))

        restarted_app = create_app(app_config)
        with restarted_app.app_context():
            from models import get_database, list_books

            books = list_books()
            self.assertEqual(len(books), 6)
            get_database().execute("DELETE FROM books WHERE id != ?", (books[0]["id"],))
            get_database().commit()

        app_with_existing_book = create_app(app_config)
        with app_with_existing_book.app_context():
            from models import list_books

            self.assertEqual(len(list_books()), 1)

    def test_book_management_pages_are_admin_only(self):
        self.assertEqual(self.client.get("/login").status_code, 200)
        response = self.client.get("/admin/books")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/login")

        self.register_user()
        forbidden = self.client.get("/admin/books")
        self.assertEqual(forbidden.status_code, 403)

    def test_admin_dashboard_links_and_book_count(self):
        dashboard = self.client.get("/admin.html")
        self.assertIn(b'href="/admin/books"', dashboard.data)
        self.assertIn(b"Qu\xe1\xba\xa3n l\xc3\xbd s\xc3\xa1ch", dashboard.data)
        self.assertIn(b'id="book-count"', dashboard.data)
        self.assertEqual(self.client.get("/api/admin/books/count").status_code, 401)

        self.register_user()
        self.assertEqual(self.client.get("/api/admin/books/count").status_code, 403)

        self.login_admin()
        with self.app.app_context():
            from models import create_book

            create_book({
                "title": "Sách kiểm thử",
                "author": "Tác giả",
                "cover_image": "",
                "category": "Lập trình",
                "description": "",
                "document_url": "https://example.com/book.pdf",
            })
        count = self.client.get("/api/admin/books/count")
        self.assertEqual(count.status_code, 200)
        self.assertEqual(count.json, {"count": 1})

    def test_public_book_catalog_tracks_admin_create_edit_and_delete(self):
        self.login_admin()
        png = BytesIO()
        Image.new("RGB", (4, 4), "green").save(png, format="PNG")
        created = self.client.post("/admin/books/add", data={
            "title": "Sách công khai",
            "author": "Tác giả mẫu",
            "category": "Python",
            "description": "Mô tả cuốn sách hiển thị trên trang chủ.",
            "details": "Nội dung chi tiết sách.\nCác chủ đề chính.",
            "document_url": "https://example.com/public-book.pdf",
            "cover_image": (BytesIO(png.getvalue()), "cover.png"),
        }, content_type="multipart/form-data")
        self.assertEqual(created.status_code, 302)
        with self.app.app_context():
            from models import list_books

            book_id = list_books()[0]["id"]

        for path in ("/", "/index.html"):
            with self.subTest(path=path):
                catalog = self.client.get(path).get_data(as_text=True)
                self.assertIn('id="book-grid"', catalog)
                self.assertIn('data-title="Sách công khai"', catalog)
                self.assertIn("Tác giả mẫu", catalog)
                self.assertIn("Mô tả cuốn sách hiển thị trên trang chủ.", catalog)
                self.assertIn(f'href="/books/{book_id}"', catalog)
                self.assertIn("/static/uploads/books/", catalog)
            detail_page = self.client.get(f"/books/{book_id}")
            self.assertEqual(detail_page.status_code, 200)
            self.assertIn("Nội dung chi tiết sách.", detail_page.get_data(as_text=True))
            self.assertIn("https://example.com/public-book.pdf", detail_page.get_data(as_text=True))
        updated = self.client.post(f"/admin/books/edit/{book_id}", data={
            "title": "Sách đã cập nhật",
            "author": "Tác giả mới",
            "category": "Java",
            "description": "Mô tả mới.",
            "details": "Nội dung sách đã sửa.",
            "document_url": "https://example.com/updated-book.pdf",
        })
        self.assertEqual(updated.status_code, 302)
        public_after_update = self.client.get("/").get_data(as_text=True)
        self.assertIn('data-title="Sách đã cập nhật"', public_after_update)
        self.assertNotIn('data-title="Sách công khai"', public_after_update)
        self.assertIn("Tác giả mới", public_after_update)
        self.assertIn("Nội dung sách đã sửa.", self.client.get(f"/books/{book_id}").get_data(as_text=True))

        deleted = self.client.post(f"/admin/books/delete/{book_id}")
        self.assertEqual(deleted.status_code, 302)
        public_after_delete = self.client.get("/index.html").get_data(as_text=True)
        self.assertNotIn("Sách đã cập nhật", public_after_delete)
        self.assertIn("Chưa có cuốn sách nào trong thư viện.", public_after_delete)
        self.assertEqual(self.client.get(f"/books/{book_id}").status_code, 404)

    def test_admin_navigation_and_add_book_route_are_consistent(self):
        self.login_admin()
        for path in (
            "/admin.html",
            "/admin-courses.html",
            "/admin-course-form.html",
            "/admin-course-delete.html",
            "/admin-accounts.html",
            "/quiz-admin.html",
            "/admin/books",
            "/admin/books/add",
        ):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                page = response.get_data(as_text=True)
                self.assertRegex(page, r'<a\b[^>]*href="/admin/books"[^>]*class="[^"]*\bnav-item\b[^"]*"')
                for target in ("/admin.html", "/admin-courses.html", "/admin/books", "/admin-accounts.html"):
                    self.assertIn(f'href="{target}"', page)
                self.assertIn("fa-solid fa-book", page)
                self.assertIn("Quản lý sách", page)

        listing = self.client.get("/admin/books")
        self.assertIn(b'href="/admin/books/add"', listing.data)
        add_form = self.client.get("/admin/books/add")
        self.assertEqual(add_form.status_code, 200)
        self.assertIn(b"Th\xc3\xaam s\xc3\xa1ch m\xe1\xbb\x9bi", add_form.data)

    def test_book_pages_use_eduhub_layout_and_form_validation(self):
        self.login_admin()
        listing = self.client.get("/admin/books")
        listing_html = listing.get_data(as_text=True)
        self.assertIn('data-protected-role="admin"', listing_html)
        self.assertIn('id="admin-sidebar"', listing_html)
        self.assertIn("sidebar-link-active", listing_html)
        self.assertIn("EDUHUB", listing_html)
        self.assertIn('href="/assets/css/admin-dashboard.css"', listing_html)
        self.assertIn('src="/assets/js/auth.js"', listing_html)
        self.assertIn("DANH SÁCH SÁCH", listing_html)
        self.assertIn("Xem danh sách, thêm, cập nhật hoặc xóa tài liệu trong thư viện.", listing_html)
        self.assertIn('href="/admin/books/add"', listing_html)
        self.assertIn("add-course-button", listing_html)
        self.assertIn('class="user-table book-table"', listing_html)
        for heading in ("<th>ID</th>", "Ảnh bìa", "Tên sách", "Tác giả", "Danh mục", "Link tài liệu"):
            self.assertIn(heading, listing_html)

        form = self.client.get("/admin/books/add")
        form_html = form.get_data(as_text=True)
        self.assertIn('href="/admin/books" class="nav-item sidebar-link sidebar-link-active"', form_html)
        self.assertIn("Eduhub", form_html)
        self.assertIn("SÁCH", form_html)
        self.assertIn('href="/assets/css/admin-dashboard.css"', form_html)
        self.assertIn('src="/assets/js/auth.js"', form_html)
        self.assertIn("Thông tin sách", form_html)
        self.assertIn("Điền thông tin và lưu thay đổi vào thư viện.", form_html)
        self.assertIn('href="/admin/books">← Danh sách sách</a>', form_html)
        self.assertIn('method="post" enctype="multipart/form-data"', form_html)
        for field in ("title", "author", "category", "document_url", "cover_image", "description"):
            self.assertIn(f'name="{field}"', form_html)
        self.assertIn("Lập trình C++ từ cơ bản đến nâng cao", form_html)
        self.assertIn("Nguyễn Văn A", form_html)
        self.assertIn("option value=\"Python\"", form_html)
        self.assertIn("Làm mới", form_html)
        self.assertGreaterEqual(form_html.count("required"), 4)

        invalid = self.client.post("/admin/books/add", data={
            "title": "   ",
            "author": "Tác giả",
            "category": "Lập trình",
        })
        self.assertEqual(invalid.status_code, 400)
        self.assertIn("Tên sách cần có từ 1 đến 200 ký tự.", invalid.get_data(as_text=True))

    def test_admin_can_create_edit_and_delete_books_with_cover_upload(self):
        self.assertEqual(self.client.post("/login", data={
            "email": "root@example.com",
            "password": "RootPassword123",
        }).status_code, 302)
        self.assertEqual(self.client.get("/admin/books").status_code, 200)
        self.assertEqual(self.client.get("/admin/books/add").status_code, 200)

        png = BytesIO()
        Image.new("RGB", (4, 4), "green").save(png, format="PNG")
        png_data = png.getvalue()
        created = self.client.post("/admin/books/add", data={
            "title": "Python cơ bản",
            "author": "Nguyễn An",
            "category": "Python",
            "description": "Tài liệu học Python",
            "details": "Các chương về cú pháp và thực hành.",
            "document_url": "https://example.com/python.pdf",
            "cover_image": (BytesIO(png_data), "cover.png"),
        }, content_type="multipart/form-data", follow_redirects=True)
        self.assertEqual(created.status_code, 200)
        created_html = created.get_data(as_text=True)
        self.assertIn("Python cơ bản", created_html)
        self.assertIn("Nguyễn An", created_html)
        self.assertIn("Mở tài liệu", created_html)

        with self.app.app_context():
            from models import list_books

            book = list_books()[0]
            book_id = book["id"]
            cover_path = book["cover_image"]
        self.assertRegex(cover_path, r"^/static/uploads/books/[a-f0-9]{32}\.png$")
        self.assertEqual(self.client.get(f"/admin/books/edit/{book_id}").status_code, 200)
        served_cover = self.client.get(cover_path)
        self.assertEqual(served_cover.status_code, 200)
        self.assertTrue(served_cover.content_type.startswith("image/png"))
        served_cover.close()

        updated = self.client.post(f"/admin/books/edit/{book_id}", data={
            "title": "Python nâng cao",
            "author": "Nguyễn An",
            "category": "Python",
            "description": "Đã cập nhật",
            "details": "Đã cập nhật nội dung chi tiết.",
            "document_url": "https://example.com/python-advanced.pdf",
        }, follow_redirects=True)
        self.assertEqual(updated.status_code, 200)
        self.assertIn("Python nâng cao", updated.get_data(as_text=True))
        local_cover = Path(self.temp_dir.name) / "books" / Path(cover_path).name
        self.assertTrue(local_cover.exists())

        deleted = self.client.post(f"/admin/books/delete/{book_id}", follow_redirects=True)
        self.assertEqual(deleted.status_code, 200)
        self.assertIn("Thư viện chưa có sách", deleted.get_data(as_text=True))
        self.assertFalse(local_cover.exists())
        missing_edit = self.client.get("/admin/books/edit/99999")
        self.assertEqual(missing_edit.status_code, 404)

    def test_regression_issue_26_malformed_book_url_returns_validation_error(self):
        self.login_admin()
        with self.app.app_context():
            from models import list_books

            initial_books = len(list_books())

        for document_url in ("https://[invalid", "https://example.com:bad/file.pdf"):
            with self.subTest(document_url=document_url):
                response = self.client.post("/admin/books/add", data={
                    "title": "Regression test book",
                    "author": "Test author",
                    "category": "Testing",
                    "description": "",
                    "details": "",
                    "document_url": document_url,
                })

                self.assertEqual(response.status_code, 400)
                self.assertIn("Liên kết tài liệu", response.get_data(as_text=True))
                with self.app.app_context():
                    self.assertEqual(len(list_books()), initial_books)

    def test_book_cover_uploads_validate_image_content_for_add_and_edit(self):
        self.login_admin()
        jpeg = BytesIO()
        Image.new("RGB", (4, 4), "blue").save(jpeg, format="JPEG")
        jpeg_data = jpeg.getvalue()
        book_form = {
            "title": "Ảnh bìa an toàn",
            "author": "Nguyễn An",
            "category": "Python",
            "description": "Mô tả",
            "details": "Nội dung",
            "document_url": "https://example.com/book.pdf",
        }

        created = self.client.post("/admin/books/add", data={
            **book_form,
            "cover_image": (BytesIO(jpeg_data), "../../cover.png"),
        }, content_type="multipart/form-data")
        self.assertEqual(created.status_code, 302)

        with self.app.app_context():
            from models import list_books

            book = list_books()[0]
            book_id = book["id"]
            original_cover = book["cover_image"]
        self.assertRegex(original_cover, r"^/static/uploads/books/[a-f0-9]{32}\.jpg$")
        with self.client.get(original_cover) as response:
            self.assertEqual(response.status_code, 200)

        upload_folder = Path(self.temp_dir.name) / "books"
        original_files = set(upload_folder.iterdir())
        invalid_add = self.client.post("/admin/books/add", data={
            **book_form,
            "title": "Ảnh lỗi",
            "cover_image": (BytesIO(b"not an image"), "fake.png"),
        }, content_type="multipart/form-data")
        self.assertEqual(invalid_add.status_code, 400)
        self.assertEqual(set(upload_folder.iterdir()), original_files)

        invalid_edit = self.client.post(f"/admin/books/edit/{book_id}", data={
            **book_form,
            "cover_image": (BytesIO(b"truncated image"), "cover.jpg"),
        }, content_type="multipart/form-data")
        self.assertEqual(invalid_edit.status_code, 400)
        with self.app.app_context():
            self.assertEqual(list_books()[0]["cover_image"], original_cover)
        self.assertEqual(set(upload_folder.iterdir()), original_files)

        updated = self.client.post(f"/admin/books/edit/{book_id}", data={
            **book_form,
            "title": "Ảnh bìa đã đổi",
            "cover_image": (BytesIO(jpeg_data), "cover.png"),
        }, content_type="multipart/form-data")
        self.assertEqual(updated.status_code, 302)
        with self.app.app_context():
            new_cover = list_books()[0]["cover_image"]
        self.assertRegex(new_cover, r"^/static/uploads/books/[a-f0-9]{32}\.jpg$")
        self.assertNotEqual(new_cover, original_cover)
        with self.client.get(new_cover) as response:
            self.assertEqual(response.status_code, 200)
        self.assertFalse((upload_folder / Path(original_cover).name).exists())

    def test_login_rejects_wrong_password(self):
        self.register_user()
        anonymous_client = self.app.test_client()
        response = anonymous_client.post("/api/auth/login", json={
            "email": "student@example.com",
            "password": "wrong-password",
        })
        self.assertEqual(response.status_code, 401)
        self.assertEqual(anonymous_client.get("/api/auth/me").status_code, 401)

    def test_authentication_and_authorization_access_matrix(self):
        protected_api = "/api/admin/books/count"
        protected_page = "/admin/books"

        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)
        self.assertEqual(self.client.get(protected_api).status_code, 401)
        redirect_response = self.client.get(protected_page)
        self.assertEqual(redirect_response.status_code, 302)
        self.assertEqual(redirect_response.headers["Location"], "/login")

        self.assertEqual(self.register_user().status_code, 201)
        self.assertEqual(self.client.get("/api/auth/me").status_code, 200)
        self.assertEqual(self.client.get(protected_api).status_code, 403)
        self.assertEqual(self.client.get(protected_page).status_code, 403)

        self.assertEqual(self.client.post("/api/auth/logout").status_code, 200)
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)
        self.assertEqual(self.login_admin().status_code, 200)
        self.assertEqual(self.client.get(protected_api).status_code, 200)
        self.assertEqual(self.client.get(protected_page).status_code, 200)

    def test_failed_admin_form_login_does_not_authenticate_student(self):
        self.register_user()
        anonymous_client = self.app.test_client()
        response = anonymous_client.post("/login", data={
            "email": "student@example.com",
            "password": "StudentPassword123",
        })
        self.assertEqual(response.status_code, 401)
        self.assertEqual(anonymous_client.get("/api/auth/me").status_code, 401)

    def test_login_rate_limit_covers_api_and_admin_form(self):
        self.app.config.update(AUTH_LOGIN_RATE_LIMIT=2, AUTH_LOGIN_RATE_WINDOW=60)
        failed_login = {"email": "missing@example.com", "password": "wrong-password"}
        self.assertEqual(self.client.post("/api/auth/login", json=failed_login).status_code, 401)
        self.assertEqual(self.client.post("/api/auth/login", json=failed_login).status_code, 401)

        blocked = self.client.post("/login", data=failed_login)
        self.assertEqual(blocked.status_code, 429)
        self.assertGreaterEqual(int(blocked.headers["Retry-After"]), 1)

    def test_registration_rate_limit_and_login_limit_are_independent(self):
        self.app.config.update(AUTH_REGISTER_RATE_LIMIT=2, AUTH_REGISTER_RATE_WINDOW=60)
        self.assertEqual(self.register_user("one@example.com").status_code, 201)
        self.assertEqual(self.register_user("two@example.com").status_code, 201)
        blocked = self.register_user("three@example.com")
        self.assertEqual(blocked.status_code, 429)
        self.assertGreaterEqual(int(blocked.headers["Retry-After"]), 1)

        self.client.post("/api/auth/logout")
        self.assertEqual(self.login_admin().status_code, 200)

    def test_invalid_json_shapes_return_validation_errors(self):
        self.assertEqual(self.client.post("/api/auth/register", json=["not", "an", "object"]).status_code, 400)
        self.assertEqual(self.client.post("/api/auth/login", json=["not", "an", "object"]).status_code, 400)
        self.login_admin()
        response = self.client.post("/api/courses", json=["not", "a", "course"])
        self.assertEqual(response.status_code, 400)

    def test_course_validation_enforces_field_types_boundaries_and_no_writes(self):
        self.login_admin()
        original_courses = self.client.get("/api/courses").json
        boundary_payload = {
            "title": "x" * 150,
            "description": "d" * 1200,
            "details": "c" * 5000,
            "image_url": "",
            "course_url": "https://example.com/course",
        }
        created = self.client.post("/api/courses", json=boundary_payload)
        self.assertEqual(created.status_code, 201)
        course_id = created.json["id"]
        self.assertEqual(len(created.json["title"]), 150)
        self.assertEqual(len(created.json["description"]), 1200)
        self.assertEqual(len(created.json["details"]), 5000)

        invalid_payloads = (
            {},
            {"description": "Description", "course_url": boundary_payload["course_url"]},
            {key: value for key, value in boundary_payload.items() if key != "course_url"},
            {**boundary_payload, "title": ""},
            {**boundary_payload, "title": "   "},
            {**boundary_payload, "title": "x" * 151},
            {**boundary_payload, "description": "d" * 1201},
            {**boundary_payload, "details": "c" * 5001},
            {**boundary_payload, "title": ["not", "text"]},
            {**boundary_payload, "description": None},
            {**boundary_payload, "details": {"text": "not a string"}},
            {**boundary_payload, "course_url": None},
            {**boundary_payload, "course_url": "javascript:alert(1)"},
            {**boundary_payload, "course_url": "http://[invalid"},
            {**boundary_payload, "course_url": "https://example.com:bad"},
            {**boundary_payload, "image_url": ["not", "text"]},
            {**boundary_payload, "image_url": "https://example.com:bad/image.png"},
            {**boundary_payload, "image_url": "../private.png"},
        )
        expected_courses = [*original_courses, created.json]
        for payload in invalid_payloads:
            with self.subTest(operation="create", payload=payload):
                response = self.client.post("/api/courses", json=payload)
                self.assertEqual(response.status_code, 400)
                self.assertIsInstance(response.json.get("error"), str)
                self.assertEqual(self.client.get("/api/courses").json, expected_courses)

            with self.subTest(operation="update", payload=payload):
                response = self.client.put(f"/api/courses/{course_id}", json=payload)
                self.assertEqual(response.status_code, 400)
                self.assertIsInstance(response.json.get("error"), str)
                self.assertEqual(self.client.get("/api/courses").json, expected_courses)

        self.assertEqual(self.client.delete(f"/api/courses/{course_id}").status_code, 200)
        self.assertEqual(self.client.get("/api/courses").json, original_courses)

    def test_update_routes_reject_invalid_json_shapes_without_changing_data(self):
        self.login_admin()
        courses_before = self.client.get("/api/courses").json
        course_id = courses_before[0]["id"]
        invalid_requests = (
            {"json": ["not", "an", "object"]},
            {"data": "{broken", "content_type": "application/json"},
            {"data": "not-json", "content_type": "text/plain"},
        )
        for request_args in invalid_requests:
            with self.subTest(request_args=request_args):
                response = self.client.put(
                    f"/api/courses/{course_id}", **request_args
                )
                self.assertEqual(response.status_code, 400)
                self.assertIsInstance(response.json.get("error"), str)
                self.assertEqual(self.client.get("/api/courses").json, courses_before)

    def test_mvc_templates_keep_existing_page_urls_and_static_assets(self):
        for path in (
            "/",
            "/admin.html",
            "/blog.html",
            "/blogs/blog1.html",
            "/courses/cpp-basic-to-advance/index.html",
            "/Contributor/index2.html",
        ):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)

        homepage = self.client.get("/").get_data(as_text=True)
        self.assertIn('id="category-toggle"', homepage)
        self.assertIn('id="category-menu"', homepage)
        self.assertIn('id="site-search-input"', homepage)
        self.assertIn('id="header-register"', homepage)
        self.assertIn('id="books-show-more"', homepage)
        self.assertIn('id="courses-show-more"', homepage)

        for path in (
            "/assets/css/admin-dashboard.css",
            "/assets/js/auth.js",
            "/assets/css/site-header.css",
            "/assets/js/site-search.js",
            "/images/logo.svg",
        ):
            with self.subTest(path=path):
                with self.client.get(path) as response:
                    self.assertEqual(response.status_code, 200)

    def test_course_image_upload_is_admin_only_and_validates_image_data(self):
        png = BytesIO()
        Image.new("RGB", (2, 2), "green").save(png, format="PNG")
        png_data = png.getvalue()

        unauthorized = self.client.post("/api/admin/uploads", data={
            "image": (BytesIO(png_data), "course.png"),
        })
        self.assertEqual(unauthorized.status_code, 401)

        self.register_user()
        forbidden = self.client.post("/api/admin/uploads", data={
            "image": (BytesIO(png_data), "course.png"),
        })
        self.assertEqual(forbidden.status_code, 403)

        self.login_admin()
        invalid = self.client.post("/api/admin/uploads", data={
            "image": (BytesIO(b"not an image"), "course.png"),
        })
        self.assertEqual(invalid.status_code, 400)

        uploaded = self.client.post("/api/admin/uploads", data={
            "image": (BytesIO(png_data), "../../course.txt"),
        })
        self.assertEqual(uploaded.status_code, 201)
        self.assertRegex(uploaded.json["image_url"], r"^/uploads/[a-f0-9]{32}\.png$")
        course = self.client.post("/api/courses", json={
            "title": "Uploaded image course",
            "description": "Uses a server-uploaded image",
            "image_url": uploaded.json["image_url"],
            "course_url": "https://example.com/uploaded-image",
        })
        self.assertEqual(course.status_code, 201)
        self.assertEqual(course.json["image_url"], uploaded.json["image_url"])
        served_image = self.client.get(uploaded.json["image_url"])
        self.assertEqual(served_image.status_code, 200)
        self.assertTrue(served_image.content_type.startswith("image/png"))
        served_image.close()

        jpeg = BytesIO()
        Image.new("RGB", (2, 2), "blue").save(jpeg, format="JPEG")
        spoofed_extension = self.client.post("/api/admin/uploads", data={
            "image": (BytesIO(jpeg.getvalue()), "../../photo.png"),
        })
        self.assertEqual(spoofed_extension.status_code, 201)
        self.assertRegex(spoofed_extension.json["image_url"], r"^/uploads/[a-f0-9]{32}\.jpg$")
        with self.client.get(spoofed_extension.json["image_url"]) as response:
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.content_type.startswith("image/jpeg"))

        invalid_paths = (
            "/uploads/not-generated.jpg",
            "/uploads/" + "a" * 32 + ".txt",
            "/uploads/" + "a" * 32 + ".jpg/extra",
        )
        for path in invalid_paths:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)

        truncated = self.client.post("/api/admin/uploads", data={
            "image": (BytesIO(png_data[:-8]), "truncated.png"),
        })
        self.assertEqual(truncated.status_code, 400)

        oversized_dimensions = BytesIO()
        Image.new("1", (5001, 5000), 0).save(oversized_dimensions, format="PNG")
        too_many_pixels = self.client.post("/api/admin/uploads", data={
            "image": (BytesIO(oversized_dimensions.getvalue()), "large-image.png"),
        })
        self.assertEqual(too_many_pixels.status_code, 400)

        too_large = self.client.post("/api/admin/uploads", data={
            "image": (BytesIO(b"x" * (5 * 1024 * 1024 + 1)), "large.png"),
        })
        self.assertEqual(too_large.status_code, 413)


if __name__ == "__main__":
    unittest.main()
