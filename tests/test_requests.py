import json

import httpx
import pytest

from coffeemail import AsyncCoffeeMail, CoffeeMail, SendEmailPayload
from coffeemail.core.http import SDK_VERSION

_EMPTY: dict[str, object] = {}


def _client(captured: list[httpx.Request], body: object = _EMPTY, status: int = 200) -> CoffeeMail:
    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(status, json=body)

    return CoffeeMail("cm_test_x", http_client=httpx.Client(transport=httpx.MockTransport(handler)))


def _body(request: httpx.Request) -> dict[str, object]:
    loaded: dict[str, object] = json.loads(request.content)
    return loaded


def test_standard_headers_and_content_type_only_with_body() -> None:
    captured: list[httpx.Request] = []
    client = _client(captured)
    client.domains.list()
    client.domains.create("exemplo.com.br")
    get, post = captured
    assert get.headers["authorization"] == "Bearer cm_test_x"
    assert get.headers["user-agent"] == f"coffeemail-python/{SDK_VERSION}"
    assert get.headers["accept-language"] == "pt-BR"
    assert "content-type" not in get.headers
    assert post.headers["content-type"] == "application/json"


def test_send_moves_idempotency_and_sandbox_to_headers() -> None:
    captured: list[httpx.Request] = []
    _client(captured, {"id": "e1", "status": "queued"}, 202).emails.send(
        SendEmailPayload(
            from_address="a@b.com",
            to="c@d.com",
            subject="x",
            text="x",
            idempotency_key="pedido-1",
            sandbox=True,
        )
    )
    request = captured[0]
    assert request.headers["x-idempotency-key"] == "pedido-1"
    assert request.headers["x-coffeemail-sandbox"] == "true"
    assert "idempotencyKey" not in _body(request)


def test_send_without_key_sends_no_idempotency_header() -> None:
    captured: list[httpx.Request] = []
    _client(captured, {"id": "e1", "status": "queued"}).emails.send(
        {"from": "a@b.com", "to": "c@d.com", "subject": "x", "text": "x"}
    )
    assert "x-idempotency-key" not in captured[0].headers
    assert "x-coffeemail-sandbox" not in captured[0].headers


def test_batch_uses_one_set_of_headers() -> None:
    captured: list[httpx.Request] = []
    _client(captured, []).emails.send_batch(
        [
            {"from": "a@b.com", "to": "c@d.com", "subject": "x", "idempotencyKey": "k1"},
            {
                "from": "a@b.com",
                "to": "e@f.com",
                "subject": "y",
                "idempotencyKey": "k2",
                "sandbox": True,
            },
        ]
    )
    assert captured[0].headers["x-idempotency-key"] == "k2"
    assert captured[0].headers["x-coffeemail-sandbox"] == "true"


def test_contacts_use_first_and_last_name() -> None:
    captured: list[httpx.Request] = []
    client = _client(captured, {"id": "c1", "email": "ana@gmail.com", "createdAt": "2026-10-14"})
    res = client.audiences.contacts.create(
        "a1", "ana@gmail.com", first_name="Ana", last_name="Lima"
    )
    assert _body(captured[0]) == {"email": "ana@gmail.com", "firstName": "Ana", "lastName": "Lima"}
    assert res.data is not None
    assert res.data.email == "ana@gmail.com"
    with pytest.raises(TypeError):
        client.audiences.contacts.create("a1", "ana@gmail.com", name="Ana")  # type: ignore[call-arg]


def test_lists_by_offset_send_limit_and_offset() -> None:
    captured: list[httpx.Request] = []
    client = _client(captured, {"audiences": [], "total": 0})
    client.audiences.list(limit=10, offset=20)
    assert dict(captured[0].url.params) == {"limit": "10", "offset": "20"}


def test_broadcast_create_requires_from_email() -> None:
    captured: list[httpx.Request] = []
    client = _client(
        captured, {"id": "b1", "audienceId": "a1", "status": "draft", "createdAt": "x"}
    )
    res = client.broadcasts.create(audience_id="a1", from_email="news@x.com", template_id="t1")
    assert _body(captured[0]) == {"audienceId": "a1", "fromEmail": "news@x.com", "templateId": "t1"}
    assert res.data is not None
    assert res.data.status == "draft"
    with pytest.raises(TypeError):
        client.broadcasts.create(audience_id="a1")  # type: ignore[call-arg]
    assert not hasattr(client.broadcasts, "delete")


def test_stats_use_contract_query_names() -> None:
    captured: list[httpx.Request] = []
    _client(captured).stats.get(start_date="2026-10-01", end_date="2026-10-14", period="last7d")
    assert dict(captured[0].url.params) == {
        "startDate": "2026-10-01",
        "endDate": "2026-10-14",
        "period": "last7d",
    }


def test_webhook_update_uses_put_and_toggle_uses_patch() -> None:
    captured: list[httpx.Request] = []
    client = _client(captured, {"id": "w1", "url": "u", "status": "paused", "createdAt": "x"})
    client.webhooks.update("w1", description="novo")
    client.webhooks.toggle("w1", enabled=False)
    assert captured[0].method == "PUT"
    assert _body(captured[0]) == {"description": "novo"}
    assert captured[1].method == "PATCH"
    assert _body(captured[1]) == {"status": "paused"}


def test_preview_by_id_renders_the_stored_template() -> None:
    responses = iter(
        [
            {
                "id": "t1",
                "name": "n",
                "html": "<p>{{nome}}</p>",
                "format": "react",
                "createdAt": "x",
            },
            {"html": "<p>Ana</p>", "text": "Ana"},
        ]
    )
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(200, json=next(responses))

    client = CoffeeMail(
        "cm_test_x", http_client=httpx.Client(transport=httpx.MockTransport(handler))
    )
    res = client.templates.preview_by_id("t1", {"nome": "Ana"})
    assert res.data is not None
    assert res.data.text == "Ana"
    assert _body(captured[1]) == {
        "html": "<p>{{nome}}</p>",
        "format": "react",
        "variables": {"nome": "Ana"},
    }


def test_introspection_is_cached_until_forced() -> None:
    captured: list[httpx.Request] = []
    client = _client(
        captured, {"id": "k1", "name": "prod", "organisationId": "o1", "scopes": ["full_access"]}
    )
    first = client.introspect()
    client.introspect()
    client.introspect(force_refresh=True)
    assert first.data is not None
    assert first.data.organisation_id == "o1"
    assert len(captured) == 2
    client.invalidate_introspection_cache()
    client.introspect()
    assert len(captured) == 3


async def test_async_client_sends_the_same_contract() -> None:
    captured: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(200, json={"contacts": [], "total": 0})

    client = AsyncCoffeeMail(
        "cm_test_x", http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler))
    )
    res = await client.audiences.contacts.list("a1", limit=5, offset=10)
    assert res.data is not None
    assert dict(captured[0].url.params) == {"limit": "5", "offset": "10"}


def test_domain_responses_follow_the_spec() -> None:
    created_body = {
        "id": "d1",
        "name": "x.com",
        "status": "pending",
        "dkimRecordsToPublish": [
            {"type": "TXT", "host": "h", "value": "v", "isInfrastructure": True}
        ],
    }
    verify_body = {
        "id": "d1",
        "name": "x.com",
        "status": "verified",
        "checks": {
            "spf": {"ok": True, "resolution": "found", "expected": "e", "got": None, "matches": []}
        },
        "requiredChecks": ["spf"],
    }
    created = _client([], created_body).domains.create("x.com")
    verified = _client([], verify_body).domains.verify("d1")
    assert created.data is not None
    assert created.data.dkim_records_to_publish[0].is_infrastructure is True
    assert verified.data is not None
    assert verified.data.required_checks == ["spf"]


def test_warmup_is_none_without_warmup_and_typed_otherwise() -> None:
    assert _client([], None).domains.get_warmup_status("d1").data is None
    warmup = _client([], {"domainId": "d1", "currentDay": 3}).domains.get_warmup_status("d1")
    assert warmup.data is not None
    assert warmup.data.current_day == 3


def test_senders_are_typed() -> None:
    created_body = {
        "id": "s1",
        "email": "ana@x.com",
        "displayName": None,
        "verificationToken": "tok",
        "verifiedAt": None,
        "active": False,
        "createdAt": "2026-10-14",
    }
    captured: list[httpx.Request] = []
    created = _client(captured, created_body).senders.create("ana@x.com")
    assert _body(captured[0]) == {"email": "ana@x.com"}
    assert created.data is not None
    assert created.data.verification_token == "tok"
    listed = _client(
        [], {"senders": [{k: v for k, v in created_body.items() if k != "verificationToken"}]}
    )
    page = listed.senders.list()
    assert page.data is not None
    assert page.data.senders[0].email == "ana@x.com"
    verified = _client([], {"id": "s1", "email": "ana@x.com"}).senders.verify("tok")
    assert verified.data is not None
    assert verified.data.id == "s1"


async def test_async_senders_are_typed() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"senders": []})

    client = AsyncCoffeeMail(
        "cm_test_x", http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler))
    )
    res = await client.senders.list()
    assert res.data is not None
    assert res.data.senders == []


def test_created_sender_without_token_still_parses() -> None:
    body = {
        "id": "s2",
        "email": "vendas@x.com",
        "displayName": None,
        "verifiedAt": None,
        "active": True,
        "createdAt": "2026-10-15",
    }
    created = _client([], body).senders.create("vendas@x.com")
    assert created.data is not None
    assert created.data.verification_token is None


def test_resend_verification_hits_the_route_and_types_errors() -> None:
    captured: list[httpx.Request] = []
    ok = _client(captured, None, 204).senders.resend_verification("s1")
    assert ok.error is None
    assert captured[0].method == "POST"
    assert captured[0].url.path == "/v1/product/senders/s1/resend-verification"
    conflict = _client(
        [], {"error": {"code": "CONFLICT", "message": "sender is already verified"}}, 409
    ).senders.resend_verification("s1")
    assert conflict.error is not None
    missing = _client(
        [], {"error": {"code": "NOT_FOUND", "message": "sender"}}, 404
    ).senders.resend_verification("x")
    assert missing.error is not None
    assert missing.error.status_code == 404


def test_broadcast_create_sends_scheduled_at_and_get_parses_metrics() -> None:
    captured: list[httpx.Request] = []
    detail = {
        "id": "b1",
        "audienceId": "a1",
        "status": "scheduled",
        "scheduledAt": "2030-01-01T10:00:00.000Z",
        "createdAt": "2026-10-15",
    }
    _client(captured, detail, 201).broadcasts.create(
        audience_id="a1",
        from_email="news@acme.com",
        template_id="tpl-1",
        scheduled_at="2030-01-01T10:00:00.000Z",
    )
    assert _body(captured[0])["scheduledAt"] == "2030-01-01T10:00:00.000Z"
    with_metrics = {
        **detail,
        "status": "sent",
        "metrics": {
            "delivered": 9,
            "opened": 4,
            "clicked": 1,
            "bounced": 1,
            "failed": 0,
            "suppressed": 2,
        },
    }
    got = _client([], with_metrics).broadcasts.get("b1")
    assert got.data is not None
    assert got.data.metrics is not None
    assert got.data.metrics.delivered == 9


def test_contact_subscribed_flag() -> None:
    body = {
        "contacts": [
            {"id": "c1", "email": "a@x.com", "subscribed": False, "createdAt": "2026-10-15"},
            {"id": "c2", "email": "b@x.com", "createdAt": "2026-10-15"},
        ],
        "total": 2,
    }
    page = _client([], body).audiences.contacts.list("aud-1")
    assert page.data is not None
    assert [c.subscribed for c in page.data.contacts] == [False, True]
