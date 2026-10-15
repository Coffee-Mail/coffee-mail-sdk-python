from collections.abc import Callable
from typing import Any

import httpx
import pytest

from coffeemail import AsyncCoffeeMail, CoffeeMail, ValidationError
from coffeemail.core.i18n import Locale

Call = Callable[[CoffeeMail], Any]
INVALID_INPUTS: dict[str, Call] = {
    "contatos-sem-email": lambda c: c.audiences.contacts.bulk_add("a1", [{"first_name": "Ana"}]),
    "atalho-de-contatos": lambda c: c.audiences.bulk_add_contacts("a1", [{"email": 123}]),
    "supressao-com-motivo-invalido": lambda c: c.suppressions.bulk_create(
        [{"email": "x@y.com", "reason": "spam"}]
    ),
    "variavel-de-template-sem-nome": lambda c: c.templates.create(
        "t", "<p/>", variables=[{"type": "string"}]
    ),
    "variavel-na-atualizacao": lambda c: c.templates.update("t1", variables=[{"type": "x"}]),
    "destinatario-invalido": lambda c: c.emails.send({"from": "a@b.com", "to": 42, "subject": "x"}),
    "anexo-sem-nome": lambda c: c.emails.send(
        {"from": "a@b.com", "to": "c@d.com", "subject": "x", "attachments": [{"content": "YQ=="}]}
    ),
    "lote-com-destinatario-invalido": lambda c: c.emails.send_batch(
        [{"from": "a@b.com", "to": 42, "subject": "x"}]
    ),
}


def _client(captured: list[httpx.Request], locale: Locale = "pt-BR") -> CoffeeMail:
    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(200, json={})

    return CoffeeMail(
        "cm_test_x", locale=locale, http_client=httpx.Client(transport=httpx.MockTransport(handler))
    )


@pytest.mark.parametrize("name", sorted(INVALID_INPUTS))
def test_malformed_input_returns_validation_error_without_calling_the_api(name: str) -> None:
    captured: list[httpx.Request] = []
    res = INVALID_INPUTS[name](_client(captured))
    assert captured == []
    assert res.data is None
    assert res.status_code == 0
    assert isinstance(res.error, ValidationError)
    assert res.error.code == "VALIDATION_ERROR"
    assert res.error.status_code == 0


def test_message_is_localized_and_details_keep_the_errors() -> None:
    pt = _client([]).audiences.contacts.bulk_add("a1", [{"first_name": "Ana"}]).error
    en = _client([], "en").audiences.contacts.bulk_add("a1", [{"first_name": "Ana"}]).error
    assert pt is not None
    assert en is not None
    assert pt.message.startswith("Dados de entrada inválidos: email")
    assert en.message.startswith("Invalid input: email")
    assert isinstance(pt.details["errors"], list)


def test_invalid_recipient_message_is_localized() -> None:
    payload = {"from": "a@b.com", "to": 42, "subject": "x"}
    pt = _client([]).emails.send(payload).error
    en = _client([], "en").emails.send(payload).error
    assert pt is not None
    assert en is not None
    assert pt.message.startswith("Destinatário inválido")
    assert en.message.startswith("Invalid recipient")


def test_valid_dict_attachment_is_serialized() -> None:
    captured: list[httpx.Request] = []
    _client(captured).emails.send(
        {
            "from": "a@b.com",
            "to": "c@d.com",
            "subject": "x",
            "attachments": [{"filename": "a.txt", "content": "YQ==", "contentType": "text/plain"}],
        }
    )
    assert b'"contentType":"text/plain"' in captured[0].content.replace(b" ", b"")


async def test_async_client_returns_the_same_validation_error() -> None:
    calls: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, json={})

    client = AsyncCoffeeMail(
        "cm_test_x", http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler))
    )
    results: list[Any] = [
        await client.audiences.contacts.bulk_add("a1", [{"first_name": "Ana"}]),
        await client.suppressions.bulk_create([{"email": "x@y.com", "reason": "spam"}]),
        await client.templates.create("t", "<p/>", variables=[{"type": "string"}]),
        await client.emails.send({"from": "a@b.com", "to": 42, "subject": "x"}),
        await client.emails.send_batch([{"from": "a@b.com", "to": 42, "subject": "x"}]),
    ]
    assert calls == []
    for res in results:
        assert isinstance(res.error, ValidationError)
        assert res.status_code == 0


def test_email_in_place_of_suppression_id_uses_status_zero() -> None:
    res = _client([]).suppressions.get("a@b.com")
    assert res.status_code == 0
    assert isinstance(res.error, ValidationError)
    assert res.error.status_code == 0
