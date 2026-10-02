"""The book screen: one tab per action (add, log, search, stats, update, remove)."""
from html import escape

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QLabel, QLineEdit, QMessageBox, QPushButton, QTabWidget, QVBoxLayout, QWidget,
)

from features.books.service import BookError
from features.books.widgets import BookForm, BookTable


class BookView(QWidget):
    """One tab per menu option: add, view, search, stats, update, remove."""

    def __init__(self, books):
        super().__init__()
        self.books = books
        self.editing_book = None  # the book currently loaded in the Update form

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.tabs.addTab(self._add_tab(), "Add Book")
        self.tabs.addTab(self._log_tab(), "Book Log")
        self.tabs.addTab(self._search_tab(), "Search Book")
        self.tabs.addTab(self._stats_tab(), "Summary Stats")
        self.tabs.addTab(self._update_tab(), "Update Book")
        self.tabs.addTab(self._remove_tab(), "Remove Book")
        for index in range(self.tabs.count()):
            self.tabs.widget(index).layout().setContentsMargins(20, 22, 20, 20)
        self.tabs.currentChanged.connect(lambda _: self.refresh())
        self.refresh()

    # ----- tabs -----
    def _add_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        self.add_form = BookForm()
        button = QPushButton("Add Book")
        button.setObjectName("primaryButton")
        button.clicked.connect(self.add_book)
        layout.addWidget(self.add_form)
        layout.addWidget(button)
        layout.addStretch(1)
        return page

    def _log_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        self.log_table = BookTable()
        layout.addWidget(self.log_table)
        return page

    def _search_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search title, author, or genre...")
        self.search_input.textChanged.connect(self.refresh_search)
        self.search_table = BookTable()
        layout.addWidget(self.search_input)
        layout.addWidget(self.search_table)
        return page

    def _stats_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        self.stats_label = QLabel()
        self.stats_label.setObjectName("statsText")
        self.stats_label.setTextFormat(Qt.TextFormat.RichText)
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.stats_label)
        return page

    def _update_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        self.update_table = BookTable()
        self.update_table.itemSelectionChanged.connect(self.load_for_update)
        self.update_form = BookForm()
        self.update_button = QPushButton("Save Changes")
        self.update_button.setObjectName("primaryButton")
        self.update_button.setEnabled(False)
        self.update_button.clicked.connect(self.update_book)
        hint = QLabel("Select a book above, edit its details, then save.")
        hint.setObjectName("appSubtitle")
        layout.addWidget(self.update_table, 1)
        layout.addWidget(hint)
        layout.addWidget(self.update_form)
        layout.addWidget(self.update_button)
        return page

    def _remove_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        self.remove_table = BookTable()
        self.remove_table.itemSelectionChanged.connect(
            lambda: self.remove_button.setEnabled(self.remove_table.selected_book() is not None)
        )
        self.remove_button = QPushButton("Remove Selected Book")
        self.remove_button.setObjectName("dangerButton")
        self.remove_button.setEnabled(False)
        self.remove_button.clicked.connect(self.remove_book)
        layout.addWidget(self.remove_table)
        layout.addWidget(self.remove_button)
        return page

    # ----- refresh -----
    def refresh(self):
        # start the Update tab fresh so old text never sits next to a disabled Save button
        self.editing_book = None
        self.update_form.clear()
        books = self.books.view_books()
        self.log_table.load(books)
        self.update_table.load(books)
        self.remove_table.load(books)
        self.refresh_search()
        self.refresh_stats()
        self.update_button.setEnabled(False)
        self.remove_button.setEnabled(False)

    def refresh_search(self):
        self.search_table.load(self.books.search_books(self.search_input.text()))

    def refresh_stats(self):
        s = self.books.summary_stats()
        # escape() stops characters like < and & in book data from breaking the HTML below
        rows = "".join(
            f"<tr><td>{escape(k)}</td><td><b>{v}</b></td></tr>" for k, v in s["by_status"].items()
        )
        avg = s["average_rating"] if s["average_rating"] is not None else "n/a"
        if s["top_author"]:
            author, count = s["top_author"]
            top = f"{escape(author)} ({count} {'book' if count == 1 else 'books'})"  # 1 book / 2 books
        else:
            top = "n/a"
        self.stats_label.setText(
            f"<h2>Reading Summary</h2>"
            f"<p>Total books: <b>{s['total']}</b></p>"
            f"<table cellspacing='6'>{rows}</table>"
            f"<p>Average rating: <b>{avg}</b></p>"
            f"<p>Most-logged author: <b>{top}</b></p>"
        )

    # ----- actions -----
    def _error(self, error):
        QMessageBox.warning(self, "Chapterd", str(error))

    def add_book(self):
        try:
            self.books.add_book(*self.add_form.values())
        except BookError as error:
            return self._error(error)
        self.add_form.clear()
        self.refresh()
        QMessageBox.information(self, "Chapterd", "Book added!")

    def load_for_update(self):
        """Fills the Update form with the selected book, asking first if edits would be lost."""
        book = self.update_table.selected_book()
        current = self.editing_book
        if current is not None and self.update_form.has_changes(current):
            if book is not None and book["id"] == current["id"]:
                return  # same book still selected, keep the edits
            answer = QMessageBox.question(
                self, "Unsaved Changes",
                f'Discard your unsaved changes to "{current["title"]}"?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                # user chose to keep editing: put the selection back on the original book
                self.update_table.select_book(current["id"])
                return
        self.editing_book = book
        if book:
            self.update_form.set_book(book)
        else:
            self.update_form.clear()
        self.update_button.setEnabled(book is not None)

    def update_book(self):
        book = self.editing_book  # the book loaded in the form, not just whatever row is selected
        if not book:
            return
        try:
            self.books.update_book(book["id"], *self.update_form.values())
        except BookError as error:
            return self._error(error)
        self.refresh()
        QMessageBox.information(self, "Chapterd", "Changes saved!")

    def remove_book(self):
        book = self.remove_table.selected_book()
        if not book:
            return
        answer = QMessageBox.question(
            self, "Remove Book", f'Remove "{book["title"]}" from your log?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            try:
                self.books.remove_book(book["id"])
            except BookError as error:
                return self._error(error)
            self.refresh()
