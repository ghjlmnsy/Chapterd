from database.database import Database

# account rules: (the register form in view.py reads these too)
MIN_USERNAME_LENGTH = 3
MAX_USERNAME_LENGTH = 30
MIN_PASSWORD_LENGTH = 8


class AuthenticationError(Exception):
    pass


class AuthenticationService:
    def __init__(self, database: Database):
        self.database = database
        self.current_user = None

    def register(self, username: str, password: str, confirm: str) -> None:
        username = username.strip()  # ignore spaces typed before/after the name
        if len(username) < MIN_USERNAME_LENGTH:
            raise AuthenticationError(f"Username must be at least {MIN_USERNAME_LENGTH} characters.")
        if len(username) > MAX_USERNAME_LENGTH:
            raise AuthenticationError(f"Username must be at most {MAX_USERNAME_LENGTH} characters.")
        if len(password) < MIN_PASSWORD_LENGTH:
            raise AuthenticationError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
        if password != confirm:
            raise AuthenticationError("Passwords do not match.")
        if not self.database.register(username, password):
            raise AuthenticationError("That username is already taken.")

    def login(self, username: str, password: str) -> dict:
        user = self.database.login(username, password)
        if user is None:
            raise AuthenticationError("Invalid username or password.")
        self.current_user = user  # {"id": ..., "username": ...}
        return self.current_user

    def logout(self) -> None:
        self.current_user = None
