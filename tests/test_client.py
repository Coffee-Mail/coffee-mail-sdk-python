import inspect

import httpx
import pytest

from coffeemail import AsyncCoffeeMail, CoffeeMail
from coffeemail.core.errors import AuthenticationError


def test_missing_api_key_raises_authentication_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("COFFEEMAIL_API_KEY", raising=False)
    with pytest.raises(AuthenticationError) as exc_info:
        CoffeeMail()
    assert "Chave de API ausente" in str(exc_info.value)


def test_missing_api_key_async_raises_authentication_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("COFFEEMAIL_API_KEY", raising=False)
    with pytest.raises(AuthenticationError) as exc_info:
        AsyncCoffeeMail()
    assert "Chave de API ausente" in str(exc_info.value)


def test_client_init_with_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COFFEEMAIL_API_KEY", "cm_live_env_key")
    client = CoffeeMail()
    assert client._transport.api_key == "cm_live_env_key"


def test_client_init_with_explicit_key() -> None:
    client = CoffeeMail("cm_live_direct_key")
    assert client._transport.api_key == "cm_live_direct_key"


@pytest.mark.parametrize("client_class", [CoffeeMail, AsyncCoffeeMail])
def test_clients_do_not_accept_a_custom_api_host(client_class: type[object]) -> None:
    assert "base_url" not in inspect.signature(client_class).parameters


def test_requests_always_target_the_official_api_host() -> None:
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(200, json={"data": []})

    client = CoffeeMail(
        "cm_live_direct_key", http_client=httpx.Client(transport=httpx.MockTransport(handler))
    )
    client.emails.get_tags()

    assert str(captured[0].url).startswith("https://api.coffeemail.com.br/")


def test_response_envelope_unpacking() -> None:
    from coffeemail.core.types import CoffeeMailResponse

    res: CoffeeMailResponse[dict[str, str]] = CoffeeMailResponse(
        data={"id": "email_123"}, error=None
    )
    data, error = res
    assert data == {"id": "email_123"}
    assert error is None
    assert res.unwrap() == {"id": "email_123"}


def test_response_unwrap_raises_error() -> None:
    from coffeemail.core.errors import NotFoundError
    from coffeemail.core.types import CoffeeMailResponse

    res: CoffeeMailResponse[None] = CoffeeMailResponse(
        data=None, error=NotFoundError("Not found", status_code=404)
    )
    with pytest.raises(NotFoundError):
        res.unwrap()
