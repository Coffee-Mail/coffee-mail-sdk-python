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
