from coffeemail.core.http import AsyncHttpTransport, HttpTransport
from coffeemail.core.types import CoffeeMailResponse
from coffeemail.models.senders import (
    CreatedSender,
    ListSendersResponse,
    VerifySenderResult,
)
from coffeemail.resources._common import compact, parse_model

SENDERS_PATH = "/v1/product/senders"


def _create_body(email: str, display_name: str | None) -> dict[str, object]:
    return compact(email=email.strip(), displayName=display_name)


class Senders:
    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport

    def create(
        self, email: str, display_name: str | None = None
    ) -> CoffeeMailResponse[CreatedSender]:
        res = self._transport.request(
            "POST", SENDERS_PATH, json_data=_create_body(email, display_name)
        )
        return parse_model(res, CreatedSender, self._transport.locale)

    def list(self) -> CoffeeMailResponse[ListSendersResponse]:
        res = self._transport.request("GET", SENDERS_PATH)
        return parse_model(res, ListSendersResponse, self._transport.locale)

    def verify(self, token: str) -> CoffeeMailResponse[VerifySenderResult]:
        res = self._transport.request("POST", f"{SENDERS_PATH}/verify", json_data={"token": token})
        return parse_model(res, VerifySenderResult, self._transport.locale)

    def resend_verification(self, sender_id: str) -> CoffeeMailResponse[dict[str, object]]:
        return self._transport.request("POST", f"{SENDERS_PATH}/{sender_id}/resend-verification")

    def delete(self, sender_id: str) -> CoffeeMailResponse[dict[str, object]]:
        return self._transport.request("DELETE", f"{SENDERS_PATH}/{sender_id}")


class AsyncSenders:
    def __init__(self, transport: AsyncHttpTransport) -> None:
        self._transport = transport

    async def create(
        self, email: str, display_name: str | None = None
    ) -> CoffeeMailResponse[CreatedSender]:
        res = await self._transport.request(
            "POST", SENDERS_PATH, json_data=_create_body(email, display_name)
        )
        return parse_model(res, CreatedSender, self._transport.locale)

    async def list(self) -> CoffeeMailResponse[ListSendersResponse]:
        res = await self._transport.request("GET", SENDERS_PATH)
        return parse_model(res, ListSendersResponse, self._transport.locale)

    async def verify(self, token: str) -> CoffeeMailResponse[VerifySenderResult]:
        res = await self._transport.request(
            "POST", f"{SENDERS_PATH}/verify", json_data={"token": token}
        )
        return parse_model(res, VerifySenderResult, self._transport.locale)

    async def resend_verification(self, sender_id: str) -> CoffeeMailResponse[dict[str, object]]:
        return await self._transport.request(
            "POST", f"{SENDERS_PATH}/{sender_id}/resend-verification"
        )

    async def delete(self, sender_id: str) -> CoffeeMailResponse[dict[str, object]]:
        return await self._transport.request("DELETE", f"{SENDERS_PATH}/{sender_id}")
