from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLabel, QLineEdit, QPushButton, QTabWidget, QVBoxLayout, QWidget,
)

from features.authentication.service import (
    MAX_USERNAME_LENGTH, MIN_PASSWORD_LENGTH, MIN_USERNAME_LENGTH, AuthenticationError,
)


class AuthenticationView(QDialog):
    def __init__(self, authentication):
        super().__init__()
        self.authentication = authentication
        self.setWindowTitle("Chapterd - Log In")
        self.setObjectName("authDialog")
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)

        title = QLabel("Chapterd")
        title.setObjectName("appTitle")
        subtitle = QLabel("Your personal book log")
        subtitle.setObjectName("appSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        self.message = QLabel("")
        self.message.setObjectName("messageLabel")
        self.message.setWordWrap(True)

        tabs = QTabWidget()
        tabs.addTab(self._login_tab(), "Log In")
        tabs.addTab(self._register_tab(), "Register")
        tabs.currentChanged.connect(lambda _: self.message.setText(""))
        layout.addWidget(tabs)
        layout.addWidget(self.message)

    def _login_tab(self):
        page = QWidget()
        form = QFormLayout(page)
        form.setContentsMargins(20, 20, 20, 20)  
        self.login_username = QLineEdit()
        self.login_password = QLineEdit()
        self.login_password.setEchoMode(QLineEdit.EchoMode.Password)
        # pressing Enter in either box logs in
        self.login_username.returnPressed.connect(self.handle_login)
        self.login_password.returnPressed.connect(self.handle_login)
        button = QPushButton("Log In")
        button.setObjectName("primaryButton")
        button.clicked.connect(self.handle_login)
        form.addRow("Username", self.login_username)
        form.addRow("Password", self.login_password)
        form.addRow(button)
        return page

    def _register_tab(self):
        page = QWidget()
        form = QFormLayout(page)
        form.setContentsMargins(20, 20, 20, 20)
        self.reg_username = QLineEdit()
        self.reg_password = QLineEdit()
        self.reg_confirm = QLineEdit()
        self.reg_username.setMaxLength(MAX_USERNAME_LENGTH)
        self.reg_username.setPlaceholderText(f"{MIN_USERNAME_LENGTH}-{MAX_USERNAME_LENGTH} characters")
        self.reg_password.setPlaceholderText(f"At least {MIN_PASSWORD_LENGTH} characters")
        for field in (self.reg_password, self.reg_confirm):
            field.setEchoMode(QLineEdit.EchoMode.Password)
        # pressing Enter in any register box submits the form
        for field in (self.reg_username, self.reg_password, self.reg_confirm):
            field.returnPressed.connect(self.handle_register)
        button = QPushButton("Create Account")
        button.setObjectName("primaryButton")
        button.clicked.connect(self.handle_register)
        form.addRow("Username", self.reg_username)
        form.addRow("Password", self.reg_password)
        form.addRow("Confirm", self.reg_confirm)
        form.addRow(button)
        return page

    def handle_login(self):
        try:
            self.authentication.login(self.login_username.text(), self.login_password.text())
        except AuthenticationError as error:
            self.message.setText(str(error))
            # clear the wrong password so the user can retype it straight away
            self.login_password.clear()
            self.login_password.setFocus()
            return
        self.accept()

    def handle_register(self):
        try:
            self.authentication.register(
                self.reg_username.text(), self.reg_password.text(), self.reg_confirm.text()
            )
        except AuthenticationError as error:
            self.message.setText(str(error))
            return
        self.message.setText("Account created! You can log in now.")
        self.login_username.setText(self.reg_username.text())
        self.reg_password.clear()
        self.reg_confirm.clear()
