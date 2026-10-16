import json

import httpx
import pytest

from coffeemail import (
    AsyncCoffeeMail,
    CoffeeMail,
    ConflictError,
    NotFoundError,
    RateLimitError,
    SendEmailPayload,
    ValidationError,
)
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


_DNS_TXT = {"type": "TXT", "host": "cm2._domainkey.x.com", "value": "v=DKIM1; p=abc", "ttl": 3600}
_ROTATION = {
    "domainId": "d1",
    "selector": "cm2",
    "startedAt": "2026-10-15T10:00:00.000Z",
    "record": _DNS_TXT,
}
_TRACKING = {
    "host": "links.x.com",
    "target": "track.coffeemail.com.br",
    "verified": False,
    "verifiedAt": None,
    "record": {"type": "CNAME", "host": "links.x.com", "value": "track.coffeemail.com.br"},
}


def _error(code: str, status: int) -> tuple[dict[str, object], int]:
    return {"error": {"code": code, "message": code.lower()}}, status


def test_warmup_exposes_status_total_days_and_dates() -> None:
    body = {
        "domainId": "d1",
        "status": "completed",
        "currentDay": 30,
        "totalDays": 30,
        "dailyQuota": 0,
        "sentToday": 12,
        "remainingToday": 0,
        "quotaUsedPercent": 0,
        "lastSendDate": "2026-10-15",
        "startedAt": "2026-09-15T10:00:00.000Z",
        "completedAt": "2026-10-15T10:00:00.000Z",
    }
    warmup = _client([], body).domains.get_warmup_status("d1")
    assert warmup.data is not None
    assert warmup.data.status == "completed"
    assert warmup.data.total_days == 30
    assert warmup.data.started_at == "2026-09-15T10:00:00.000Z"
    assert warmup.data.completed_at == "2026-10-15T10:00:00.000Z"
    warming = _client([], {"domainId": "d1", "status": "warming", "completedAt": None})
    in_progress = warming.domains.get_warmup_status("d1")
    assert in_progress.data is not None
    assert in_progress.data.completed_at is None


def test_domain_detail_exposes_rotation_return_path_and_tracking() -> None:
    body = {
        "id": "d1",
        "name": "x.com",
        "status": "verified",
        "dkimRotation": _ROTATION,
        "returnPath": {
            **_TRACKING,
            "host": "bounces.x.com",
            "verified": True,
            "verifiedAt": "2026-10-15T10:00:00.000Z",
        },
        "trackingDomain": _TRACKING,
        "trackingDomainsAvailable": True,
    }
    detail = _client([], body).domains.get("d1")
    assert detail.data is not None
    assert detail.data.dkim_rotation is not None
    assert detail.data.dkim_rotation.selector == "cm2"
    assert detail.data.dkim_rotation.record.ttl == 3600
    assert detail.data.return_path is not None
    assert detail.data.return_path.verified is True
    assert detail.data.tracking_domain is not None
    assert detail.data.tracking_domain.record.type == "CNAME"
    assert detail.data.tracking_domains_available is True
    legacy = _client([], {"id": "d1", "name": "x.com", "status": "pending"}).domains.get("d1")
    assert legacy.data is not None
    assert legacy.data.dkim_rotation is None
    assert legacy.data.return_path is None
    assert legacy.data.tracking_domain is None
    assert legacy.data.tracking_domains_available is False


def test_rotate_dkim_hits_the_route_and_types_errors() -> None:
    captured: list[httpx.Request] = []
    rotation = _client(captured, _ROTATION).domains.rotate_dkim("d1")
    assert captured[0].method == "POST"
    assert captured[0].url.path == "/v1/product/domains/d1/dkim/rotate"
    assert captured[0].content == b""
    assert rotation.data is not None
    assert rotation.data.record.host == "cm2._domainkey.x.com"
    missing = _client([], *_error("DOMAIN_NOT_FOUND", 404)).domains.rotate_dkim("x")
    assert isinstance(missing.error, NotFoundError)
    assert missing.error.api_code == "DOMAIN_NOT_FOUND"
    pending = _client([], *_error("DOMAIN_NOT_VERIFIED", 409)).domains.rotate_dkim("d1")
    assert isinstance(pending.error, ConflictError)
    assert pending.error.api_code == "DOMAIN_NOT_VERIFIED"


def test_set_tracking_domain_sends_host_and_types_errors() -> None:
    captured: list[httpx.Request] = []
    status = _client(captured, _TRACKING).domains.set_tracking_domain("d1", " links.x.com ")
    assert captured[0].method == "PUT"
    assert captured[0].url.path == "/v1/product/domains/d1/tracking-domain"
    assert _body(captured[0]) == {"host": "links.x.com"}
    assert status.data is not None
    assert status.data.target == "track.coffeemail.com.br"
    assert status.data.verified_at is None
    invalid = _client([], *_error("INVALID_TRACKING_HOST", 400)).domains.set_tracking_domain(
        "d1", "outro.com"
    )
    assert isinstance(invalid.error, ValidationError)
    assert invalid.error.api_code == "INVALID_TRACKING_HOST"
    disabled = _client([], *_error("TRACKING_DOMAINS_DISABLED", 409)).domains.set_tracking_domain(
        "d1", "links.x.com"
    )
    assert isinstance(disabled.error, ConflictError)
    assert disabled.error.api_code == "TRACKING_DOMAINS_DISABLED"
    missing = _client([], *_error("DOMAIN_NOT_FOUND", 404)).domains.set_tracking_domain(
        "x", "links.x.com"
    )
    assert isinstance(missing.error, NotFoundError)


def test_remove_tracking_domain_returns_previous_host_or_none() -> None:
    captured: list[httpx.Request] = []
    removed = _client(captured, _TRACKING).domains.remove_tracking_domain("d1")
    assert captured[0].method == "DELETE"
    assert captured[0].url.path == "/v1/product/domains/d1/tracking-domain"
    assert removed.data is not None
    assert removed.data.host == "links.x.com"
    assert _client([], None).domains.remove_tracking_domain("d1").data is None
    missing = _client([], *_error("DOMAIN_NOT_FOUND", 404)).domains.remove_tracking_domain("x")
    assert isinstance(missing.error, NotFoundError)
    assert missing.data is None


async def test_async_domains_deliverability_operations() -> None:
    captured: list[httpx.Request] = []
    responses: dict[tuple[str, str], object] = {
        ("POST", "/v1/product/domains/d1/dkim/rotate"): _ROTATION,
        ("PUT", "/v1/product/domains/d1/tracking-domain"): _TRACKING,
        ("DELETE", "/v1/product/domains/d1/tracking-domain"): None,
    }

    async def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(200, json=responses[(request.method, request.url.path)])

    client = AsyncCoffeeMail(
        "cm_test_x", http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler))
    )
    rotation = await client.domains.rotate_dkim("d1")
    tracking = await client.domains.set_tracking_domain("d1", "links.x.com")
    removed = await client.domains.remove_tracking_domain("d1")
    assert rotation.data is not None
    assert rotation.data.selector == "cm2"
    assert tracking.data is not None
    assert tracking.data.host == "links.x.com"
    assert _body(captured[1]) == {"host": "links.x.com"}
    assert removed.error is None
    assert removed.data is None


_VERSION_SUMMARY = {
    "version": 2,
    "name": "Boas-vindas",
    "subject": None,
    "createdBy": None,
    "createdAt": "2026-10-15T10:00:00.000Z",
}
_VERSION_DETAIL = {
    **_VERSION_SUMMARY,
    "templateId": "t1",
    "preheader": None,
    "html": "<p>{{nome}}</p>",
    "contentJson": None,
    "textPayload": None,
    "variables": [{"name": "nome"}],
    "format": "react",
    "sourceLocale": "en",
}
_TEMPLATE = {"id": "t1", "name": "Boas-vindas", "html": "<p>x</p>", "createdAt": "2026-10-15"}
_DELIVERY = {
    "id": "dl2",
    "webhookId": "w1",
    "emailEventId": None,
    "eventType": "email.delivered",
    "responseStatus": None,
    "responseBody": None,
    "attempts": 0,
    "lastError": None,
    "status": "pending",
    "nextRunAt": "2026-10-15T10:00:00.000Z",
    "createdAt": "2026-10-15T10:00:00.000Z",
    "requestPayload": '{"event_type":"email.delivered"}',
}
_VALIDATION = {
    "items": [
        {"email": "ana@gmail.com", "formatValid": True, "mxValid": True, "isDisposable": False},
        {
            "email": "x@mailinator.com",
            "formatValid": True,
            "mxValid": True,
            "isDisposable": True,
            "reason": "disposable",
        },
    ],
    "validCount": 1,
    "invalidCount": 1,
    "credits": {"limit": 1000, "used": 2, "remaining": 998},
}


def test_list_versions_sends_pagination_and_parses_page() -> None:
    captured: list[httpx.Request] = []
    body = {"data": [_VERSION_SUMMARY], "total": 7}
    page = _client(captured, body).templates.list_versions("t1", limit=5, offset=10)
    assert captured[0].method == "GET"
    assert captured[0].url.path == "/v1/product/templates/t1/versions"
    assert dict(captured[0].url.params) == {"limit": "5", "offset": "10"}
    assert page.data is not None
    assert page.data.total == 7
    assert page.data.versions[0].version == 2
    assert page.data.versions[0].subject is None
    assert page.data.versions[0].created_by is None
    _client(captured).templates.list_versions("t1")
    assert not captured[1].url.params
    missing = _client([], *_error("TEMPLATE_NOT_FOUND", 404)).templates.list_versions("x")
    assert isinstance(missing.error, NotFoundError)
    assert missing.error.api_code == "TEMPLATE_NOT_FOUND"


def test_get_version_parses_detail_and_types_errors() -> None:
    captured: list[httpx.Request] = []
    detail = _client(captured, _VERSION_DETAIL).templates.get_version("t1", 2)
    assert captured[0].url.path == "/v1/product/templates/t1/versions/2"
    assert detail.data is not None
    assert detail.data.template_id == "t1"
    assert detail.data.format == "react"
    assert detail.data.source_locale == "en"
    assert detail.data.variables[0].name == "nome"
    gone = _client([], *_error("TEMPLATE_VERSION_NOT_FOUND", 404)).templates.get_version("t1", 9)
    assert isinstance(gone.error, NotFoundError)
    assert gone.error.api_code == "TEMPLATE_VERSION_NOT_FOUND"
    missing = _client([], *_error("TEMPLATE_NOT_FOUND", 404)).templates.get_version("x", 1)
    assert isinstance(missing.error, NotFoundError)
    assert missing.error.api_code == "TEMPLATE_NOT_FOUND"


def test_restore_version_posts_without_body_and_returns_template() -> None:
    captured: list[httpx.Request] = []
    restored = _client(captured, _TEMPLATE).templates.restore_version("t1", 2)
    assert captured[0].method == "POST"
    assert captured[0].url.path == "/v1/product/templates/t1/versions/2/restore"
    assert captured[0].content == b""
    assert "content-type" not in captured[0].headers
    assert restored.data is not None
    assert restored.data.id == "t1"
    gone = _client([], *_error("TEMPLATE_VERSION_NOT_FOUND", 404)).templates.restore_version(
        "t1", 9
    )
    assert isinstance(gone.error, NotFoundError)
    assert gone.error.api_code == "TEMPLATE_VERSION_NOT_FOUND"


def test_send_accepts_template_alias() -> None:
    captured: list[httpx.Request] = []
    payload = SendEmailPayload(
        from_address="a@x.com", to="b@y.com", template_id="boas-vindas", variables={"nome": "Ana"}
    )
    _client(captured, {"id": "e1"}).emails.send(payload)
    assert _body(captured[0])["templateId"] == "boas-vindas"


def test_validate_sends_emails_and_parses_items_and_credits() -> None:
    captured: list[httpx.Request] = []
    result = _client(captured, _VALIDATION).validation.validate([" ana@gmail.com ", "x@x.com"])
    assert captured[0].method == "POST"
    assert captured[0].url.path == "/v1/product/validate"
    assert _body(captured[0]) == {"emails": ["ana@gmail.com", "x@x.com"]}
    assert result.data is not None
    assert result.data.valid_count == 1
    assert result.data.invalid_count == 1
    assert result.data.items[0].reason is None
    assert result.data.items[1].is_disposable is True
    assert result.data.items[1].reason == "disposable"
    assert result.data.credits.remaining == 998
    assert result.data.credits.unlimited is False
    unlimited = {**_VALIDATION, "credits": {"limit": None, "used": 5, "remaining": None}}
    open_plan = _client([], unlimited).validation.validate(["ana@gmail.com"])
    assert open_plan.data is not None
    assert open_plan.data.credits.unlimited is True
    assert open_plan.data.credits.remaining is None


def test_validate_credits_exhausted_is_rate_limit_without_retry() -> None:
    captured: list[httpx.Request] = []
    client = _client(captured, *_error("VALIDATION_CREDITS_EXHAUSTED", 429))
    exhausted = client.validation.validate(["ana@gmail.com"])
    assert len(captured) == 1
    assert isinstance(exhausted.error, RateLimitError)
    assert exhausted.error.api_code == "VALIDATION_CREDITS_EXHAUSTED"
    assert exhausted.data is None
    invalid = _client([], *_error("VALIDATION_ERROR", 400)).validation.validate([])
    assert isinstance(invalid.error, ValidationError)


async def test_async_validate_credits_exhausted_without_retry() -> None:
    captured: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        body, status = _error("VALIDATION_CREDITS_EXHAUSTED", 429)
        return httpx.Response(status, json=body, headers={"retry-after": "60"})

    client = AsyncCoffeeMail(
        "cm_test_x", http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler))
    )
    exhausted = await client.validation.validate(["ana@gmail.com"])
    assert len(captured) == 1
    assert isinstance(exhausted.error, RateLimitError)
    assert exhausted.error.api_code == "VALIDATION_CREDITS_EXHAUSTED"


def test_get_delivery_exposes_request_payload_and_types_errors() -> None:
    captured: list[httpx.Request] = []
    delivery = _client(captured, {**_DELIVERY, "status": "failed"}).webhooks.get_delivery(
        "w1", "dl1"
    )
    assert captured[0].method == "GET"
    assert captured[0].url.path == "/v1/product/webhooks/w1/deliveries/dl1"
    assert delivery.data is not None
    assert delivery.data.request_payload == '{"event_type":"email.delivered"}'
    assert delivery.data.status == "failed"
    gone = _client([], *_error("WEBHOOK_DELIVERY_NOT_FOUND", 404)).webhooks.get_delivery("w1", "x")
    assert isinstance(gone.error, NotFoundError)
    assert gone.error.api_code == "WEBHOOK_DELIVERY_NOT_FOUND"
    missing = _client([], *_error("WEBHOOK_NOT_FOUND", 404)).webhooks.get_delivery("x", "dl1")
    assert isinstance(missing.error, NotFoundError)
    assert missing.error.api_code == "WEBHOOK_NOT_FOUND"


def test_replay_delivery_posts_without_body_and_types_conflicts() -> None:
    captured: list[httpx.Request] = []
    replay = _client(captured, _DELIVERY, 202).webhooks.replay_delivery("w1", "dl1")
    assert captured[0].method == "POST"
    assert captured[0].url.path == "/v1/product/webhooks/w1/deliveries/dl1/replay"
    assert captured[0].content == b""
    assert replay.status_code == 202
    assert replay.data is not None
    assert replay.data.id == "dl2"
    assert replay.data.status == "pending"
    for code in ("WEBHOOK_DELIVERY_PENDING", "WEBHOOK_NOT_ACTIVE"):
        conflict = _client([], *_error(code, 409)).webhooks.replay_delivery("w1", "dl1")
        assert isinstance(conflict.error, ConflictError)
        assert conflict.error.api_code == code
    gone = _client([], *_error("WEBHOOK_DELIVERY_NOT_FOUND", 404)).webhooks.replay_delivery(
        "w1", "x"
    )
    assert isinstance(gone.error, NotFoundError)


async def test_async_versions_and_deliveries() -> None:
    captured: list[httpx.Request] = []
    responses: dict[tuple[str, str], tuple[int, object]] = {
        ("GET", "/v1/product/templates/t1/versions"): (200, {"data": [], "total": 0}),
        ("GET", "/v1/product/templates/t1/versions/2"): (200, _VERSION_DETAIL),
        ("POST", "/v1/product/templates/t1/versions/2/restore"): (200, _TEMPLATE),
        ("GET", "/v1/product/webhooks/w1/deliveries/dl1"): (200, _DELIVERY),
        ("POST", "/v1/product/webhooks/w1/deliveries/dl1/replay"): (202, _DELIVERY),
        ("POST", "/v1/product/validate"): (200, _VALIDATION),
    }

    async def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        status, body = responses[(request.method, request.url.path)]
        return httpx.Response(status, json=body)

    client = AsyncCoffeeMail(
        "cm_test_x", http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler))
    )
    versions = await client.templates.list_versions("t1", limit=1)
    version = await client.templates.get_version("t1", 2)
    restored = await client.templates.restore_version("t1", 2)
    delivery = await client.webhooks.get_delivery("w1", "dl1")
    replay = await client.webhooks.replay_delivery("w1", "dl1")
    validated = await client.validation.validate(["ana@gmail.com"])
    assert versions.data is not None
    assert versions.data.total == 0
    assert dict(captured[0].url.params) == {"limit": "1"}
    assert version.data is not None
    assert version.data.html == "<p>{{nome}}</p>"
    assert restored.data is not None
    assert restored.data.name == "Boas-vindas"
    assert delivery.data is not None
    assert delivery.data.request_payload.startswith("{")
    assert replay.status_code == 202
    assert validated.data is not None
    assert validated.data.credits.used == 2
    assert _body(captured[-1]) == {"emails": ["ana@gmail.com"]}
