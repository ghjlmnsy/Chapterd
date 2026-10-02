from database.database import Database


class AuthenticationError(Exception):
    pass


class AuthenticationService:
    def __init__(self, database: Database):
        self.database = database
        self.current_user = None

    def register(self, username: str, password: str, confirm: str) -> None:
        if len(username.strip()) < 3:
            raise AuthenticationError("Username must be at least 3 characters.")
        if len(password) < 4:
            raise AuthenticationError("Password must be at least 4 characters.")
        if password != confirm:
            raise AuthenticationError("Passwords do not match.")
        if not self.database.register(username, password):
            raise AuthenticationError("That username is already taken.")

    def login(self, username: str, password: str) -> dict:
        user_id = self.database.login(username, password)
        if user_id is None:
            raise AuthenticationError("Invalid username or password.")
        self.current_user = {"id": user_id, "username": username.strip()}
        return self.current_user

    def logout(self) -> None:
        self.current_user = None
