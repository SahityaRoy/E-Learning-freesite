import tempfile
import time
import unittest
from pathlib import Path

from app import create_app


class NonFunctionalRequirementTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test-only-secret",
            "DATABASE": str(Path(self.temp_dir.name) / "test.sqlite3"),
            "BOOTSTRAP_ADMIN_EMAIL": "root@example.com",
            "BOOTSTRAP_ADMIN_PASSWORD": "RootPassword123",
            "UPLOAD_FOLDER": str(Path(self.temp_dir.name) / "uploads"),
            "BOOK_UPLOAD_FOLDER": str(Path(self.temp_dir.name) / "books"),
            "SESSION_COOKIE_SECURE": True,
        })
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_security_headers_and_session_cookie_flags(self):
        response = self.client.get("/")
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(
            response.headers["Referrer-Policy"], "strict-origin-when-cross-origin"
        )

        login = self.client.post("/api/auth/login", json={
            "email": "root@example.com",
            "password": "RootPassword123",
        })
        self.assertEqual(login.status_code, 200)
        session_cookie = next(
            cookie for cookie in login.headers.getlist("Set-Cookie")
            if cookie.startswith("session=")
        )
        self.assertIn("HttpOnly", session_cookie)
        self.assertIn("SameSite=Lax", session_cookie)
        self.assertIn("Secure", session_cookie)

    def test_auth_responses_do_not_expose_passwords_or_password_hashes(self):
        password = "StudentPassword123"
        registration = self.client.post("/api/auth/register", json={
            "name": "Student",
            "email": "student@example.com",
            "password": password,
        })
        self.assertEqual(registration.status_code, 201)
        self.assertNotIn("password", registration.json)
        self.assertNotIn("password_hash", registration.json)
        self.assertNotIn(password, registration.get_data(as_text=True))

        with self.app.app_context():
            from models import find_user_by_email

            stored_hash = find_user_by_email("student@example.com")["password_hash"]
        self.assertNotEqual(stored_hash, password)

        self.client.post("/api/auth/logout")
        login = self.client.post("/api/auth/login", json={
            "email": "student@example.com",
            "password": password,
        })
        self.assertEqual(login.status_code, 200)
        self.assertNotIn("password", login.json)
        self.assertNotIn("password_hash", login.json)
        self.assertNotIn(password, login.get_data(as_text=True))

    def test_login_treats_sql_syntax_in_email_as_data(self):
        response = self.client.post("/api/auth/login", json={
            "email": "x'OR'1'='1'--@example.com",
            "password": "anything",
        })
        self.assertEqual(response.status_code, 401)
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)

    def test_course_list_performance_smoke_with_500_records(self):
        from models import get_database

        with self.app.app_context():
            database = get_database()
            database.execute("DELETE FROM courses")
            database.executemany(
                "INSERT INTO courses (title, description, image_url, course_url, details) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    (
                        f"Course {index}",
                        "Performance smoke-test record",
                        "",
                        "https://example.com/course",
                        "",
                    )
                    for index in range(500)
                ),
            )
            database.commit()

        warmup = self.client.get("/api/courses")
        self.assertEqual(warmup.status_code, 200)
        self.assertEqual(len(warmup.json), 500)

        started = time.perf_counter()
        for _ in range(10):
            response = self.client.get("/api/courses")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.json), 500)
        elapsed = time.perf_counter() - started

        self.assertLess(
            elapsed,
            3.0,
            f"10 in-process requests for 500 courses took {elapsed:.3f}s (budget: 3.0s)",
        )


if __name__ == "__main__":
    unittest.main()
