import time
from collections.abc import Mapping
from typing import TypeVar

import httpx

from coffeemail.core.errors import (
    AuthenticationError,
    NetworkError,
    create_error_from_response,
)
from coffeemail.core.i18n import Locale, get_message
from coffeemail.core.types import ApiKeyIntrospection, CoffeeMailResponse

SDK_VERSION = "0.1.0"
DEFAULT_BASE_URL = "https://api.coffeemail.com.br"
DEFAULT_TIMEOUT_SECONDS = 10.0

T = TypeVar("T")


class BaseTransport:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        locale: Locale = "pt-BR",
    ) -> None:
        clean_key = (api_key or "").strip()
        if not clean_key:
            raise AuthenticationError(get_message("missing_api_key", locale))

        self.api_key = clean_key
        self.base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout
        self.locale = locale

    def get_headers(self, custom_headers: dict[str, str] | None = None) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Accept-Language": self.locale,
            "User-Agent": f"coffeemail-python/{SDK_VERSION}",
        }
        if custom_headers:
            headers.update(custom_headers)
        return headers


class HttpTransport(BaseTransport):
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        locale: Locale = "pt-BR",
        client: httpx.Client | None = None,
    ) -> None:
        super().__init__(api_key, base_url, timeout, locale)
        self.client = client or httpx.Client(timeout=self.timeout)
        self._cached_introspection: ApiKeyIntrospection | None = None
        self._introspection_expires_at: float = 0.0

    def request(
        self,
        method: str,
        path: str,
        params: Mapping[str, object] | None = None,
        json_data: Mapping[str, object] | None = None,
        headers: dict[str, str] | None = None,
    ) -> CoffeeMailResponse[dict[str, object]]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        req_headers = self.get_headers(headers)
        clean_params = (
            {k: str(v) for k, v in params.items() if v is not None} if params is not None else None
        )

        try:
            response = self.client.request(
                method=method,
                url=url,
                params=clean_params,
                json=json_data,
                headers=req_headers,
            )
        except httpx.TimeoutException as exc:
            err = NetworkError(
                get_message("timeout_error", self.locale), details={"original_error": str(exc)}
            )
            return CoffeeMailResponse(data=None, error=err, status_code=None)
        except httpx.RequestError as exc:
            err = NetworkError(
                get_message("network_error", self.locale), details={"original_error": str(exc)}
            )
            return CoffeeMailResponse(data=None, error=err, status_code=None)

        if not response.is_success:
            body: dict[str, object] = {"message": response.text}
            try:
                parsed_body = response.json()
                if isinstance(parsed_body, dict):
                    body = parsed_body
            except Exception:
                pass
            error = create_error_from_response(response.status_code, body)
            return CoffeeMailResponse(data=None, error=error, status_code=response.status_code)

        data: dict[str, object] = {}
        if response.content:
            try:
                parsed_data = response.json()
                if isinstance(parsed_data, dict):
                    data = parsed_data
            except Exception:
                data = {}

        return CoffeeMailResponse(data=data, error=None, status_code=response.status_code)

    def introspect(self, force_refresh: bool = False) -> CoffeeMailResponse[ApiKeyIntrospection]:
        now = time.time()
        if (
            not force_refresh
            and self._cached_introspection
            and now < self._introspection_expires_at
        ):
            return CoffeeMailResponse(data=self._cached_introspection, error=None, status_code=200)

        raw_response = self.request("GET", "/v1/product/auth/me/api-key")
        if raw_response.error or raw_response.data is None:
            return CoffeeMailResponse(
                data=None, error=raw_response.error, status_code=raw_response.status_code
            )

        introspection = ApiKeyIntrospection.model_validate(raw_response.data)
        self._cached_introspection = introspection
        self._introspection_expires_at = now + 300.0
        return CoffeeMailResponse(
            data=introspection, error=None, status_code=raw_response.status_code
        )

    def invalidate_introspection_cache(self) -> None:
        self._cached_introspection = None
        self._introspection_expires_at = 0.0


class AsyncHttpTransport(BaseTransport):
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        locale: Locale = "pt-BR",
        client: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(api_key, base_url, timeout, locale)
        self.client = client or httpx.AsyncClient(timeout=self.timeout)
        self._cached_introspection: ApiKeyIntrospection | None = None
        self._introspection_expires_at: float = 0.0

    async def request(
        self,
        method: str,
        path: str,
        params: Mapping[str, object] | None = None,
        json_data: Mapping[str, object] | None = None,
        headers: dict[str, str] | None = None,
    ) -> CoffeeMailResponse[dict[str, object]]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        req_headers = self.get_headers(headers)
        clean_params = (
            {k: str(v) for k, v in params.items() if v is not None} if params is not None else None
        )

        try:
            response = await self.client.request(
                method=method,
                url=url,
                params=clean_params,
                json=json_data,
                headers=req_headers,
            )
        except httpx.TimeoutException as exc:
            err = NetworkError(
                get_message("timeout_error", self.locale), details={"original_error": str(exc)}
            )
            return CoffeeMailResponse(data=None, error=err, status_code=None)
        except httpx.RequestError as exc:
            err = NetworkError(
                get_message("network_error", self.locale), details={"original_error": str(exc)}
            )
            return CoffeeMailResponse(data=None, error=err, status_code=None)

        if not response.is_success:
            body: dict[str, object] = {"message": response.text}
            try:
                parsed_body = response.json()
                if isinstance(parsed_body, dict):
                    body = parsed_body
            except Exception:
                pass
            error = create_error_from_response(response.status_code, body)
            return CoffeeMailResponse(data=None, error=error, status_code=response.status_code)

        data: dict[str, object] = {}
        if response.content:
            try:
                parsed_data = response.json()
                if isinstance(parsed_data, dict):
                    data = parsed_data
            except Exception:
                data = {}

        return CoffeeMailResponse(data=data, error=None, status_code=response.status_code)

    async def introspect(
        self, force_refresh: bool = False
    ) -> CoffeeMailResponse[ApiKeyIntrospection]:
        now = time.time()
        if (
            not force_refresh
            and self._cached_introspection
            and now < self._introspection_expires_at
        ):
            return CoffeeMailResponse(data=self._cached_introspection, error=None, status_code=200)

        raw_response = await self.request("GET", "/v1/product/auth/me/api-key")
        if raw_response.error or raw_response.data is None:
            return CoffeeMailResponse(
                data=None, error=raw_response.error, status_code=raw_response.status_code
            )

        introspection = ApiKeyIntrospection.model_validate(raw_response.data)
        self._cached_introspection = introspection
        self._introspection_expires_at = now + 300.0
        return CoffeeMailResponse(
            data=introspection, error=None, status_code=raw_response.status_code
        )

    def invalidate_introspection_cache(self) -> None:
        self._cached_introspection = None
        self._introspection_expires_at = 0.0
