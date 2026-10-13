from coffeemail.core.http import AsyncHttpTransport, HttpTransport
from coffeemail.core.types import CoffeeMailResponse


class Senders:
    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport

    def create(self, email: str, display_name: str) -> CoffeeMailResponse[dict[str, object]]:
        return self._transport.request(
            "POST", "/v1/product/senders", json_data={"email": email, "displayName": display_name}
        )

    def list(self) -> CoffeeMailResponse[dict[str, object]]:
        return self._transport.request("GET", "/v1/product/senders")

    def verify(self, token: str) -> CoffeeMailResponse[dict[str, object]]:
        return self._transport.request(
            "POST", "/v1/product/senders/verify", json_data={"token": token}
        )

    def delete(self, sender_id: str) -> CoffeeMailResponse[dict[str, object]]:
        return self._transport.request("DELETE", f"/v1/product/senders/{sender_id}")


class AsyncSenders:
    def __init__(self, transport: AsyncHttpTransport) -> None:
        self._transport = transport

    async def create(self, email: str, display_name: str) -> CoffeeMailResponse[dict[str, object]]:
        return await self._transport.request(
            "POST", "/v1/product/senders", json_data={"email": email, "displayName": display_name}
        )

    async def list(self) -> CoffeeMailResponse[dict[str, object]]:
        return await self._transport.request("GET", "/v1/product/senders")

    async def verify(self, token: str) -> CoffeeMailResponse[dict[str, object]]:
        return await self._transport.request(
            "POST", "/v1/product/senders/verify", json_data={"token": token}
        )

    async def delete(self, sender_id: str) -> CoffeeMailResponse[dict[str, object]]:
        return await self._transport.request("DELETE", f"/v1/product/senders/{sender_id}")
