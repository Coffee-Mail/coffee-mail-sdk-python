import httpx
import pytest

from coffeemail import (
    AsyncCoffeeMail,
    AuthenticationError,
    CoffeeMail,
    CoffeeMailError,
    ConflictError,
    ForbiddenError,
    NetworkError,
    NotFoundError,
    PaymentRequiredError,
    PermissionDeniedError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from coffeemail.core.i18n import Locale


def _client(
    status: int,
    body: object = None,
    *,
    text: str | None = None,
    headers: dict[str, str] | None = None,
    locale: Locale = "pt-BR",
) -> CoffeeMail:
    def handler(_: httpx.Request) -> httpx.Response:
        if text is not None:
            return httpx.Response(status, text=text, headers=headers)
        return httpx.Response(status, json=body, headers=headers)

    return CoffeeMail(
        "cm_test_x",
        locale=locale,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )


API_ERROR = {
    "error": {
        "code": "API_SPECIFIC",
        "message": "falhou",
        "meta": {"issues": [1]},
        "details": {"campo": "to"},
    }
}


@pytest.mark.parametrize(
    ("status", "error_class", "code"),
    [
        (400, ValidationError, "VALIDATION_ERROR"),
        (401, AuthenticationError, "UNAUTHORIZED"),
        (402, PaymentRequiredError, "PAYMENT_REQUIRED"),
        (403, ForbiddenError, "FORBIDDEN"),
        (404, NotFoundError, "NOT_FOUND"),
        (409, ConflictError, "CONFLICT"),
        (429, RateLimitError, "RATE_LIMIT_EXCEEDED"),
        (500, ServerError, "INTERNAL_SERVER_ERROR"),
        (502, ServerError, "INTERNAL_SERVER_ERROR"),
        (503, ServerError, "INTERNAL_SERVER_ERROR"),
        (504, ServerError, "INTERNAL_SERVER_ERROR"),
    ],
)
def test_status_maps_to_canonical_error(
    status: int, error_class: type[CoffeeMailError], code: str
) -> None:
    res = _client(status, API_ERROR, headers={"x-request-id": "req_1"}).domains.list()
    error = res.error
    assert type(error) is error_class
    assert error.code == code
    assert error.api_code == "API_SPECIFIC"
    assert error.status_code == status
    assert error.message == "falhou"
    assert error.request_id == "req_1"
    assert error.details == {"issues": [1], "campo": "to"}
    assert res.data is None


def test_unknown_status_keeps_the_api_code_or_falls_back_to_api_error() -> None:
    error = (
        _client(422, {"error": {"code": "INVALID_FROM_DOMAIN", "message": "x"}})
        .domains.list()
        .error
    )
    assert type(error) is CoffeeMailError
    assert error.code == "INVALID_FROM_DOMAIN"
    assert _client(418, {}).domains.list().error.code == "API_ERROR"  # type: ignore[union-attr]


@pytest.mark.parametrize(
    ("status", "kwargs", "locale", "expected"),
    [
        (
            401,
            {"body": {"error": {"code": "UNAUTHENTICATED"}}},
            "pt-BR",
            "Ocorreu um erro inesperado",
        ),
        (429, {"body": {"error": {"code": "RATE_LIMIT_EXCEEDED"}}}, "en", "Rate limit exceeded"),
        (502, {"text": "<html>Bad Gateway</html>"}, "pt-BR", "<html>Bad Gateway</html>"),
        (503, {"text": ""}, "en", "An unexpected error"),
        (400, {"body": {"message": "raiz"}}, "pt-BR", "raiz"),
    ],
)
def test_missing_message_falls_back_to_local_catalog(
    status: int, kwargs: dict[str, object], locale: Locale, expected: str
) -> None:
    error = _client(status, locale=locale, **kwargs).domains.list().error  # type: ignore[arg-type]
    assert error is not None
    assert error.message.startswith(expected)


@pytest.mark.parametrize(
    ("header", "expected"), [("60", 60), (" 5 ", 5), ("abc", None), ("-1", None)]
)
def test_retry_after_is_parsed(header: str, expected: int | None) -> None:
    error = _client(429, {}, headers={"Retry-After": header}).domains.list().error
    assert isinstance(error, RateLimitError)
    assert error.retry_after_seconds == expected


def test_plan_quota_keeps_api_code_for_callers_to_tell_it_apart() -> None:
    error = _client(429, {"error": {"code": "PLAN_QUOTA_EXCEEDED"}}).domains.list().error
    assert isinstance(error, RateLimitError)
    assert error.api_code == "PLAN_QUOTA_EXCEEDED"


def test_broadcast_forbidden_becomes_permission_denied() -> None:
    error = _client(403, {"error": {"code": "FORBIDDEN"}}, locale="en").broadcasts.send("b1").error
    assert isinstance(error, PermissionDeniedError)
    assert isinstance(error, ForbiddenError)
    assert error.code == "PERMISSION_DENIED"
    assert error.api_code == "FORBIDDEN"
    assert error.required_permission == "full_access"
    assert error.details["operation"] == "broadcasts.send"
    assert "full_access (called by broadcasts.send)" in error.message
    assert type(_client(403, {}).domains.list().error) is ForbiddenError


def test_invalid_success_body_becomes_invalid_response() -> None:
    error = _client(200, text="nao-json").domains.list().error
    assert error is not None
    assert error.code == "INVALID_RESPONSE"
    shape_error = _client(200, {"id": 1}).audiences.get("a1").error
    assert shape_error is not None
    assert shape_error.code == "INVALID_RESPONSE"


def test_network_errors_and_timeouts_are_localized() -> None:
    def refused(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    def slow(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timeout", request=request)

    refused_client = CoffeeMail(
        "cm_test_x", http_client=httpx.Client(transport=httpx.MockTransport(refused))
    )
    slow_client = CoffeeMail(
        "cm_test_x",
        timeout=2.5,
        locale="en",
        http_client=httpx.Client(transport=httpx.MockTransport(slow)),
    )
    network = refused_client.domains.list().error
    timeout = slow_client.domains.list().error
    assert isinstance(network, NetworkError)
    assert network.code == "NETWORK_ERROR"
    assert "connection refused" in network.message
    assert isinstance(timeout, NetworkError)
    assert timeout.message == "The request timed out after 2500ms."


async def test_async_client_maps_errors_the_same_way() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"error": {"code": "EMAIL_NOT_FOUND", "message": "x"}})

    client = AsyncCoffeeMail(
        "cm_test_x", http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler))
    )
    res = await client.emails.get("e1")
    assert isinstance(res.error, NotFoundError)
    assert res.error.api_code == "EMAIL_NOT_FOUND"
