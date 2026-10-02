"""Tests for the database and service layers (no window needed).

Run from the chapterd_qt folder:  python -m unittest discover -s tests -v
"""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from database.database import Database
from features.authentication.service import AuthenticationError, AuthenticationService
from features.books.service import BookError, BookService


class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.database = Database(Path(self.tmp.name) / "test.db")
        self.database.create_tables()
        self.auth = AuthenticationService(self.database)
        self.books = BookService(self.database, self.auth)

    def tearDown(self):
        self.tmp.cleanup()

    def log_in(self, username="reader", password="password123"):
        self.auth.register(username, password, password)
        return self.auth.login(username, password)


class DatabaseTests(AppTestCase):
    def test_connections_are_closed(self):
        with self.database.connect() as connection:
            connection.execute("SELECT 1")
        with self.assertRaises(sqlite3.ProgrammingError):  # "Cannot operate on a closed database"
            connection.execute("SELECT 1")

    def test_invalid_status_and_rating_rejected_by_database(self):
        user = self.log_in()
        with self.assertRaises(sqlite3.IntegrityError):
            self.database.add_book(user["id"], "T", "A", status="Nope")
        with self.assertRaises(sqlite3.IntegrityError):
            self.database.add_book(user["id"], "T", "A", rating=9)

    def test_search_treats_wildcards_literally(self):
        self.log_in()
        self.books.add_book("Dune", "Frank Herbert", "", "Reading", 0, "")
        self.books.add_book("100% Real", "Someone", "", "Reading", 0, "")
        self.assertEqual(len(self.books.search_books("%")), 1)
        self.assertEqual(len(self.books.search_books("_")), 0)
        self.assertEqual(len(self.books.search_books("")), 2)


class AuthenticationTests(AppTestCase):
    def test_username_is_case_insensitive(self):
        self.log_in("Reader")
        with self.assertRaises(AuthenticationError):
            self.auth.register("reader", "password123", "password123")
        user = self.auth.login("READER", "password123")
        self.assertEqual(user["username"], "Reader")

    def test_password_rules(self):
        with self.assertRaises(AuthenticationError):
            self.auth.register("reader", "short", "short")
        with self.assertRaises(AuthenticationError):
            self.auth.register("reader", "password123", "password124")

    def test_wrong_password(self):
        self.log_in()
        with self.assertRaises(AuthenticationError):
            self.auth.login("reader", "wrongpassword")


class BookTests(AppTestCase):
    def setUp(self):
        super().setUp()
        self.log_in()

    def test_add_update_remove(self):
        self.books.add_book("Dune", "Frank Herbert", "Sci-Fi", "Reading", 4, "")
        book = self.books.view_books()[0]
        self.books.update_book(book["id"], "Dune", "Frank Herbert", "Sci-Fi", "Finished", 5, "great")
        self.assertEqual(self.books.view_books()[0]["status"], "Finished")
        self.books.remove_book(book["id"])
        self.assertEqual(self.books.view_books(), [])

    def test_duplicate_books_blocked(self):
        self.books.add_book("Dune", "Frank Herbert", "", "Reading", 0, "")
        with self.assertRaises(BookError):
            self.books.add_book("dune", "FRANK HERBERT", "", "Reading", 0, "")
        # updating a book without changing its title/author is not a duplicate
        book = self.books.view_books()[0]
        self.books.update_book(book["id"], "Dune", "Frank Herbert", "", "Finished", 3, "")

    def test_length_limits(self):
        with self.assertRaises(BookError):
            self.books.add_book("x" * 201, "A", "", "Reading", 0, "")
        with self.assertRaises(BookError):
            self.books.add_book("T", "A", "", "Reading", 0, "x" * 2001)

    def test_top_author_ignores_case(self):
        self.books.add_book("Book 1", "Jo Author", "", "Reading", 0, "")
        self.books.add_book("Book 2", "jo author", "", "Reading", 0, "")
        self.books.add_book("Book 3", "Other", "", "Reading", 0, "")
        _, count = self.books.summary_stats()["top_author"]
        self.assertEqual(count, 2)

    def test_users_only_see_their_own_books(self):
        self.books.add_book("Dune", "Frank Herbert", "", "Reading", 0, "")
        self.log_in("another", "password123")
        self.assertEqual(self.books.view_books(), [])


if __name__ == "__main__":
    unittest.main()
