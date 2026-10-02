import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from database.database import Database
from features.authentication.service import AuthenticationService
from features.authentication.view import AuthenticationView
from features.books.service import STATUSES, BookService
from features.books.view import BookView


class ChapterdWindow(QDialog):
    def __init__(self, books, authentication):
        super().__init__()
        self.authentication = authentication
        self.logged_out = False

        self.setWindowTitle("Chapterd")
        # QDialog has no minimize/maximize buttons by default; give it normal window controls
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowMinMaxButtonsHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self.resize(900, 700)
        self.setObjectName("mainContent")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(14)

        header = QWidget()
        header.setObjectName("appHeader")
        header.setMinimumHeight(78)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(22, 14, 18, 14)
        header_layout.setSpacing(16)

        title_group = QVBoxLayout()
        title_group.setSpacing(2)
        title = QLabel("Chapterd")
        title.setObjectName("appTitle")
        username = authentication.current_user["username"]
        subtitle = QLabel(f"Welcome back, {username}! Log your reads.")
        subtitle.setObjectName("appSubtitle")
        title_group.addWidget(title)
        title_group.addWidget(subtitle)
        header_layout.addLayout(title_group, 1)

        logout_button = QPushButton("Log Out")
        logout_button.setObjectName("logoutButton")
        logout_button.setFixedHeight(36)
        logout_button.clicked.connect(self.logout)
        header_layout.addWidget(logout_button)
        layout.addWidget(header)

        layout.addWidget(BookView(books))

    def logout(self):
        if QMessageBox.question(
            self,
            "Log Out",
            "Are you sure you want to log out?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes:
            self.authentication.logout()
            self.logged_out = True
            self.close()


def main():
    database = Database()
    database.create_tables(STATUSES)

    app = QApplication(sys.argv)
    app.setStyleSheet(Path(__file__).with_name("style.qss").read_text(encoding="utf-8"))

    authentication = AuthenticationService(database)
    books = BookService(database, authentication)

    while True:
        login_dialog = AuthenticationView(authentication)
        if login_dialog.exec() != QDialog.DialogCode.Accepted:
            return 0

        window = ChapterdWindow(books, authentication)
        window.exec()
        if not window.logged_out:
            return 0


if __name__ == "__main__":
    raise SystemExit(main())
