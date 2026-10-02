import hashlib
import hmac
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

def _escape_like(text: str) -> str:
    """Makes %, _ and \\ match literally inside a LIKE pattern (used with ESCAPE '\\')."""
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class Database:
    def __init__(self, database_path: str | Path | None = None):
        self.database_path = (
            Path(database_path)
            if database_path is not None
            else Path(__file__).resolve().parent.parent / "chapterd.db"
        )

    @contextmanager
    def connect(self):
        """Opens a connection, commits (or rolls back) on exit, and always closes it."""
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        # `with connection` alone only commits/rolls back; the finally makes sure it is closed too
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def create_tables(self, statuses: list[str]) -> None:
        """Creates the tables. `statuses` (from features/books/service.py) are the only allowed ones."""
        status_list = ", ".join(f"'{status}'" for status in statuses)
        invalid_book = f"NEW.status NOT IN ({status_list}) OR NEW.rating NOT BETWEEN 0 AND 5"
        with self.connect() as connection:
            connection.executescript(
                f"""
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

                -- usernames are unique regardless of upper/lower case
                CREATE UNIQUE INDEX IF NOT EXISTS users_username_nocase
                    ON users (username COLLATE NOCASE);

                -- the database itself rejects invalid statuses and ratings
                -- (dropped and re-made every start so a changed status list takes effect)
                DROP TRIGGER IF EXISTS books_validate_insert;
                DROP TRIGGER IF EXISTS books_validate_update;
                CREATE TRIGGER books_validate_insert
                    BEFORE INSERT ON books WHEN {invalid_book}
                BEGIN
                    SELECT RAISE(ABORT, 'invalid book status or rating');
                END;
                CREATE TRIGGER books_validate_update
                    BEFORE UPDATE ON books WHEN {invalid_book}
                BEGIN
                    SELECT RAISE(ABORT, 'invalid book status or rating');
                END;
                """
            )

    # ---------- authentication ----------
    @staticmethod
    def _hash(password: str, salt: bytes) -> str:
        return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000).hex()

    def register(self, username: str, password: str) -> bool:
        username = username.strip()
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

    def login(self, username: str, password: str) -> dict | None:
        """Returns {"id", "username"} if the credentials are valid, otherwise None."""
        with self.connect() as connection:
            row = connection.execute(
                # COLLATE NOCASE: "Jo", "jo" and "JO" all find the same account
                "SELECT id, username, password FROM users WHERE username = ? COLLATE NOCASE",
                (username.strip(),),
            ).fetchone()
        if row is None:
            return None
        salt_hex, stored_hash = row["password"].split("$")
        attempt = self._hash(password, bytes.fromhex(salt_hex))
        if not hmac.compare_digest(attempt, stored_hash):
            return None
        # return the username as it was registered, not as it was typed
        return {"id": row["id"], "username": row["username"]}

    # ---------- book log ----------
    def add_book(self, user_id, title, author, genre, status, rating, notes):
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
        like = f"%{_escape_like(keyword.strip())}%"
        # ESCAPE '\' tells SQLite that a backslash before % or _ means "match it literally"
        with self.connect() as connection:
            return connection.execute(
                "SELECT * FROM books WHERE user_id = ? "
                "AND (title LIKE ? ESCAPE '\\' OR author LIKE ? ESCAPE '\\' "
                "OR genre LIKE ? ESCAPE '\\') ORDER BY id",
                (user_id, like, like, like),
            ).fetchall()

    def book_exists(self, user_id, title, author, exclude_id=None) -> bool:
        """True if this user already logged a book with the same title and author (any case)."""
        with self.connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM books WHERE user_id = ? "
                # `id IS NOT ?` skips the book being edited; with None it matches every book
                "AND title = ? COLLATE NOCASE AND author = ? COLLATE NOCASE AND id IS NOT ?",
                (user_id, title.strip(), author.strip(), exclude_id),
            ).fetchone()
        return row is not None

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
            # read rowcount before the connection closes
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
            # group authors ignoring case so "Jo Author" and "jo author" count together
            top = connection.execute(
                "SELECT author, COUNT(*) AS n FROM books WHERE user_id = ? "
                "GROUP BY author COLLATE NOCASE ORDER BY n DESC, author COLLATE NOCASE LIMIT 1",
                (user_id,),
            ).fetchone()
        return {
            "total": total,
            "average_rating": round(avg, 2) if avg else None,
            # only statuses that have books; BookService adds the zeros
            "by_status": {row["status"]: row["n"] for row in by_status},
            "top_author": (top["author"], top["n"]) if top else None,
        }
