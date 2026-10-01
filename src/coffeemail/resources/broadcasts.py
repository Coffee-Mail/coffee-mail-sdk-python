from coffeemail.core.http import AsyncHttpTransport, HttpTransport
from coffeemail.core.types import CoffeeMailResponse
from coffeemail.models.broadcasts import (
    BroadcastDetail,
    ListBroadcastsResponse,
)


class Broadcasts:
    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport

    def list(
        self,
        limit: int | None = None,
        after: str | None = None,
    ) -> CoffeeMailResponse[ListBroadcastsResponse]:
        params: dict[str, object] = {}
        if limit is not None:
            params["limit"] = limit
        if after is not None:
            params["after"] = after

        res = self._transport.request("GET", "/v1/product/broadcasts", params=params)
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=ListBroadcastsResponse.model_validate(res.data),
            error=None,
            status_code=res.status_code,
        )

    def get(self, broadcast_id: str) -> CoffeeMailResponse[BroadcastDetail]:
        res = self._transport.request("GET", f"/v1/product/broadcasts/{broadcast_id}")
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=BroadcastDetail.model_validate(res.data), error=None, status_code=res.status_code
        )

    def create(
        self,
        name: str,
        subject: str,
        audience_id: str,
        template_id: str | None = None,
        html: str | None = None,
        text: str | None = None,
        scheduled_at: str | None = None,
    ) -> CoffeeMailResponse[BroadcastDetail]:
        body: dict[str, object] = {
            "name": name.strip(),
            "subject": subject.strip(),
            "audienceId": audience_id,
        }
        if template_id:
            body["templateId"] = template_id
        if html:
            body["html"] = html
        if text:
            body["text"] = text
        if scheduled_at:
            body["scheduledAt"] = scheduled_at

        res = self._transport.request("POST", "/v1/product/broadcasts", json_data=body)
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=BroadcastDetail.model_validate(res.data), error=None, status_code=res.status_code
        )

    def send(self, broadcast_id: str) -> CoffeeMailResponse[dict[str, object]]:
        return self._transport.request("POST", f"/v1/product/broadcasts/{broadcast_id}/send")

    def cancel(self, broadcast_id: str) -> CoffeeMailResponse[dict[str, object]]:
        return self._transport.request("POST", f"/v1/product/broadcasts/{broadcast_id}/cancel")

    def delete(self, broadcast_id: str) -> CoffeeMailResponse[dict[str, object]]:
        return self._transport.request("DELETE", f"/v1/product/broadcasts/{broadcast_id}")


class AsyncBroadcasts:
    def __init__(self, transport: AsyncHttpTransport) -> None:
        self._transport = transport

    async def list(
        self,
        limit: int | None = None,
        after: str | None = None,
    ) -> CoffeeMailResponse[ListBroadcastsResponse]:
        params: dict[str, object] = {}
        if limit is not None:
            params["limit"] = limit
        if after is not None:
            params["after"] = after

        res = await self._transport.request("GET", "/v1/product/broadcasts", params=params)
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=ListBroadcastsResponse.model_validate(res.data),
            error=None,
            status_code=res.status_code,
        )

    async def get(self, broadcast_id: str) -> CoffeeMailResponse[BroadcastDetail]:
        res = await self._transport.request("GET", f"/v1/product/broadcasts/{broadcast_id}")
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=BroadcastDetail.model_validate(res.data), error=None, status_code=res.status_code
        )

    async def create(
        self,
        name: str,
        subject: str,
        audience_id: str,
        template_id: str | None = None,
        html: str | None = None,
        text: str | None = None,
        scheduled_at: str | None = None,
    ) -> CoffeeMailResponse[BroadcastDetail]:
        body: dict[str, object] = {
            "name": name.strip(),
            "subject": subject.strip(),
            "audienceId": audience_id,
        }
        if template_id:
            body["templateId"] = template_id
        if html:
            body["html"] = html
        if text:
            body["text"] = text
        if scheduled_at:
            body["scheduledAt"] = scheduled_at

        res = await self._transport.request("POST", "/v1/product/broadcasts", json_data=body)
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=BroadcastDetail.model_validate(res.data), error=None, status_code=res.status_code
        )

    async def send(self, broadcast_id: str) -> CoffeeMailResponse[dict[str, object]]:
        return await self._transport.request("POST", f"/v1/product/broadcasts/{broadcast_id}/send")

    async def cancel(self, broadcast_id: str) -> CoffeeMailResponse[dict[str, object]]:
        return await self._transport.request(
            "POST", f"/v1/product/broadcasts/{broadcast_id}/cancel"
        )

    async def delete(self, broadcast_id: str) -> CoffeeMailResponse[dict[str, object]]:
        return await self._transport.request("DELETE", f"/v1/product/broadcasts/{broadcast_id}")
