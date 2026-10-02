"""Reusable book widgets (table, form, status dropdown, title suggestions) used by view.py."""
from PyQt6.QtCore import QObject, QStringListModel, Qt, QTimer, QUrl
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PyQt6.QtWidgets import (
    QAbstractItemView, QComboBox, QCompleter, QFormLayout, QHeaderView, QLineEdit,
    QPlainTextEdit, QTableWidget, QTableWidgetItem, QWidget,
)

from features.books.lookup import parse_results, search_url
from features.books.service import MAX_TEXT_LENGTH, STATUSES

COLUMNS = ["ID", "Title", "Author", "Genre", "Status", "Rating"]

# color per reading status
STATUS_COLORS = {
    "Want to Read": "#3b6ea5",  
    "Reading": "#c27c0e",       
    "Finished": "#3f8a4f",      
    "Dropped": "#b23b3b",       
}


def stars(rating):
    """0 -> "Unrated", 3 -> "★★★☆☆"."""
    return "★" * rating + "☆" * (5 - rating) if rating else "Unrated"


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
            values = [book["id"], book["title"], book["author"], book["genre"],
                      book["status"], stars(book["rating"])]
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

    def select_book(self, book_id):
        """Selects the row for book_id without emitting selection signals."""
        self.blockSignals(True)
        self.clearSelection()
        for row in range(self.rowCount()):
            if self.item(row, 0).data(Qt.ItemDataRole.UserRole)["id"] == book_id:
                self.selectRow(row)
                break
        self.blockSignals(False)


class StatusComboBox(QComboBox):
    def __init__(self):
        super().__init__()
        self.addItems(STATUSES)
        self.highlighted.connect(self.color_bar)
        self.currentIndexChanged.connect(self.color_bar)

    def showPopup(self):
        super().showPopup()
        self.color_bar(self.currentIndex())

    def color_bar(self, index):
        status = self.itemText(index)
        if status not in STATUS_COLORS:
            return
        view = self.view()
        palette = view.palette()
        palette.setColor(QPalette.ColorRole.Accent, QColor(STATUS_COLORS[status]))
        view.setPalette(palette)


class TitleSuggestions(QObject):
    """Shows Open Library books under the Title box while typing; picking one fills author and genre."""

    def __init__(self, title, author, genre):
        super().__init__(title)
        self.title, self.author, self.genre = title, author, genre
        self.books = {}    # suggestion text -> {"title", "author", "genre"}
        self.reply = None  # the search currently waiting for an answer
        self.network = QNetworkAccessManager(self)  # downloads in the background, so the app never freezes
        # wait until the user pauses typing for 400 ms, instead of searching on every key
        self.timer = QTimer(self, singleShot=True, interval=400)
        self.timer.timeout.connect(self.search)
        self.model = QStringListModel(self)
        self.completer = QCompleter(self.model, self)
        # show every result as-is (Open Library already matched them to what was typed)
        self.completer.setCompletionMode(QCompleter.CompletionMode.UnfilteredPopupCompletion)
        self.completer.activated.connect(self.pick)
        self.completer.popup().setObjectName("titleSuggestions")  # styled in style.qss
        title.setCompleter(self.completer)
        title.textEdited.connect(self.timer.start)  # textEdited = only real typing, not setText()

    def search(self):
        text = self.title.text().strip()
        if len(text) < 3:
            return
        if self.reply:
            self.reply.abort()  # an older search is outdated now
        request = QNetworkRequest(QUrl(search_url(text)))
        request.setRawHeader(b"User-Agent", b"Chapterd/1.0 (personal book log)")  # Open Library asks for this
        self.reply = self.network.get(request)
        self.reply.finished.connect(lambda reply=self.reply: self.show_results(reply))

    def show_results(self, reply):
        reply.deleteLater()
        if reply is not self.reply or reply.error() != QNetworkReply.NetworkError.NoError:
            return  # outdated, or offline: just show no suggestions
        self.reply = None
        books = parse_results(bytes(reply.readAll()))
        self.books = {f"{b['title']} — {b['author']}" if b["author"] else b["title"]: b for b in books}
        self.model.setStringList(list(self.books))
        if self.books and self.title.hasFocus():
            self.completer.complete()

    def pick(self, text):
        book = self.books.get(text)
        if book:
            # wait one moment: the completer first puts the whole "Title — Author" text in the box
            QTimer.singleShot(0, lambda: self.fill(book))

    def fill(self, book):
        self.title.setText(book["title"])
        self.author.setText(book["author"])
        if book["genre"]:
            self.genre.setText(book["genre"])


class BookForm(QWidget):
    def __init__(self):
        super().__init__()
        form = QFormLayout(self)
        form.setContentsMargins(0, 0, 0, 0)
        self.title = QLineEdit()
        self.author = QLineEdit()
        self.genre = QLineEdit()
        # stop typing at the same limit the service checks
        for field in (self.title, self.author, self.genre):
            field.setMaxLength(MAX_TEXT_LENGTH)
        self.suggestions = TitleSuggestions(self.title, self.author, self.genre)
        self.status = StatusComboBox()
        self.rating = QComboBox()
        for rating in range(6):
            self.rating.addItem(stars(rating), rating)  # shows stars, stores the number 0-5
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
                self.status.currentText(), self.rating.currentData(), self.notes.toPlainText())

    def has_changes(self, book):
        """True if the form no longer matches the saved book (i.e. there are unsaved edits)."""
        original = (book["title"], book["author"], book["genre"],
                    book["status"], book["rating"], book["notes"])
        return self.values() != original

    def set_book(self, book):
        self.title.setText(book["title"])
        self.author.setText(book["author"])
        self.genre.setText(book["genre"])
        self.status.setCurrentText(book["status"])
        self.rating.setCurrentIndex(self.rating.findData(book["rating"]))
        self.notes.setPlainText(book["notes"])

    def clear(self):
        for field in (self.title, self.author, self.genre):
            field.clear()
        self.status.setCurrentIndex(0)
        self.rating.setCurrentIndex(0)
        self.notes.clear()
