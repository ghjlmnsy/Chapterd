from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView, QComboBox, QFormLayout, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QMessageBox, QPlainTextEdit, QPushButton, QSpinBox, QTableWidget,
    QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget,
)

from database.database import STATUSES
from features.books.service import BookError

COLUMNS = ["ID", "Title", "Author", "Genre", "Status", "Rating"]


class BookTable(QTableWidget):
    def __init__(self):
        super().__init__(0, len(COLUMNS))
        self.setHorizontalHeaderLabels(COLUMNS)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)

    def load(self, books):
        self.blockSignals(True)
        self.setRowCount(len(books))
        for r, book in enumerate(books):
            stars = "★" * book["rating"] + "☆" * (5 - book["rating"])
            values = [book["id"], book["title"], book["author"], book["genre"], book["status"], stars]
            for c, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if c == 0:
                    item.setData(Qt.ItemDataRole.UserRole, book)
                self.setItem(r, c, item)
        self.blockSignals(False)
        self.clearSelection()

    def selected_book(self):
        items = self.selectedItems()
        if not items:
            return None
        return self.item(items[0].row(), 0).data(Qt.ItemDataRole.UserRole)


class BookForm(QWidget):
    def __init__(self):
        super().__init__()
        form = QFormLayout(self)
        form.setContentsMargins(0, 0, 0, 0)
        self.title = QLineEdit()
        self.author = QLineEdit()
        self.genre = QLineEdit()
        self.status = QComboBox()
        self.status.addItems(STATUSES)
        self.rating = QSpinBox()
        self.rating.setRange(0, 5)
        self.rating.setSuffix(" / 5")
        self.notes = QPlainTextEdit()
        self.notes.setFixedHeight(70)
        form.addRow("Title", self.title)
        form.addRow("Author", self.author)
        form.addRow("Genre", self.genre)
        form.addRow("Status", self.status)
        form.addRow("Rating", self.rating)
        form.addRow("Notes", self.notes)

    def values(self):
        return (self.title.text(), self.author.text(), self.genre.text(),
                self.status.currentText(), self.rating.value(), self.notes.toPlainText())

    def set_book(self, book):
        self.title.setText(book["title"])
        self.author.setText(book["author"])
        self.genre.setText(book["genre"])
        self.status.setCurrentText(book["status"])
        self.rating.setValue(book["rating"])
        self.notes.setPlainText(book["notes"])

    def clear(self):
        for field in (self.title, self.author, self.genre):
            field.clear()
        self.status.setCurrentIndex(0)
        self.rating.setValue(0)
        self.notes.clear()


class BookView(QWidget):
    """One tab per menu option: add, view, search, stats, update, remove."""

    def __init__(self, books):
        super().__init__()
        self.books = books

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
        rows = "".join(f"<tr><td>{k}</td><td><b>{v}</b></td></tr>" for k, v in s["by_status"].items())
        avg = s["average_rating"] if s["average_rating"] is not None else "n/a"
        top = f"{s['top_author'][0]} ({s['top_author'][1]} books)" if s["top_author"] else "n/a"
        self.stats_label.setText(
            f"<h2>Reading Summary</h2>"
            f"<p>Total books: <b>{s['total']}</b></p>"
            f"<table cellspacing='6'>{rows}</table>"
            f"<p>Average rating: <b>{avg}</b></p>"
            f"<p>Most-logged author: <b>{top}</b></p>"
        )

    # ----- actions -----
    def _error(self, error):
        QMessageBox.warning(self, "LetterBook", str(error))

    def add_book(self):
        try:
            self.books.add_book(*self.add_form.values())
        except BookError as error:
            return self._error(error)
        self.add_form.clear()
        self.refresh()
        QMessageBox.information(self, "LetterBook", "Book added!")

    def load_for_update(self):
        book = self.update_table.selected_book()
        if book:
            self.update_form.set_book(book)
            self.update_button.setEnabled(True)

    def update_book(self):
        book = self.update_table.selected_book()
        if not book:
            return
        try:
            self.books.update_book(book["id"], *self.update_form.values())
        except BookError as error:
            return self._error(error)
        self.update_form.clear()
        self.refresh()

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
