import builtins
import time
from collections.abc import Callable, Mapping

from coffeemail.core.crypto import DEFAULT_TOLERANCE_SECONDS, verify_webhook_signature
from coffeemail.core.http import AsyncHttpTransport, HttpTransport
from coffeemail.core.types import CoffeeMailResponse
from coffeemail.models.webhooks import (
    CreatedWebhookDetail,
    ListWebhookDeliveriesResponse,
    ListWebhooksResponse,
    RotateWebhookSecretResult,
    TestWebhookResult,
    ToggleWebhookResult,
    WebhookDeliveryDetail,
    WebhookDeliveryStatus,
    WebhookDetail,
    WebhookStatus,
)
from coffeemail.resources._common import compact, parse_model

WEBHOOKS_PATH = "/v1/product/webhooks"
_STATUS_BY_ENABLED: dict[bool, WebhookStatus] = {True: "active", False: "paused"}


def _create_body(
    url: str, events: builtins.list[str], description: str | None
) -> dict[str, object]:
    return compact(url=url.strip(), events=list(events), description=description)


def _update_body(
    url: str | None, events: builtins.list[str] | None, description: str | None
) -> dict[str, object]:
    return compact(
        url=url.strip() if url else None,
        events=list(events) if events is not None else None,
        description=description,
    )


def _deliveries_params(
    event_type: str | None,
    status: WebhookDeliveryStatus | None,
    from_date: str | None,
    to_date: str | None,
    limit: int | None,
) -> dict[str, object]:
    return compact(
        eventType=event_type, status=status, limit=limit, **{"from": from_date, "to": to_date}
    )


def _delivery_path(webhook_id: str, delivery_id: str) -> str:
    return f"{WEBHOOKS_PATH}/{webhook_id}/deliveries/{delivery_id}"


def _verify(
    payload: str | bytes,
    secret: str,
    headers: Mapping[str, str] | None,
    signature: str | None,
    timestamp: str | None,
    idempotency_key: str | None,
    tolerance_seconds: int,
    now: Callable[[], float],
) -> bool:
    return verify_webhook_signature(
        payload,
        secret,
        headers=headers,
        signature=signature,
        timestamp=timestamp,
        idempotency_key=idempotency_key,
        tolerance_seconds=tolerance_seconds,
        now=now,
    )


class Webhooks:
    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport

    def list(self, status: WebhookStatus | None = None) -> CoffeeMailResponse[ListWebhooksResponse]:
        res = self._transport.request("GET", WEBHOOKS_PATH, params=compact(status=status))
        return parse_model(res, ListWebhooksResponse, self._transport.locale)

    def get(self, webhook_id: str) -> CoffeeMailResponse[WebhookDetail]:
        res = self._transport.request("GET", f"{WEBHOOKS_PATH}/{webhook_id}")
        return parse_model(res, WebhookDetail, self._transport.locale)

    def create(
        self, url: str, events: builtins.list[str], description: str | None = None
    ) -> CoffeeMailResponse[CreatedWebhookDetail]:
        body = _create_body(url, events, description)
        res = self._transport.request("POST", WEBHOOKS_PATH, json_data=body)
        return parse_model(res, CreatedWebhookDetail, self._transport.locale)

    def update(
        self,
        webhook_id: str,
        *,
        url: str | None = None,
        events: builtins.list[str] | None = None,
        description: str | None = None,
    ) -> CoffeeMailResponse[WebhookDetail]:
        body = _update_body(url, events, description)
        res = self._transport.request("PUT", f"{WEBHOOKS_PATH}/{webhook_id}", json_data=body)
        return parse_model(res, WebhookDetail, self._transport.locale)

    def toggle(self, webhook_id: str, enabled: bool) -> CoffeeMailResponse[ToggleWebhookResult]:
        body: dict[str, object] = {"status": _STATUS_BY_ENABLED[enabled]}
        res = self._transport.request("PATCH", f"{WEBHOOKS_PATH}/{webhook_id}", json_data=body)
        return parse_model(res, ToggleWebhookResult, self._transport.locale)

    def delete(self, webhook_id: str) -> CoffeeMailResponse[dict[str, object]]:
        return self._transport.request("DELETE", f"{WEBHOOKS_PATH}/{webhook_id}")

    def rotate_secret(self, webhook_id: str) -> CoffeeMailResponse[RotateWebhookSecretResult]:
        res = self._transport.request("POST", f"{WEBHOOKS_PATH}/{webhook_id}/rotate-secret")
        return parse_model(res, RotateWebhookSecretResult, self._transport.locale)

    def list_deliveries(
        self,
        webhook_id: str,
        *,
        event_type: str | None = None,
        status: WebhookDeliveryStatus | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        limit: int | None = None,
    ) -> CoffeeMailResponse[ListWebhookDeliveriesResponse]:
        params = _deliveries_params(event_type, status, from_date, to_date, limit)
        res = self._transport.request(
            "GET", f"{WEBHOOKS_PATH}/{webhook_id}/deliveries", params=params
        )
        return parse_model(res, ListWebhookDeliveriesResponse, self._transport.locale)

    def get_delivery(
        self, webhook_id: str, delivery_id: str
    ) -> CoffeeMailResponse[WebhookDeliveryDetail]:
        res = self._transport.request("GET", _delivery_path(webhook_id, delivery_id))
        return parse_model(res, WebhookDeliveryDetail, self._transport.locale)

    def replay_delivery(
        self, webhook_id: str, delivery_id: str
    ) -> CoffeeMailResponse[WebhookDeliveryDetail]:
        """Reenfileira o mesmo corpo como uma entrega nova (``pending``)."""
        res = self._transport.request("POST", f"{_delivery_path(webhook_id, delivery_id)}/replay")
        return parse_model(res, WebhookDeliveryDetail, self._transport.locale)

    def test(self, webhook_id: str) -> CoffeeMailResponse[TestWebhookResult]:
        res = self._transport.request("POST", f"{WEBHOOKS_PATH}/{webhook_id}/test")
        return parse_model(res, TestWebhookResult, self._transport.locale)

    @staticmethod
    def verify_signature(
        payload: str | bytes,
        secret: str,
        *,
        headers: Mapping[str, str] | None = None,
        signature: str | None = None,
        timestamp: str | None = None,
        idempotency_key: str | None = None,
        tolerance_seconds: int = DEFAULT_TOLERANCE_SECONDS,
        now: Callable[[], float] = time.time,
    ) -> bool:
        """Verifica uma entrega de webhook. Veja :func:`coffeemail.verify_webhook_signature`."""
        return _verify(
            payload, secret, headers, signature, timestamp, idempotency_key, tolerance_seconds, now
        )


class AsyncWebhooks:
    def __init__(self, transport: AsyncHttpTransport) -> None:
        self._transport = transport

    async def list(
        self, status: WebhookStatus | None = None
    ) -> CoffeeMailResponse[ListWebhooksResponse]:
        res = await self._transport.request("GET", WEBHOOKS_PATH, params=compact(status=status))
        return parse_model(res, ListWebhooksResponse, self._transport.locale)

    async def get(self, webhook_id: str) -> CoffeeMailResponse[WebhookDetail]:
        res = await self._transport.request("GET", f"{WEBHOOKS_PATH}/{webhook_id}")
        return parse_model(res, WebhookDetail, self._transport.locale)

    async def create(
        self, url: str, events: builtins.list[str], description: str | None = None
    ) -> CoffeeMailResponse[CreatedWebhookDetail]:
        body = _create_body(url, events, description)
        res = await self._transport.request("POST", WEBHOOKS_PATH, json_data=body)
        return parse_model(res, CreatedWebhookDetail, self._transport.locale)

    async def update(
        self,
        webhook_id: str,
        *,
        url: str | None = None,
        events: builtins.list[str] | None = None,
        description: str | None = None,
    ) -> CoffeeMailResponse[WebhookDetail]:
        body = _update_body(url, events, description)
        res = await self._transport.request("PUT", f"{WEBHOOKS_PATH}/{webhook_id}", json_data=body)
        return parse_model(res, WebhookDetail, self._transport.locale)

    async def toggle(
        self, webhook_id: str, enabled: bool
    ) -> CoffeeMailResponse[ToggleWebhookResult]:
        body: dict[str, object] = {"status": _STATUS_BY_ENABLED[enabled]}
        res = await self._transport.request(
            "PATCH", f"{WEBHOOKS_PATH}/{webhook_id}", json_data=body
        )
        return parse_model(res, ToggleWebhookResult, self._transport.locale)

    async def delete(self, webhook_id: str) -> CoffeeMailResponse[dict[str, object]]:
        return await self._transport.request("DELETE", f"{WEBHOOKS_PATH}/{webhook_id}")

    async def rotate_secret(self, webhook_id: str) -> CoffeeMailResponse[RotateWebhookSecretResult]:
        res = await self._transport.request("POST", f"{WEBHOOKS_PATH}/{webhook_id}/rotate-secret")
        return parse_model(res, RotateWebhookSecretResult, self._transport.locale)

    async def list_deliveries(
        self,
        webhook_id: str,
        *,
        event_type: str | None = None,
        status: WebhookDeliveryStatus | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        limit: int | None = None,
    ) -> CoffeeMailResponse[ListWebhookDeliveriesResponse]:
        params = _deliveries_params(event_type, status, from_date, to_date, limit)
        res = await self._transport.request(
            "GET", f"{WEBHOOKS_PATH}/{webhook_id}/deliveries", params=params
        )
        return parse_model(res, ListWebhookDeliveriesResponse, self._transport.locale)

    async def get_delivery(
        self, webhook_id: str, delivery_id: str
    ) -> CoffeeMailResponse[WebhookDeliveryDetail]:
        res = await self._transport.request("GET", _delivery_path(webhook_id, delivery_id))
        return parse_model(res, WebhookDeliveryDetail, self._transport.locale)

    async def replay_delivery(
        self, webhook_id: str, delivery_id: str
    ) -> CoffeeMailResponse[WebhookDeliveryDetail]:
        """Reenfileira o mesmo corpo como uma entrega nova (``pending``)."""
        res = await self._transport.request(
            "POST", f"{_delivery_path(webhook_id, delivery_id)}/replay"
        )
        return parse_model(res, WebhookDeliveryDetail, self._transport.locale)

    async def test(self, webhook_id: str) -> CoffeeMailResponse[TestWebhookResult]:
        res = await self._transport.request("POST", f"{WEBHOOKS_PATH}/{webhook_id}/test")
        return parse_model(res, TestWebhookResult, self._transport.locale)

    @staticmethod
    def verify_signature(
        payload: str | bytes,
        secret: str,
        *,
        headers: Mapping[str, str] | None = None,
        signature: str | None = None,
        timestamp: str | None = None,
        idempotency_key: str | None = None,
        tolerance_seconds: int = DEFAULT_TOLERANCE_SECONDS,
        now: Callable[[], float] = time.time,
    ) -> bool:
        """Verifica uma entrega de webhook. Veja :func:`coffeemail.verify_webhook_signature`."""
        return _verify(
            payload, secret, headers, signature, timestamp, idempotency_key, tolerance_seconds, now
        )
