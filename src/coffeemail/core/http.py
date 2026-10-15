import time
from collections.abc import Mapping, Sequence
from typing import TypeVar

import httpx

from coffeemail.core.errors import (
    CODE_INVALID_RESPONSE,
    FULL_ACCESS_PERMISSION,
    AuthenticationError,
    CoffeeMailError,
    ForbiddenError,
    NetworkError,
    PermissionDeniedError,
    create_error_from_response,
)
from coffeemail.core.i18n import Locale, get_message
from coffeemail.core.parsing import parse_model
from coffeemail.core.types import ApiKeyIntrospection, CoffeeMailResponse

SDK_VERSION = "0.2.0"
DEFAULT_BASE_URL = "https://api.coffeemail.com.br"
DEFAULT_TIMEOUT_SECONDS = 10.0
INTROSPECTION_TTL_SECONDS = 300.0
INTROSPECTION_PATH = "/v1/product/auth/me/api-key"
JSON_MEDIA_TYPE = "application/json"
HEADER_REQUEST_ID = "x-request-id"
HEADER_RETRY_AFTER = "retry-after"
HEADER_IDEMPOTENCY_KEY = "x-idempotency-key"
HEADER_SANDBOX = "x-coffeemail-sandbox"
SANDBOX_ENABLED = "true"
_MILLISECONDS = 1000
_FALLBACK_KEYS: dict[int, str] = {429: "rate_limit_exceeded"}

T = TypeVar("T")
JsonBody = Mapping[str, object] | Sequence[object]


def send_headers(idempotency_key: str | None, sandbox: bool) -> dict[str, str]:
    headers: dict[str, str] = {}
    if idempotency_key:
        headers[HEADER_IDEMPOTENCY_KEY] = idempotency_key
    if sandbox:
        headers[HEADER_SANDBOX] = SANDBOX_ENABLED
    return headers


class BaseTransport:
    def __init__(
        self,
        api_key: str | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        locale: Locale = "pt-BR",
    ) -> None:
        clean_key = (api_key or "").strip()
        if not clean_key:
            raise AuthenticationError(get_message("missing_api_key", locale))

        self.api_key = clean_key
        self.timeout = timeout
        self.locale = locale
        self._cached_introspection: ApiKeyIntrospection | None = None
        self._introspection_expires_at: float = 0.0

    def get_headers(
        self, custom_headers: Mapping[str, str] | None = None, has_body: bool = False
    ) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": JSON_MEDIA_TYPE,
            "Accept-Language": self.locale,
            "User-Agent": f"coffeemail-python/{SDK_VERSION}",
        }
        if has_body:
            headers["Content-Type"] = JSON_MEDIA_TYPE
        headers.update(custom_headers or {})
        return headers

    def _url(self, path: str) -> str:
        return f"{DEFAULT_BASE_URL}/{path.lstrip('/')}"

    @staticmethod
    def _clean_params(params: Mapping[str, object] | None) -> dict[str, str] | None:
        if params is None:
            return None
        return {k: _query_value(v) for k, v in params.items() if v is not None}

    def _network_error(self, exc: httpx.HTTPError) -> CoffeeMailResponse[object]:
        is_timeout = isinstance(exc, httpx.TimeoutException)
        message = (
            get_message(
                "request_timeout",
                self.locale,
                {"timeoutMs": str(int(self.timeout * _MILLISECONDS))},
            )
            if is_timeout
            else get_message("network_error", self.locale, {"details": str(exc)})
        )
        error = NetworkError(message, details={"original_error": str(exc)})
        return CoffeeMailResponse(data=None, error=error, status_code=None)

    def _to_response(
        self, response: httpx.Response, permission_operation: str | None
    ) -> CoffeeMailResponse[object]:
        if not response.is_success:
            error = self._api_error(response, permission_operation)
            return CoffeeMailResponse(data=None, error=error, status_code=response.status_code)
        if not response.content.strip():
            return CoffeeMailResponse(data={}, error=None, status_code=response.status_code)
        try:
            data: object = response.json()
        except ValueError:
            invalid = CoffeeMailError(
                get_message("invalid_json", self.locale),
                status_code=response.status_code,
                code=CODE_INVALID_RESPONSE,
                request_id=response.headers.get(HEADER_REQUEST_ID),
            )
            return CoffeeMailResponse(data=None, error=invalid, status_code=response.status_code)
        return CoffeeMailResponse(data=data, error=None, status_code=response.status_code)

    def _api_error(
        self, response: httpx.Response, permission_operation: str | None
    ) -> CoffeeMailError:
        body = _json_or_none(response)
        raw_text = response.text.strip()
        fallback_key = _FALLBACK_KEYS.get(response.status_code, "unexpected_error")
        fallback = (
            raw_text
            if raw_text and not isinstance(body, dict)
            else get_message(fallback_key, self.locale)
        )
        error = create_error_from_response(
            response.status_code,
            body,
            fallback_message=fallback,
            request_id=response.headers.get(HEADER_REQUEST_ID),
            retry_after=response.headers.get(HEADER_RETRY_AFTER),
        )
        return self._remap_permission(error, permission_operation)

    def _remap_permission(self, error: CoffeeMailError, operation: str | None) -> CoffeeMailError:
        if operation is None or type(error) is not ForbiddenError:
            return error
        permission = f"{FULL_ACCESS_PERMISSION} (called by {operation})"
        return PermissionDeniedError(
            get_message("permission_denied", self.locale, {"requiredPermission": permission}),
            status_code=error.status_code,
            details={**error.details, "operation": operation},
            api_code=error.api_code,
            request_id=error.request_id,
        )

    def _cached(self) -> ApiKeyIntrospection | None:
        if self._cached_introspection and time.time() < self._introspection_expires_at:
            return self._cached_introspection
        return None

    def _store(self, introspection: ApiKeyIntrospection) -> None:
        self._cached_introspection = introspection
        self._introspection_expires_at = time.time() + INTROSPECTION_TTL_SECONDS

    def invalidate_introspection_cache(self) -> None:
        self._cached_introspection = None
        self._introspection_expires_at = 0.0


def _json_or_none(response: httpx.Response) -> object:
    try:
        return response.json()
    except ValueError:
        return None


def _query_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _as_object(raw: CoffeeMailResponse[object]) -> CoffeeMailResponse[dict[str, object]]:
    if raw.error is not None:
        return CoffeeMailResponse(data=None, error=raw.error, status_code=raw.status_code)
    payload = raw.data if isinstance(raw.data, dict) else {}
    return CoffeeMailResponse(data=payload, error=None, status_code=raw.status_code)


def _as_list(raw: CoffeeMailResponse[object]) -> CoffeeMailResponse[list[object]]:
    if raw.error is not None:
        return CoffeeMailResponse(data=None, error=raw.error, status_code=raw.status_code)
    payload = raw.data if isinstance(raw.data, list) else []
    return CoffeeMailResponse(data=payload, error=None, status_code=raw.status_code)


def _introspection_result(
    raw: CoffeeMailResponse[dict[str, object]], locale: Locale
) -> CoffeeMailResponse[ApiKeyIntrospection]:
    return parse_model(raw, ApiKeyIntrospection, locale)


class HttpTransport(BaseTransport):
    def __init__(
        self,
        api_key: str | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        locale: Locale = "pt-BR",
        client: httpx.Client | None = None,
    ) -> None:
        super().__init__(api_key, timeout, locale)
        self.client = client or httpx.Client(timeout=self.timeout, follow_redirects=False)

    def request_list(
        self,
        method: str,
        path: str,
        json_data: Sequence[object] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> CoffeeMailResponse[list[object]]:
        """Variante para endpoints cujo corpo e/ou resposta são arrays (envio em lote)."""
        return _as_list(self._request_raw(method, path, json_data=json_data, headers=headers))

    def request(
        self,
        method: str,
        path: str,
        params: Mapping[str, object] | None = None,
        json_data: Mapping[str, object] | None = None,
        headers: Mapping[str, str] | None = None,
        permission_operation: str | None = None,
    ) -> CoffeeMailResponse[dict[str, object]]:
        raw = self._request_raw(
            method,
            path,
            params=params,
            json_data=json_data,
            headers=headers,
            permission_operation=permission_operation,
        )
        return _as_object(raw)

    def _request_raw(
        self,
        method: str,
        path: str,
        params: Mapping[str, object] | None = None,
        json_data: JsonBody | None = None,
        headers: Mapping[str, str] | None = None,
        permission_operation: str | None = None,
    ) -> CoffeeMailResponse[object]:
        try:
            response = self.client.request(
                method=method,
                url=self._url(path),
                params=self._clean_params(params),
                json=json_data,
                headers=self.get_headers(headers, has_body=json_data is not None),
            )
        except httpx.HTTPError as exc:
            return self._network_error(exc)
        return self._to_response(response, permission_operation)

    def introspect(self, force_refresh: bool = False) -> CoffeeMailResponse[ApiKeyIntrospection]:
        cached = None if force_refresh else self._cached()
        if cached is not None:
            return CoffeeMailResponse(data=cached, error=None, status_code=200)
        result = _introspection_result(self.request("GET", INTROSPECTION_PATH), self.locale)
        if result.data is not None:
            self._store(result.data)
        return result


class AsyncHttpTransport(BaseTransport):
    def __init__(
        self,
        api_key: str | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        locale: Locale = "pt-BR",
        client: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(api_key, timeout, locale)
        self.client = client or httpx.AsyncClient(timeout=self.timeout, follow_redirects=False)

    async def request_list(
        self,
        method: str,
        path: str,
        json_data: Sequence[object] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> CoffeeMailResponse[list[object]]:
        raw = await self._request_raw(method, path, json_data=json_data, headers=headers)
        return _as_list(raw)

    async def request(
        self,
        method: str,
        path: str,
        params: Mapping[str, object] | None = None,
        json_data: Mapping[str, object] | None = None,
        headers: Mapping[str, str] | None = None,
        permission_operation: str | None = None,
    ) -> CoffeeMailResponse[dict[str, object]]:
        raw = await self._request_raw(
            method,
            path,
            params=params,
            json_data=json_data,
            headers=headers,
            permission_operation=permission_operation,
        )
        return _as_object(raw)

    async def _request_raw(
        self,
        method: str,
        path: str,
        params: Mapping[str, object] | None = None,
        json_data: JsonBody | None = None,
        headers: Mapping[str, str] | None = None,
        permission_operation: str | None = None,
    ) -> CoffeeMailResponse[object]:
        try:
            response = await self.client.request(
                method=method,
                url=self._url(path),
                params=self._clean_params(params),
                json=json_data,
                headers=self.get_headers(headers, has_body=json_data is not None),
            )
        except httpx.HTTPError as exc:
            return self._network_error(exc)
        return self._to_response(response, permission_operation)

    async def introspect(
        self, force_refresh: bool = False
    ) -> CoffeeMailResponse[ApiKeyIntrospection]:
        cached = None if force_refresh else self._cached()
        if cached is not None:
            return CoffeeMailResponse(data=cached, error=None, status_code=200)
        result = _introspection_result(await self.request("GET", INTROSPECTION_PATH), self.locale)
        if result.data is not None:
            self._store(result.data)
        return result
