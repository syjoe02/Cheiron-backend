from app.errors.error_code import ErrorCode
from app.errors.error_registry import get_status_and_message


class AppException(Exception):
    def __init__(self, code: ErrorCode) -> None:
        self.code = code
        self.status, self.message = get_status_and_message(code)
        super().__init__(self.message)
