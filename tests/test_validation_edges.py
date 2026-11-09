from io import BytesIO
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from app import create_app


class ValidationEdgeCaseTests(unittest.TestCase):
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
            "CSRF_ENABLED": False,
        })
        self.client = self.app.test_client()
        with self.app.app_context():
            from models import get_database

            get_database().execute("DELETE FROM books")
            get_database().commit()
        self.login_admin()

    def tearDown(self):
        self.temp_dir.cleanup()

    def login_admin(self):
        response = self.client.post("/api/auth/login", json={
            "email": "root@example.com",
            "password": "RootPassword123",
        })
        self.assertEqual(response.status_code, 200)

    @staticmethod
    def valid_book_form():
        return {
            "title": "Boundary Test Book",
            "author": "Test Author",
            "category": "Testing",
            "description": "A test description",
            "details": "Test details",
            "document_url": "https://example.com/book.pdf",
        }

    @staticmethod
    def cover_upload():
        image = BytesIO()
        Image.new("RGB", (2, 2), "blue").save(image, format="PNG")
        return BytesIO(image.getvalue()), "cover.png"

    def books_snapshot(self):
        with self.app.app_context():
            from models import list_books

            return [dict(book) for book in list_books()]

    def test_book_fields_accept_maximum_lengths_and_reject_invalid_values_without_writes(self):
        boundary_form = {
            "title": "t" * 200,
            "author": "a" * 120,
            "category": "c" * 80,
            "description": "d" * 2000,
            "details": "x" * 5000,
            "document_url": "https://example.com/book.pdf",
            "cover_image": self.cover_upload(),
        }
        created = self.client.post(
            "/admin/books/add",
            data=boundary_form,
            content_type="multipart/form-data",
        )
        self.assertEqual(created.status_code, 302)
        original_books = self.books_snapshot()
        self.assertEqual(len(original_books), 1)
        original_book = original_books[0]
        book_id = original_book["id"]
        self.assertEqual(len(original_book["title"]), 200)
        self.assertEqual(len(original_book["author"]), 120)
        self.assertEqual(len(original_book["category"]), 80)
        self.assertEqual(len(original_book["description"]), 2000)
        self.assertEqual(len(original_book["details"]), 5000)

        invalid_forms = (
            {**self.valid_book_form(), "title": ""},
            {**self.valid_book_form(), "title": "t" * 201},
            {**self.valid_book_form(), "author": "a" * 121},
            {**self.valid_book_form(), "category": "c" * 81},
            {**self.valid_book_form(), "description": "d" * 2001},
            {**self.valid_book_form(), "details": "x" * 5001},
            {**self.valid_book_form(), "document_url": "javascript:alert(1)"},
            {**self.valid_book_form(), "document_url": "https://[invalid"},
            {**self.valid_book_form(), "document_url": "https://example.com:bad/book.pdf"},
            {**self.valid_book_form(), "cover_image": "../private.png"},
        )
        for invalid_form in invalid_forms:
            with self.subTest(form=invalid_form):
                rejected_create = self.client.post(
                    "/admin/books/add", data=invalid_form
                )
                self.assertEqual(rejected_create.status_code, 400)
                self.assertIn("error", rejected_create.get_data(as_text=True).lower())
                self.assertEqual(self.books_snapshot(), original_books)

                rejected_update = self.client.post(
                    f"/admin/books/edit/{book_id}", data=invalid_form
                )
                self.assertEqual(rejected_update.status_code, 400)
                self.assertEqual(self.books_snapshot(), original_books)

    def test_quiz_attempts_accept_numeric_boundaries_and_reject_invalid_state_without_writes(self):
        boundary_attempts = (
            {
                "examId": "x",
                "title": "x",
                "subject": "x",
                "correct": 0,
                "total": 1,
                "duration": 0,
            },
            {
                "examId": "x" * 100,
                "title": "t" * 100,
                "subject": "s" * 60,
                "correct": 200,
                "total": 200,
                "duration": 18000,
            },
        )
        for attempt in boundary_attempts:
            with self.subTest(attempt=attempt):
                self.assertEqual(
                    self.client.post("/api/quiz/attempts", json=attempt).status_code,
                    201,
                )

        invalid_attempts = (
            {},
            {"examId": "", "title": "Quiz", "subject": "Python", "correct": 0, "total": 1, "duration": 0},
            {"examId": "x" * 101, "title": "Quiz", "subject": "Python", "correct": 0, "total": 1, "duration": 0},
            {"examId": "quiz", "title": "", "subject": "Python", "correct": 0, "total": 1, "duration": 0},
            {"examId": "quiz", "title": "t" * 101, "subject": "Python", "correct": 0, "total": 1, "duration": 0},
            {"examId": "quiz", "title": "Quiz", "subject": "", "correct": 0, "total": 1, "duration": 0},
            {"examId": "quiz", "title": "Quiz", "subject": "s" * 61, "correct": 0, "total": 1, "duration": 0},
            {"examId": "quiz", "title": "Quiz", "subject": "Python", "correct": 0, "total": 0, "duration": 0},
            {"examId": "quiz", "title": "Quiz", "subject": "Python", "correct": 0, "total": 201, "duration": 0},
            {"examId": "quiz", "title": "Quiz", "subject": "Python", "correct": -1, "total": 1, "duration": 0},
            {"examId": "quiz", "title": "Quiz", "subject": "Python", "correct": 2, "total": 1, "duration": 0},
            {"examId": "quiz", "title": "Quiz", "subject": "Python", "correct": 0, "total": 1, "duration": -1},
            {"examId": "quiz", "title": "Quiz", "subject": "Python", "correct": 0, "total": 1, "duration": 18001},
            {"examId": "quiz", "title": "Quiz", "subject": "Python", "correct": True, "total": 1, "duration": 0},
            {"examId": "quiz", "title": "Quiz", "subject": "Python", "correct": 0, "total": True, "duration": 0},
            {"examId": "quiz", "title": "Quiz", "subject": "Python", "correct": 0, "total": 1, "duration": False},
        )
        with self.app.app_context():
            from models import get_database

            database = get_database()
            initial_attempts = database.execute(
                "SELECT COUNT(*) FROM quiz_attempts"
            ).fetchone()[0]

        for attempt in invalid_attempts:
            with self.subTest(attempt=attempt):
                response = self.client.post("/api/quiz/attempts", json=attempt)
                self.assertEqual(response.status_code, 400)
                self.assertIsInstance(response.json.get("error"), str)
                with self.app.app_context():
                    from models import get_database

                    count = get_database().execute(
                        "SELECT COUNT(*) FROM quiz_attempts"
                    ).fetchone()[0]
                self.assertEqual(count, initial_attempts)

    def test_quiz_attempts_reject_non_integer_numeric_values_without_writes(self):
        invalid_attempts = []
        valid_attempt = {
            "examId": "python-basics",
            "title": "Python cơ bản",
            "subject": "Python",
            "correct": 1,
            "total": 5,
            "duration": 120,
        }
        for field in ("correct", "total", "duration"):
            for value in ("1", 1.0, None):
                invalid_attempts.append({**valid_attempt, field: value})

        with self.app.app_context():
            from models import get_database

            database = get_database()
            initial_attempts = database.execute(
                "SELECT COUNT(*) FROM quiz_attempts"
            ).fetchone()[0]

        for attempt in invalid_attempts:
            with self.subTest(attempt=attempt):
                response = self.client.post("/api/quiz/attempts", json=attempt)
                self.assertEqual(response.status_code, 400)
                self.assertIsInstance(response.json.get("error"), str)
                with self.app.app_context():
                    from models import get_database

                    count = get_database().execute(
                        "SELECT COUNT(*) FROM quiz_attempts"
                    ).fetchone()[0]
                self.assertEqual(count, initial_attempts)


if __name__ == "__main__":
    unittest.main()
