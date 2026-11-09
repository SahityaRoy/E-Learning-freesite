import re
import tempfile
import unittest
from pathlib import Path

from app import create_app


class CsrfProtectionTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "csrf-test-secret",
            "DATABASE": str(Path(self.temp_dir.name) / "test.sqlite3"),
            "BOOTSTRAP_ADMIN_EMAIL": "root@example.com",
            "BOOTSTRAP_ADMIN_PASSWORD": "RootPassword123",
            "UPLOAD_FOLDER": str(Path(self.temp_dir.name) / "uploads"),
            "BOOK_UPLOAD_FOLDER": str(Path(self.temp_dir.name) / "books"),
            "CSRF_ENABLED": True,
        })
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def get_csrf_token(self, path="/auth.html"):
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertIn("X-CSRF-Token", response.headers)
        return response.headers["X-CSRF-Token"], response

    def test_html_forms_and_token_endpoint_expose_session_token(self):
        token, page = self.get_csrf_token("/login")
        self.assertIn(f'<meta name="csrf-token" content="{token}">', page.get_data(as_text=True))
        self.assertIn(f'name="_csrf_token" value="{token}"', page.get_data(as_text=True))
        self.assertNotIn(token, page.request.url)

        token_response = self.client.get("/api/csrf-token")
        self.assertEqual(token_response.status_code, 200)
        self.assertEqual(token_response.json["csrf_token"], token)
        self.assertEqual(token_response.headers["X-CSRF-Token"], token)
        self.assertEqual(token_response.headers["Cache-Control"], "no-store")

    def test_registration_rejects_missing_and_invalid_tokens_and_rotates_after_login(self):
        token, _ = self.get_csrf_token()
        payload = {
            "name": "Student",
            "email": "student@example.com",
            "password": "StudentPassword123",
        }

        missing = self.client.post("/api/auth/register", json=payload)
        self.assertEqual(missing.status_code, 400)
        self.assertIn("CSRF", missing.json["error"])

        invalid = self.client.post(
            "/api/auth/register",
            json=payload,
            headers={"X-CSRF-Token": "invalid-token"},
        )
        self.assertEqual(invalid.status_code, 400)

        accepted = self.client.post(
            "/api/auth/register",
            json=payload,
            headers={"X-CSRF-Token": token},
        )
        self.assertEqual(accepted.status_code, 201)
        refreshed_token = accepted.headers["X-CSRF-Token"]
        self.assertNotEqual(refreshed_token, token)
        self.assertEqual(self.client.get("/api/auth/me").status_code, 200)

    def test_admin_api_requires_token_and_preserves_server_side_role_check(self):
        token, _ = self.get_csrf_token()
        login = self.client.post(
            "/api/auth/login",
            json={"email": "root@example.com", "password": "RootPassword123"},
            headers={"X-CSRF-Token": token},
        )
        self.assertEqual(login.status_code, 200)
        token = login.headers["X-CSRF-Token"]

        payload = {
            "name": "Second Admin",
            "email": "second-admin@example.com",
            "password": "SecondPassword123",
        }
        missing = self.client.post("/api/admin/users", json=payload)
        self.assertEqual(missing.status_code, 400)
        invalid = self.client.post(
            "/api/admin/users",
            json=payload,
            headers={"X-CSRF-Token": "invalid-token"},
        )
        self.assertEqual(invalid.status_code, 400)

        created = self.client.post(
            "/api/admin/users",
            json=payload,
            headers={"X-CSRF-Token": token},
        )
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.json["role"], "admin")

    def test_admin_course_create_update_and_delete_require_tokens(self):
        token, _ = self.get_csrf_token()
        login = self.client.post(
            "/api/auth/login",
            json={"email": "root@example.com", "password": "RootPassword123"},
            headers={"X-CSRF-Token": token},
        )
        self.assertEqual(login.status_code, 200)
        token = login.headers["X-CSRF-Token"]
        course = {
            "title": "Python",
            "description": "Python cơ bản",
            "details": "Nội dung Python",
            "image_url": "",
            "course_url": "https://example.com/python",
        }
        created = self.client.post(
            "/api/courses",
            json=course,
            headers={"X-CSRF-Token": token},
        )
        self.assertEqual(created.status_code, 201)
        course_id = created.json["id"]

        updated_payload = {**course, "title": "Python nâng cao"}
        for headers in ({}, {"X-CSRF-Token": "invalid-token"}):
            with self.subTest(method="PUT", headers=headers):
                rejected = self.client.put(
                    f"/api/courses/{course_id}",
                    json=updated_payload,
                    headers=headers,
                )
                self.assertEqual(rejected.status_code, 400)
        updated = self.client.put(
            f"/api/courses/{course_id}",
            json=updated_payload,
            headers={"X-CSRF-Token": token},
        )
        self.assertEqual(updated.status_code, 200)

        for headers in ({}, {"X-CSRF-Token": "invalid-token"}):
            with self.subTest(method="DELETE", headers=headers):
                rejected = self.client.delete(
                    f"/api/courses/{course_id}",
                    headers=headers,
                )
                self.assertEqual(rejected.status_code, 400)
        deleted = self.client.delete(
            f"/api/courses/{course_id}",
            headers={"X-CSRF-Token": token},
        )
        self.assertEqual(deleted.status_code, 200)

    def test_public_quiz_submission_requires_valid_csrf_token(self):
        token, _ = self.get_csrf_token()
        attempt = {
            "examId": "python-basics",
            "title": "Python cơ bản",
            "subject": "Python",
            "correct": 4,
            "total": 5,
            "duration": 120,
        }
        self.assertEqual(
            self.client.post("/api/quiz/attempts", json=attempt).status_code,
            400,
        )
        self.assertEqual(
            self.client.post(
                "/api/quiz/attempts",
                json=attempt,
                headers={"X-CSRF-Token": "invalid-token"},
            ).status_code,
            400,
        )
        accepted = self.client.post(
            "/api/quiz/attempts",
            json=attempt,
            headers={"X-CSRF-Token": token},
        )
        self.assertEqual(accepted.status_code, 201)

    def test_html_login_form_rejects_missing_token_and_accepts_hidden_token(self):
        token, page = self.get_csrf_token("/login")
        self.assertRegex(
            page.get_data(as_text=True),
            re.compile(r'name="_csrf_token"\s+value="' + re.escape(token) + r'"'),
        )
        credentials = {
            "email": "root@example.com",
            "password": "RootPassword123",
        }

        missing = self.client.post("/login", data=credentials)
        self.assertEqual(missing.status_code, 400)

        accepted = self.client.post(
            "/login",
            data={**credentials, "_csrf_token": token},
        )
        self.assertEqual(accepted.status_code, 302)
        self.assertNotEqual(accepted.headers["X-CSRF-Token"], token)

    def test_admin_book_form_contains_csrf_hidden_field(self):
        token, _ = self.get_csrf_token()
        login = self.client.post(
            "/api/auth/login",
            json={"email": "root@example.com", "password": "RootPassword123"},
            headers={"X-CSRF-Token": token},
        )
        self.assertEqual(login.status_code, 200)

        form_page = self.client.get("/admin/books/add")
        self.assertEqual(form_page.status_code, 200)
        self.assertIn(
            f'name="_csrf_token" value="{form_page.headers["X-CSRF-Token"]}"',
            form_page.get_data(as_text=True),
        )

    def test_non_admin_with_valid_token_still_cannot_call_admin_api(self):
        token, _ = self.get_csrf_token()
        registration = self.client.post(
            "/api/auth/register",
            json={
                "name": "Student",
                "email": "student@example.com",
                "password": "StudentPassword123",
            },
            headers={"X-CSRF-Token": token},
        )
        self.assertEqual(registration.status_code, 201)

        forbidden = self.client.post(
            "/api/admin/users",
            json={
                "name": "Unauthorized Admin",
                "email": "unauthorized@example.com",
                "password": "StudentPassword123",
            },
            headers={"X-CSRF-Token": registration.headers["X-CSRF-Token"]},
        )
        self.assertEqual(forbidden.status_code, 403)
