from database.database import STATUSES, Database


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
    def _validate(title, author, status, rating):
        if not title.strip():
            raise BookError("Title is required.")
        if not author.strip():
            raise BookError("Author is required.")
        if status not in STATUSES:
            raise BookError("Invalid status.")
        if not 0 <= rating <= 5:
            raise BookError("Rating must be between 0 and 5.")

    def add_book(self, title, author, genre, status, rating, notes):
        self._validate(title, author, status, rating)
        self.database.add_book(self.user_id, title, author, genre, status, rating, notes)

    def view_books(self):
        return [dict(row) for row in self.database.get_books(self.user_id)]

    def search_books(self, keyword):
        return [dict(row) for row in self.database.search_books(self.user_id, keyword)]

    def update_book(self, book_id, title, author, genre, status, rating, notes):
        self._validate(title, author, status, rating)
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
