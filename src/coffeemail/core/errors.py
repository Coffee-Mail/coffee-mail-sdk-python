class CoffeeMailError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        code: str | None = None,
        details: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details or {}

    def __str__(self) -> str:
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message


class AuthenticationError(CoffeeMailError):
    pass


class PermissionDeniedError(CoffeeMailError):
    pass


class NotFoundError(CoffeeMailError):
    pass


class ValidationError(CoffeeMailError):
    pass


class ConflictError(CoffeeMailError):
    pass


class RateLimitError(CoffeeMailError):
    pass


class ServerError(CoffeeMailError):
    pass


class NetworkError(CoffeeMailError):
    pass


def create_error_from_response(
    status_code: int,
    body: dict[str, object] | None = None,
    default_message: str | None = None,
) -> CoffeeMailError:
    data = body or {}
    message = str(
        data.get("message") or data.get("error") or default_message or f"HTTP Error {status_code}"
    )
    code = data.get("code")
    str_code = str(code) if code else None
    details = data.get("details")
    details_dict = details if isinstance(details, dict) else {}

    if status_code == 401:
        return AuthenticationError(
            message, status_code=status_code, code=str_code, details=details_dict
        )
    if status_code == 403:
        return PermissionDeniedError(
            message, status_code=status_code, code=str_code, details=details_dict
        )
    if status_code == 404:
        return NotFoundError(message, status_code=status_code, code=str_code, details=details_dict)
    if status_code in (400, 422):
        return ValidationError(
            message, status_code=status_code, code=str_code, details=details_dict
        )
    if status_code == 409:
        return ConflictError(message, status_code=status_code, code=str_code, details=details_dict)
    if status_code == 429:
        return RateLimitError(message, status_code=status_code, code=str_code, details=details_dict)
    if status_code >= 500:
        return ServerError(message, status_code=status_code, code=str_code, details=details_dict)

    return CoffeeMailError(message, status_code=status_code, code=str_code, details=details_dict)
