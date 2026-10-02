import hashlib
import hmac
import os
import sqlite3
from pathlib import Path

STATUSES = ["Want to Read", "Reading", "Finished", "Dropped"]


class Database:
    def __init__(self, database_path: str | Path | None = None):
        self.database_path = (
            Path(database_path)
            if database_path is not None
            else Path(__file__).resolve().parent.parent / "chapterd.db"
        )

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def create_tables(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS books (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    author TEXT NOT NULL,
                    genre TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'Want to Read',
                    rating INTEGER NOT NULL DEFAULT 0,
                    notes TEXT NOT NULL DEFAULT '',
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
                """
            )

    # ---------- authentication ----------
    @staticmethod
    def _hash(password: str, salt: bytes) -> str:
        return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000).hex()

    def register(self, username: str, password: str) -> bool:
        username = username.strip()
        if len(username) < 3 or len(password) < 4:
            return False
        salt = os.urandom(16)
        stored = f"{salt.hex()}${self._hash(password, salt)}"
        try:
            with self.connect() as connection:
                connection.execute(
                    "INSERT INTO users (username, password) VALUES (?, ?)",
                    (username, stored),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def login(self, username: str, password: str) -> int | None:
        """Returns the user id if the credentials are valid, otherwise None."""
        with self.connect() as connection:
            row = connection.execute(
                "SELECT id, password FROM users WHERE username = ?", (username.strip(),)
            ).fetchone()
        if row is None:
            return None
        salt_hex, stored_hash = row["password"].split("$")
        attempt = self._hash(password, bytes.fromhex(salt_hex))
        return row["id"] if hmac.compare_digest(attempt, stored_hash) else None

    # ---------- book log ----------
    def add_book(self, user_id, title, author, genre="", status="Want to Read", rating=0, notes=""):
        with self.connect() as connection:
            connection.execute(
                "INSERT INTO books (user_id, title, author, genre, status, rating, notes) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (user_id, title.strip(), author.strip(), genre.strip(), status, rating, notes.strip()),
            )

    def get_books(self, user_id):
        with self.connect() as connection:
            return connection.execute(
                "SELECT * FROM books WHERE user_id = ? ORDER BY id", (user_id,)
            ).fetchall()

    def search_books(self, user_id, keyword):
        like = f"%{keyword.strip()}%"
        with self.connect() as connection:
            return connection.execute(
                "SELECT * FROM books WHERE user_id = ? "
                "AND (title LIKE ? OR author LIKE ? OR genre LIKE ?) ORDER BY id",
                (user_id, like, like, like),
            ).fetchall()

    def get_book(self, user_id, book_id):
        with self.connect() as connection:
            return connection.execute(
                "SELECT * FROM books WHERE id = ? AND user_id = ?", (book_id, user_id)
            ).fetchone()

    def update_book(self, user_id, book_id, **fields) -> bool:
        allowed = {"title", "author", "genre", "status", "rating", "notes"}
        fields = {k: v for k, v in fields.items() if k in allowed}
        if not fields:
            return False
        assignments = ", ".join(f"{name} = ?" for name in fields)
        with self.connect() as connection:
            cursor = connection.execute(
                f"UPDATE books SET {assignments} WHERE id = ? AND user_id = ?",
                (*fields.values(), book_id, user_id),
            )
        return cursor.rowcount > 0

    def remove_book(self, user_id, book_id) -> bool:
        with self.connect() as connection:
            cursor = connection.execute(
                "DELETE FROM books WHERE id = ? AND user_id = ?", (book_id, user_id)
            )
        return cursor.rowcount > 0

    def summary_stats(self, user_id) -> dict:
        with self.connect() as connection:
            total, avg = connection.execute(
                "SELECT COUNT(*), AVG(NULLIF(rating, 0)) FROM books WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            by_status = connection.execute(
                "SELECT status, COUNT(*) AS n FROM books WHERE user_id = ? GROUP BY status",
                (user_id,),
            ).fetchall()
            top = connection.execute(
                "SELECT author, COUNT(*) AS n FROM books WHERE user_id = ? "
                "GROUP BY author ORDER BY n DESC, author LIMIT 1",
                (user_id,),
            ).fetchone()
        counts = {status: 0 for status in STATUSES}
        counts.update({row["status"]: row["n"] for row in by_status})
        return {
            "total": total,
            "average_rating": round(avg, 2) if avg else None,
            "by_status": counts,
            "top_author": (top["author"], top["n"]) if top else None,
        }


