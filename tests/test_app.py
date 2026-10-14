from io import BytesIO
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

import controllers
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
        })
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
            "image_url": "images/picture/card-1.png",
            "course_url": "https://example.com/python",
        })
        self.assertEqual(created.status_code, 201)
        course_id = created.json["id"]

        updated = self.client.put(f"/api/courses/{course_id}", json={
            "title": "Python nâng cao",
            "description": "Nội dung đã sửa",
            "image_url": "",
            "course_url": "https://example.com/advanced-python",
        })
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json["title"], "Python nâng cao")
        self.assertEqual(self.client.put("/api/courses/99999", json=updated.json).status_code, 404)
        self.assertEqual(self.client.delete(f"/api/courses/{course_id}").status_code, 200)
        self.assertEqual(self.client.delete(f"/api/courses/{course_id}").status_code, 404)

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

    def test_login_rejects_wrong_password(self):
        self.register_user()
        response = self.client.post("/api/auth/login", json={
            "email": "student@example.com",
            "password": "wrong-password",
        })
        self.assertEqual(response.status_code, 401)

    def test_google_login_creates_and_authenticates_account(self):
        google_user = {
            "email": "google-user@example.com",
            "name": "Google Student",
            "sub": "google-sub-123",
        }
        with patch.object(controllers, "verify_google_id_token", return_value=google_user):
            response = self.client.post("/api/auth/google", json={"credential": "valid-token"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["email"], google_user["email"])
        self.assertEqual(response.json["name"], google_user["name"])
        self.assertEqual(response.json["role"], "user")
        with self.client.session_transaction() as user_session:
            self.assertIn("user_id", user_session)

    def test_invalid_json_shapes_return_validation_errors(self):
        self.assertEqual(self.client.post("/api/auth/register", json=["not", "an", "object"]).status_code, 400)
        self.login_admin()
        response = self.client.post("/api/courses", json=["not", "a", "course"])
        self.assertEqual(response.status_code, 400)

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

        for path in (
            "/assets/css/admin-dashboard.css",
            "/assets/js/auth.js",
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

        too_large = self.client.post("/api/admin/uploads", data={
            "image": (BytesIO(b"x" * (5 * 1024 * 1024 + 1)), "large.png"),
        })
        self.assertEqual(too_large.status_code, 413)


if __name__ == "__main__":
    unittest.main()