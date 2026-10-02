from database.database import STATUSES, Database

MAX_TEXT_LENGTH = 200  # title, author, genre
MAX_NOTES_LENGTH = 2000


class BookError(Exception):
    pass


class BookService:
    def __init__(self, database: Database, authentication):
        self.database = database
        self.authentication = authentication

    @property
    def user_id(self) -> int:
        return self.authentication.current_user["id"]

    @staticmethod
    def _validate(title, author, genre, status, rating, notes):
        if not title.strip():
            raise BookError("Title is required.")
        if not author.strip():
            raise BookError("Author is required.")
        for label, value in (("Title", title), ("Author", author), ("Genre", genre)):
            if len(value.strip()) > MAX_TEXT_LENGTH:
                raise BookError(f"{label} must be at most {MAX_TEXT_LENGTH} characters.")
        if len(notes.strip()) > MAX_NOTES_LENGTH:
            raise BookError(f"Notes must be at most {MAX_NOTES_LENGTH} characters.")
        if status not in STATUSES:
            raise BookError("Invalid status.")
        if not 0 <= rating <= 5:
            raise BookError("Rating must be between 0 and 5.")

    def _check_duplicate(self, title, author, exclude_id=None):
        if self.database.book_exists(self.user_id, title, author, exclude_id):
            raise BookError(f'"{title.strip()}" by {author.strip()} is already in your log.')

    def add_book(self, title, author, genre, status, rating, notes):
        self._validate(title, author, genre, status, rating, notes)
        self._check_duplicate(title, author)
        self.database.add_book(self.user_id, title, author, genre, status, rating, notes)

    def view_books(self):
        return [dict(row) for row in self.database.get_books(self.user_id)]

    def search_books(self, keyword):
        return [dict(row) for row in self.database.search_books(self.user_id, keyword)]

    def update_book(self, book_id, title, author, genre, status, rating, notes):
        self._validate(title, author, genre, status, rating, notes)
        self._check_duplicate(title, author, exclude_id=book_id)
        if not self.database.update_book(
            self.user_id, book_id, title=title.strip(), author=author.strip(),
            genre=genre.strip(), status=status, rating=rating, notes=notes.strip(),
        ):
            raise BookError("Book not found.")

    def remove_book(self, book_id):
        if not self.database.remove_book(self.user_id, book_id):
            raise BookError("Book not found.")

    def summary_stats(self):
        return self.database.summary_stats(self.user_id)
