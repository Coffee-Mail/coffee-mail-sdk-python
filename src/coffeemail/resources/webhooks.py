import builtins

from coffeemail.core.crypto import verify_webhook_signature
from coffeemail.core.http import AsyncHttpTransport, HttpTransport
from coffeemail.core.types import CoffeeMailResponse
from coffeemail.models.webhooks import (
    CreatedWebhookDetail,
    ListWebhooksResponse,
    RotateWebhookSecretResult,
    TestWebhookResult,
    WebhookDetail,
)


class Webhooks:
    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport

    def list(self) -> CoffeeMailResponse[ListWebhooksResponse]:
        res = self._transport.request("GET", "/v1/product/webhooks")
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=ListWebhooksResponse.model_validate(res.data),
            error=None,
            status_code=res.status_code,
        )

    def get(self, webhook_id: str) -> CoffeeMailResponse[WebhookDetail]:
        res = self._transport.request("GET", f"/v1/product/webhooks/{webhook_id}")
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=WebhookDetail.model_validate(res.data), error=None, status_code=res.status_code
        )

    def create(
        self, url: str, events: builtins.list[str], secret: str | None = None
    ) -> CoffeeMailResponse[CreatedWebhookDetail]:
        body: dict[str, object] = {"url": url.strip(), "events": events}
        if secret:
            body["secret"] = secret.strip()

        res = self._transport.request("POST", "/v1/product/webhooks", json_data=body)
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=CreatedWebhookDetail.model_validate(res.data),
            error=None,
            status_code=res.status_code,
        )

    def update(
        self,
        webhook_id: str,
        url: str | None = None,
        events: builtins.list[str] | None = None,
    ) -> CoffeeMailResponse[WebhookDetail]:
        body: dict[str, object] = {}
        if url:
            body["url"] = url.strip()
        if events:
            body["events"] = events

        res = self._transport.request("PATCH", f"/v1/product/webhooks/{webhook_id}", json_data=body)
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=WebhookDetail.model_validate(res.data), error=None, status_code=res.status_code
        )

    def rotate_secret(self, webhook_id: str) -> CoffeeMailResponse[RotateWebhookSecretResult]:
        res = self._transport.request("POST", f"/v1/product/webhooks/{webhook_id}/rotate-secret")
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=RotateWebhookSecretResult.model_validate(res.data),
            error=None,
            status_code=res.status_code,
        )

    def test(self, webhook_id: str) -> CoffeeMailResponse[TestWebhookResult]:
        res = self._transport.request("POST", f"/v1/product/webhooks/{webhook_id}/test")
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=TestWebhookResult.model_validate(res.data), error=None, status_code=res.status_code
        )

    def delete(self, webhook_id: str) -> CoffeeMailResponse[dict[str, object]]:
        return self._transport.request("DELETE", f"/v1/product/webhooks/{webhook_id}")

    @staticmethod
    def verify_signature(payload: str | bytes, signature: str, secret: str) -> bool:
        return verify_webhook_signature(payload, signature, secret)

    def list_deliveries(self, webhook_id: str) -> CoffeeMailResponse[dict[str, object]]:
        return self._transport.request("GET", f"/v1/product/webhooks/{webhook_id}/deliveries")

    def toggle(self, webhook_id: str, enabled: bool) -> CoffeeMailResponse[dict[str, object]]:
        return self._transport.request(
            "PATCH",
            f"/v1/product/webhooks/{webhook_id}",
            json_data={"status": "active" if enabled else "paused"},
        )


class AsyncWebhooks:
    def __init__(self, transport: AsyncHttpTransport) -> None:
        self._transport = transport

    async def list(self) -> CoffeeMailResponse[ListWebhooksResponse]:
        res = await self._transport.request("GET", "/v1/product/webhooks")
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=ListWebhooksResponse.model_validate(res.data),
            error=None,
            status_code=res.status_code,
        )

    async def get(self, webhook_id: str) -> CoffeeMailResponse[WebhookDetail]:
        res = await self._transport.request("GET", f"/v1/product/webhooks/{webhook_id}")
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=WebhookDetail.model_validate(res.data), error=None, status_code=res.status_code
        )

    async def create(
        self, url: str, events: builtins.list[str], secret: str | None = None
    ) -> CoffeeMailResponse[CreatedWebhookDetail]:
        body: dict[str, object] = {"url": url.strip(), "events": events}
        if secret:
            body["secret"] = secret.strip()

        res = await self._transport.request("POST", "/v1/product/webhooks", json_data=body)
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=CreatedWebhookDetail.model_validate(res.data),
            error=None,
            status_code=res.status_code,
        )

    async def update(
        self,
        webhook_id: str,
        url: str | None = None,
        events: builtins.list[str] | None = None,
    ) -> CoffeeMailResponse[WebhookDetail]:
        body: dict[str, object] = {}
        if url:
            body["url"] = url.strip()
        if events:
            body["events"] = events

        res = await self._transport.request(
            "PATCH", f"/v1/product/webhooks/{webhook_id}", json_data=body
        )
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=WebhookDetail.model_validate(res.data), error=None, status_code=res.status_code
        )

    async def rotate_secret(self, webhook_id: str) -> CoffeeMailResponse[RotateWebhookSecretResult]:
        res = await self._transport.request(
            "POST", f"/v1/product/webhooks/{webhook_id}/rotate-secret"
        )
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=RotateWebhookSecretResult.model_validate(res.data),
            error=None,
            status_code=res.status_code,
        )

    async def test(self, webhook_id: str) -> CoffeeMailResponse[TestWebhookResult]:
        res = await self._transport.request("POST", f"/v1/product/webhooks/{webhook_id}/test")
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=TestWebhookResult.model_validate(res.data), error=None, status_code=res.status_code
        )

    async def delete(self, webhook_id: str) -> CoffeeMailResponse[dict[str, object]]:
        return await self._transport.request("DELETE", f"/v1/product/webhooks/{webhook_id}")

    @staticmethod
    def verify_signature(payload: str | bytes, signature: str, secret: str) -> bool:
        return verify_webhook_signature(payload, signature, secret)

    async def list_deliveries(self, webhook_id: str) -> CoffeeMailResponse[dict[str, object]]:
        return await self._transport.request("GET", f"/v1/product/webhooks/{webhook_id}/deliveries")

    async def toggle(self, webhook_id: str, enabled: bool) -> CoffeeMailResponse[dict[str, object]]:
        return await self._transport.request(
            "PATCH",
            f"/v1/product/webhooks/{webhook_id}",
            json_data={"status": "active" if enabled else "paused"},
        )
