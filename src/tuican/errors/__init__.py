class ValidationError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class UserNotFoundError(Exception):
    """Raised when a Telegram update contains no identifiable user."""

    def __init__(self, update):
        super().__init__("No user id found in update")
