import re
from collections.abc import Mapping

CODE_VALIDATION_ERROR = "VALIDATION_ERROR"
CODE_UNAUTHORIZED = "UNAUTHORIZED"
CODE_PAYMENT_REQUIRED = "PAYMENT_REQUIRED"
CODE_FORBIDDEN = "FORBIDDEN"
CODE_NOT_FOUND = "NOT_FOUND"
CODE_CONFLICT = "CONFLICT"
CODE_RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
CODE_INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
CODE_NETWORK_ERROR = "NETWORK_ERROR"
CODE_PERMISSION_DENIED = "PERMISSION_DENIED"
CODE_API_ERROR = "API_ERROR"
CODE_INVALID_RESPONSE = "INVALID_RESPONSE"

FULL_ACCESS_PERMISSION = "full_access"
_RETRY_AFTER_SECONDS = re.compile(r"^\d{1,18}$")


class CoffeeMailError(Exception):
    """Erro de toda operação do SDK.

    ``code`` é o código canônico, igual em todos os SDKs oficiais; ``api_code`` é o
    código original enviado pela API (ex.: ``PLAN_QUOTA_EXCEEDED``).
    """

    default_code = CODE_API_ERROR

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        code: str | None = None,
        details: dict[str, object] | None = None,
        api_code: str | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code or self.default_code
        self.details = details or {}
        self.api_code = api_code
        self.request_id = request_id

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


class ValidationError(CoffeeMailError):
    default_code = CODE_VALIDATION_ERROR


class AuthenticationError(CoffeeMailError):
    default_code = CODE_UNAUTHORIZED


class PaymentRequiredError(CoffeeMailError):
    default_code = CODE_PAYMENT_REQUIRED


class ForbiddenError(CoffeeMailError):
    default_code = CODE_FORBIDDEN


class PermissionDeniedError(ForbiddenError):
    """A chave não tem a permissão exigida pela operação (ex.: broadcasts exigem full_access)."""

    default_code = CODE_PERMISSION_DENIED

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        code: str | None = None,
        details: dict[str, object] | None = None,
        api_code: str | None = None,
        request_id: str | None = None,
        required_permission: str = FULL_ACCESS_PERMISSION,
    ) -> None:
        super().__init__(message, status_code, code, details, api_code, request_id)
        self.required_permission = required_permission


class NotFoundError(CoffeeMailError):
    default_code = CODE_NOT_FOUND


class ConflictError(CoffeeMailError):
    default_code = CODE_CONFLICT


class RateLimitError(CoffeeMailError):
    default_code = CODE_RATE_LIMIT_EXCEEDED

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        code: str | None = None,
        details: dict[str, object] | None = None,
        api_code: str | None = None,
        request_id: str | None = None,
        retry_after_seconds: int | None = None,
    ) -> None:
        super().__init__(message, status_code, code, details, api_code, request_id)
        self.retry_after_seconds = retry_after_seconds


class ServerError(CoffeeMailError):
    default_code = CODE_INTERNAL_SERVER_ERROR


class NetworkError(CoffeeMailError):
    default_code = CODE_NETWORK_ERROR


ERROR_CLASSES: dict[int, type[CoffeeMailError]] = {
    400: ValidationError,
    401: AuthenticationError,
    402: PaymentRequiredError,
    403: ForbiddenError,
    404: NotFoundError,
    409: ConflictError,
    429: RateLimitError,
    500: ServerError,
    502: ServerError,
    503: ServerError,
    504: ServerError,
}


def _as_dict(value: object) -> dict[str, object]:
    return {str(k): v for k, v in value.items()} if isinstance(value, Mapping) else {}


def _first_text(*candidates: object) -> str | None:
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate
    return None


def parse_retry_after(value: str | None) -> int | None:
    trimmed = (value or "").strip()
    if not _RETRY_AFTER_SECONDS.match(trimmed):
        return None
    return int(trimmed)


def create_error_from_response(
    status_code: int,
    body: object,
    *,
    fallback_message: str,
    request_id: str | None = None,
    retry_after: str | None = None,
) -> CoffeeMailError:
    """Mapeia uma resposta não-2xx para o erro tipado, por tabela de status.

    A API responde ``{"error": {"code", "message", "meta", "details"}}``; ``details``
    do SDK reúne ``meta`` e ``details``. Sem mensagem, usa ``fallback_message``.
    """
    root = _as_dict(body)
    error = _as_dict(root.get("error"))
    api_code = _first_text(error.get("code"))
    message = _first_text(error.get("message"), root.get("message")) or fallback_message
    details = {**_as_dict(error.get("meta")), **_as_dict(error.get("details"))}
    error_class = ERROR_CLASSES.get(status_code, CoffeeMailError)
    canonical = None if error_class is not CoffeeMailError else (api_code or CODE_API_ERROR)
    if error_class is RateLimitError:
        return RateLimitError(
            message,
            status_code=status_code,
            details=details,
            api_code=api_code,
            request_id=request_id,
            retry_after_seconds=parse_retry_after(retry_after),
        )
    return error_class(
        message,
        status_code=status_code,
        code=canonical,
        details=details,
        api_code=api_code,
        request_id=request_id,
    )
