import re
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
            "HSTS_ENABLED": False,
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
        self.assertEqual(response.headers["X-Frame-Options"], "DENY")
        self.assertIn("frame-ancestors 'none'", response.headers["Content-Security-Policy"])
        self.assertNotIn("Strict-Transport-Security", response.headers)

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

    def test_content_security_policy_nonce_covers_html_and_is_not_static(self):
        first_response = self.client.get("/")
        second_response = self.client.get("/")

        for response in (first_response, second_response):
            policy = response.headers["Content-Security-Policy"]
            script_policy = next(
                directive for directive in policy.split(";")
                if directive.strip().startswith("script-src ")
            )
            self.assertNotIn("'unsafe-inline'", script_policy)
            nonce = re.search(r"'nonce-([^']+)'", script_policy).group(1)
            script_tags = re.findall(r"<script\b[^>]*>", response.get_data(as_text=True))
            self.assertTrue(script_tags)
            self.assertTrue(all(f'nonce="{nonce}"' in tag for tag in script_tags))

        first_nonce = re.search(
            r"'nonce-([^']+)'", first_response.headers["Content-Security-Policy"]
        ).group(1)
        second_nonce = re.search(
            r"'nonce-([^']+)'", second_response.headers["Content-Security-Policy"]
        ).group(1)
        self.assertNotEqual(first_nonce, second_nonce)

    def test_security_headers_cover_login_admin_api_and_static_responses(self):
        responses = {
            "/login": self.client.get("/login"),
            "/blog.html": self.client.get("/blog.html"),
            "/api/courses": self.client.get("/api/courses"),
            "/assets/js/auth.js": self.client.get("/assets/js/auth.js"),
            "/assets/js/blog.js": self.client.get("/assets/js/blog.js"),
            "/assets/js/admin-books.js": self.client.get("/assets/js/admin-books.js"),
        }
        self.client.post("/api/auth/login", json={
            "email": "root@example.com",
            "password": "RootPassword123",
        })
        responses["/admin/books"] = self.client.get("/admin/books")

        try:
            for path, response in responses.items():
                with self.subTest(path=path):
                    self.assertIn("Content-Security-Policy", response.headers)
                    self.assertEqual(response.headers["X-Frame-Options"], "DENY")
                    if response.mimetype == "text/html":
                        nonce = re.search(
                            r"'nonce-([^']+)'",
                            response.headers["Content-Security-Policy"],
                        ).group(1)
                        script_tags = re.findall(
                            r"<script\b[^>]*>", response.get_data(as_text=True)
                        )
                        self.assertTrue(
                            all(f'nonce="{nonce}"' in tag for tag in script_tags)
                        )
            blog_html = responses["/blog.html"].get_data(as_text=True)
            self.assertNotIn("onclick=", blog_html)
            self.assertNotIn("javascript:", blog_html)
        finally:
            for response in responses.values():
                response.close()

    def test_hsts_is_enabled_only_by_explicit_configuration(self):
        self.app.config["HSTS_ENABLED"] = True

        response = self.client.get("/")

        self.assertEqual(
            response.headers["Strict-Transport-Security"], "max-age=31536000"
        )

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
