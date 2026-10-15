"""Valida toda requisição produzida pelo SDK contra o OpenAPI de produto (spec/product.json).

Falha se uma requisição sair do contrato (corpo, query, método ou rota) ou se alguma
operação do spec ficar sem método no SDK.
"""

import json
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx
import pytest
from openapi_core import OpenAPI
from openapi_core.datatypes import RequestParameters
from openapi_core.exceptions import OpenAPIError
from openapi_core.validation.request.exceptions import MissingRequiredRequestBody
from werkzeug.datastructures import Headers, ImmutableMultiDict

from coffeemail import CoffeeMail, ContactInput, EmailParticipant, SendEmailPayload

SPEC_PATH = Path(__file__).resolve().parent.parent / "spec" / "product.json"
API_HOST = "https://api.coffeemail.com.br"
UUID_A = "6f1c2a7e-3b4d-4e5f-8a9b-0c1d2e3f4a5b"
UUID_B = "7a2d3b8f-4c5e-4f60-9b0c-1d2e3f4a5b6c"
BROWSER_ONLY = {("GET", "/v1/product/auth/csrf")}
OPTIONAL_BODY_ROUTES = {
    ("DELETE", "/v1/product/domains/{id}"): (
        "o spec marca o corpo de reautenticação como obrigatório, mas a API só o exige "
        "em sessões do dashboard"
    ),
}
LIST_RESPONSES = {"/v1/product/emails/batch"}


class HttpxOpenAPIRequest:
    def __init__(self, request: httpx.Request) -> None:
        self._request = request
        self.parameters = RequestParameters(
            query=ImmutableMultiDict(list(request.url.params.multi_items())),
            header=Headers(dict(request.headers)),
            cookie=ImmutableMultiDict(),
        )

    @property
    def host_url(self) -> str:
        return API_HOST

    @property
    def path(self) -> str:
        return self._request.url.path

    @property
    def method(self) -> str:
        return self._request.method.lower()

    @property
    def body(self) -> bytes | None:
        return self._request.content or None

    @property
    def content_type(self) -> str:
        return str(self._request.headers.get("content-type", ""))


def _load_spec() -> dict[str, Any]:
    spec: dict[str, Any] = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    spec["servers"] = [{"url": API_HOST}]
    return spec


SPEC = _load_spec()
OPENAPI = OpenAPI.from_dict(SPEC)


def _spec_operations() -> set[tuple[str, str]]:
    methods = {"get", "post", "put", "patch", "delete"}
    return {
        (method.upper(), path)
        for path, item in SPEC["paths"].items()
        for method in item
        if method in methods
    } - BROWSER_ONLY


def _template_for(method: str, path: str) -> tuple[str, str] | None:
    candidates = sorted(_spec_operations(), key=lambda op: op[1].count("{"))
    for spec_method, template in candidates:
        pattern = "^" + re.sub(r"\{[^}]+\}", "[^/]+", template) + "$"
        if spec_method == method and re.match(pattern, path):
            return spec_method, template
    return None


def validate(request: httpx.Request) -> tuple[str, str]:
    operation = _template_for(request.method, request.url.path)
    assert operation is not None, f"{request.method} {request.url.path} não existe no spec"
    try:
        OPENAPI.validate_request(HttpxOpenAPIRequest(request))
    except MissingRequiredRequestBody:
        assert operation in OPTIONAL_BODY_ROUTES, f"{operation} exige corpo"
    return operation


def _client(captured: list[httpx.Request]) -> CoffeeMail:
    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        body: object = [] if request.url.path in LIST_RESPONSES else {}
        return httpx.Response(200, json=body)

    return CoffeeMail(
        "cm_test_contract", http_client=httpx.Client(transport=httpx.MockTransport(handler))
    )


Call = Callable[[CoffeeMail], object]

EMAIL = SendEmailPayload(
    from_address=EmailParticipant(email="no-reply@exemplo.com.br", name="Exemplo"),
    to=["cliente@gmail.com"],
    subject="Olá",
    html="<p>Olá</p>",
    tags=[{"name": "fluxo", "value": "boas-vindas"}],  # type: ignore[list-item]
    email_type="transactional",
    suppression_category="marketing",
    metadata={"pedido": 42},
    scheduled_at="2026-10-20T12:00:00Z",
    idempotency_key="pedido-42",
    sandbox=True,
)

CALLS: dict[str, Call] = {
    "introspect": lambda c: c.introspect(force_refresh=True),
    "emails.send": lambda c: c.emails.send(EMAIL),
    "emails.send_batch": lambda c: c.emails.send_batch([EMAIL]),
    "emails.list": lambda c: c.emails.list(
        limit=10, status="delivered", tag="fluxo", from_date="2026-10-01T00:00:00Z"
    ),
    "emails.get": lambda c: c.emails.get(UUID_A),
    "emails.get_events": lambda c: c.emails.get_events(UUID_A),
    "emails.get_tags": lambda c: c.emails.get_tags(),
    "emails.cancel": lambda c: c.emails.cancel(UUID_A),
    "emails.resend": lambda c: c.emails.resend(UUID_A),
    "domains.create": lambda c: c.domains.create("exemplo.com.br"),
    "domains.list": lambda c: c.domains.list(),
    "domains.get": lambda c: c.domains.get(UUID_A),
    "domains.verify": lambda c: c.domains.verify(UUID_A),
    "domains.delete": lambda c: c.domains.delete(UUID_A),
    "domains.get_health": lambda c: c.domains.get_health(UUID_A),
    "domains.get_warmup_status": lambda c: c.domains.get_warmup_status(UUID_A),
    "templates.create": lambda c: c.templates.create(
        "Boas-vindas",
        "<p>{{nome}}</p>",
        subject="Oi",
        format="html",
        variables=[{"name": "nome", "fallbackValue": "cliente"}],
        source_locale="pt-BR",
    ),
    "templates.list": lambda c: c.templates.list(),
    "templates.get": lambda c: c.templates.get(UUID_A),
    "templates.update": lambda c: c.templates.update(UUID_A, name="Novo", is_active=False),
    "templates.delete": lambda c: c.templates.delete(UUID_A),
    "templates.preview": lambda c: c.templates.preview("<p>x</p>", variables={"nome": "Ana"}),
    "templates.format": lambda c: c.templates.format("<p>x</p>", format="html"),
    "templates.test_render": lambda c: c.templates.test_render("<p>x</p>"),
    "templates.test_send": lambda c: c.templates.test_send(
        UUID_A, "teste@gmail.com", from_email="no-reply@exemplo.com.br"
    ),
    "audiences.create": lambda c: c.audiences.create("Clientes", description="Todos"),
    "audiences.list": lambda c: c.audiences.list(limit=20, offset=40),
    "audiences.get": lambda c: c.audiences.get(UUID_A),
    "audiences.update": lambda c: c.audiences.update(UUID_A, active=False),
    "audiences.delete": lambda c: c.audiences.delete(UUID_A),
    "contacts.create": lambda c: c.audiences.contacts.create(
        UUID_A, "ana@gmail.com", first_name="Ana", metadata={"plano": "pro"}
    ),
    "contacts.list": lambda c: c.audiences.contacts.list(UUID_A, limit=10, offset=0),
    "contacts.bulk_add": lambda c: c.audiences.contacts.bulk_add(
        UUID_A,
        [ContactInput(email="ana@gmail.com"), {"email": "bia@gmail.com", "firstName": "Bia"}],
    ),
    "contacts.update": lambda c: c.audiences.contacts.update(UUID_A, UUID_B, last_name="Silva"),
    "contacts.delete": lambda c: c.audiences.contacts.delete(UUID_A, UUID_B),
    "broadcasts.create": lambda c: c.broadcasts.create(
        audience_id=UUID_A, from_email="news@exemplo.com.br", template_id=UUID_B
    ),
    "broadcasts.list": lambda c: c.broadcasts.list(limit=5, status="sent"),
    "broadcasts.get": lambda c: c.broadcasts.get(UUID_A),
    "broadcasts.send": lambda c: c.broadcasts.send(UUID_A),
    "broadcasts.test_send": lambda c: c.broadcasts.test_send(UUID_A, "teste@gmail.com"),
    "broadcasts.cancel": lambda c: c.broadcasts.cancel(UUID_A),
    "senders.create": lambda c: c.senders.create("ana@exemplo.com.br", "Ana"),
    "senders.create_sem_nome": lambda c: c.senders.create("ana@exemplo.com.br"),
    "senders.list": lambda c: c.senders.list(),
    "senders.verify": lambda c: c.senders.verify(UUID_A),
    "senders.delete": lambda c: c.senders.delete(UUID_A),
    "suppressions.create": lambda c: c.suppressions.create("x@gmail.com", "bounce"),
    "suppressions.list": lambda c: c.suppressions.list(limit=50, category="bounce"),
    "suppressions.get": lambda c: c.suppressions.get(UUID_A),
    "suppressions.delete": lambda c: c.suppressions.delete(UUID_A),
    "suppressions.reactivate": lambda c: c.suppressions.reactivate(UUID_A),
    "suppressions.bulk_create": lambda c: c.suppressions.bulk_create([{"email": "x@gmail.com"}]),
    "webhooks.create": lambda c: c.webhooks.create(
        "https://exemplo.com.br/hook", ["email.delivered"], description="principal"
    ),
    "webhooks.list": lambda c: c.webhooks.list(status="active"),
    "webhooks.get": lambda c: c.webhooks.get(UUID_A),
    "webhooks.update": lambda c: c.webhooks.update(UUID_A, description="novo"),
    "webhooks.toggle": lambda c: c.webhooks.toggle(UUID_A, enabled=False),
    "webhooks.delete": lambda c: c.webhooks.delete(UUID_A),
    "webhooks.rotate_secret": lambda c: c.webhooks.rotate_secret(UUID_A),
    "webhooks.list_deliveries": lambda c: c.webhooks.list_deliveries(
        UUID_A, status="failed", limit=5
    ),
    "webhooks.test": lambda c: c.webhooks.test(UUID_A),
    "stats.get": lambda c: c.stats.get(
        start_date="2026-10-01", end_date="2026-10-14", granularity="day", email_type="all"
    ),
}


@pytest.mark.parametrize("name", sorted(CALLS))
def test_every_request_matches_the_spec(name: str) -> None:
    captured: list[httpx.Request] = []
    CALLS[name](_client(captured))
    assert captured, f"{name} não fez requisição"
    validate(captured[-1])


def test_every_spec_operation_has_a_method() -> None:
    covered: set[tuple[str, str]] = set()
    for call in CALLS.values():
        captured: list[httpx.Request] = []
        call(_client(captured))
        covered.update(validate(request) for request in captured)
    missing = _spec_operations() - covered
    assert not missing, f"operações do spec sem método no SDK: {sorted(missing)}"


def _request(method: str, path: str, body: object | None = None) -> httpx.Request:
    content = json.dumps(body).encode() if body is not None else None
    headers = {"content-type": "application/json"} if body is not None else {}
    return httpx.Request(method, API_HOST + path, content=content, headers=headers)


@pytest.mark.parametrize(
    "request_",
    [
        _request("POST", "/v1/product/emails", {"from": {"email": "a@b.com"}}),
        _request("PATCH", f"/v1/product/webhooks/{UUID_A}", {"status": "disabled"}),
        _request("POST", "/v1/product/suppressions", {"email": "nao-e-email"}),
        _request(
            "POST", f"/v1/product/audiences/{UUID_A}/contacts", {"email": "a@b.com", "name": "x"}
        ),
    ],
    ids=["campo-obrigatorio", "enum-invalido", "email-malformado", "campo-desconhecido"],
)
def test_contract_check_rejects_requests_outside_the_spec(request_: httpx.Request) -> None:
    with pytest.raises(OpenAPIError):
        OPENAPI.validate_request(HttpxOpenAPIRequest(request_))


def test_contract_check_rejects_unknown_routes() -> None:
    assert _template_for("DELETE", f"/v1/product/broadcasts/{UUID_A}") is None
