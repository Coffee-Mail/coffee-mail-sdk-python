import json
from pathlib import Path
from typing import Any

import pytest

from coffeemail import AsyncCoffeeMail, CoffeeMail, sign_webhook, verify_webhook_signature
from coffeemail.resources.webhooks import AsyncWebhooks, Webhooks

VECTORS: list[dict[str, Any]] = json.loads(
    (Path(__file__).parent / "fixtures" / "webhook_vectors.json").read_text(encoding="utf-8")
)["vectors"]
SECRET = "whsec_test"
NOW = 1_760_000_000.0


def test_vectors_were_loaded() -> None:
    assert len(VECTORS) == 11


@pytest.mark.parametrize("vector", VECTORS, ids=[v["name"] for v in VECTORS])
def test_shared_vectors(vector: dict[str, Any]) -> None:
    result = verify_webhook_signature(
        vector["body"],
        vector["secret"],
        signature=vector["signature"],
        timestamp=vector["timestamp"],
        idempotency_key=vector["idempotencyKey"],
        tolerance_seconds=vector["toleranceSeconds"],
        now=lambda: float(vector["nowEpochSeconds"]),
    )
    assert result is vector["expected"]


def _headers(body: str, timestamp: str = "1760000000") -> dict[str, str]:
    signature = sign_webhook(body, SECRET, timestamp, "ed4e7012eb856296")
    return {
        "X-Webhook-Signature": signature,
        "X-Webhook-Timestamp": timestamp,
        "X-Webhook-Idempotency-Key": "ed4e7012eb856296",
    }


def test_accepts_request_headers_case_insensitively() -> None:
    body = '{"event_type":"email.delivered"}'
    assert verify_webhook_signature(body, SECRET, headers=_headers(body), now=lambda: NOW)
    assert verify_webhook_signature(body.encode(), SECRET, headers=_headers(body), now=lambda: NOW)


def test_rejects_missing_headers_or_secret() -> None:
    body = "{}"
    assert not verify_webhook_signature(body, SECRET, headers={}, now=lambda: NOW)
    assert not verify_webhook_signature(body, "", headers=_headers(body), now=lambda: NOW)


def test_rejects_body_reserialization_and_expired_deliveries() -> None:
    body = '{"a": 1}'
    assert not verify_webhook_signature('{"a":1}', SECRET, headers=_headers(body), now=lambda: NOW)
    assert not verify_webhook_signature(body, SECRET, headers=_headers(body), now=lambda: NOW + 301)


def test_tolerance_is_configurable() -> None:
    body = "{}"
    headers = _headers(body)
    assert verify_webhook_signature(
        body, SECRET, headers=headers, tolerance_seconds=600, now=lambda: NOW + 500
    )


@pytest.mark.parametrize("resource", [Webhooks, AsyncWebhooks])
def test_resources_expose_the_same_verifier(resource: type[Webhooks] | type[AsyncWebhooks]) -> None:
    body = "{}"
    assert resource.verify_signature(body, SECRET, headers=_headers(body), now=lambda: NOW)
    assert not resource.verify_signature(
        body, "whsec_errado", headers=_headers(body), now=lambda: NOW
    )


def test_clients_expose_the_verifier_without_network() -> None:
    body = "{}"
    sync_client = CoffeeMail("cm_test_x")
    async_client = AsyncCoffeeMail("cm_test_x")
    assert sync_client.webhooks.verify_signature(
        body, SECRET, headers=_headers(body), now=lambda: NOW
    )
    assert async_client.webhooks.verify_signature(
        body, SECRET, headers=_headers(body), now=lambda: NOW
    )


def test_old_positional_call_fails_loudly() -> None:
    with pytest.raises(TypeError):
        legacy_call: Any = Webhooks.verify_signature
        legacy_call("{}", "sha256=abc", SECRET)
