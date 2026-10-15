from collections.abc import Mapping

from coffeemail.core.http import AsyncHttpTransport, HttpTransport
from coffeemail.core.types import CoffeeMailResponse
from coffeemail.models.broadcasts import (
    BroadcastDetail,
    BroadcastStatus,
    CancelBroadcastResult,
    ListBroadcastsResponse,
    SendBroadcastResult,
    TestSendResult,
)
from coffeemail.resources._common import compact, parse_model

BROADCASTS_PATH = "/v1/product/broadcasts"
OP_CREATE = "broadcasts.create"
OP_LIST = "broadcasts.list"
OP_GET = "broadcasts.get"
OP_SEND = "broadcasts.send"
OP_TEST_SEND = "broadcasts.testSend"
OP_CANCEL = "broadcasts.cancel"


def _list_params(
    limit: int | None,
    after: str | None,
    status: BroadcastStatus | None,
    from_date: str | None,
    to_date: str | None,
) -> dict[str, object]:
    return compact(limit=limit, after=after, status=status, **{"from": from_date, "to": to_date})


def _create_body(
    audience_id: str,
    from_email: str,
    subject: str | None,
    template_id: str | None,
    html: str | None,
    text: str | None,
    reply_to: str | None,
    variables: Mapping[str, object] | None,
) -> dict[str, object]:
    return compact(
        audienceId=audience_id,
        fromEmail=from_email.strip(),
        subject=subject,
        templateId=template_id,
        html=html,
        text=text,
        replyTo=reply_to,
        variables=dict(variables) if variables is not None else None,
    )


def _test_send_body(to: str, variables: Mapping[str, object] | None) -> dict[str, object]:
    return compact(to=to.strip(), variables=dict(variables) if variables is not None else None)


class Broadcasts:
    """Campanhas. Toda operação exige chave ``full_access``; sem ela o erro é
    ``PermissionDeniedError`` (código ``PERMISSION_DENIED``)."""

    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport

    def list(
        self,
        limit: int | None = None,
        after: str | None = None,
        *,
        status: BroadcastStatus | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> CoffeeMailResponse[ListBroadcastsResponse]:
        params = _list_params(limit, after, status, from_date, to_date)
        res = self._transport.request(
            "GET", BROADCASTS_PATH, params=params, permission_operation=OP_LIST
        )
        return parse_model(res, ListBroadcastsResponse, self._transport.locale)

    def get(self, broadcast_id: str) -> CoffeeMailResponse[BroadcastDetail]:
        res = self._transport.request(
            "GET", f"{BROADCASTS_PATH}/{broadcast_id}", permission_operation=OP_GET
        )
        return parse_model(res, BroadcastDetail, self._transport.locale)

    def create(
        self,
        *,
        audience_id: str,
        from_email: str,
        subject: str | None = None,
        template_id: str | None = None,
        html: str | None = None,
        text: str | None = None,
        reply_to: str | None = None,
        variables: Mapping[str, object] | None = None,
    ) -> CoffeeMailResponse[BroadcastDetail]:
        body = _create_body(
            audience_id, from_email, subject, template_id, html, text, reply_to, variables
        )
        res = self._transport.request(
            "POST", BROADCASTS_PATH, json_data=body, permission_operation=OP_CREATE
        )
        return parse_model(res, BroadcastDetail, self._transport.locale)

    def send(self, broadcast_id: str) -> CoffeeMailResponse[SendBroadcastResult]:
        res = self._transport.request(
            "POST", f"{BROADCASTS_PATH}/{broadcast_id}/send", permission_operation=OP_SEND
        )
        return parse_model(res, SendBroadcastResult, self._transport.locale)

    def cancel(self, broadcast_id: str) -> CoffeeMailResponse[CancelBroadcastResult]:
        res = self._transport.request(
            "POST", f"{BROADCASTS_PATH}/{broadcast_id}/cancel", permission_operation=OP_CANCEL
        )
        return parse_model(res, CancelBroadcastResult, self._transport.locale)

    def test_send(
        self, broadcast_id: str, to: str, variables: Mapping[str, object] | None = None
    ) -> CoffeeMailResponse[TestSendResult]:
        res = self._transport.request(
            "POST",
            f"{BROADCASTS_PATH}/{broadcast_id}/test-send",
            json_data=_test_send_body(to, variables),
            permission_operation=OP_TEST_SEND,
        )
        return parse_model(res, TestSendResult, self._transport.locale)


class AsyncBroadcasts:
    """Versão assíncrona de :class:`Broadcasts`."""

    def __init__(self, transport: AsyncHttpTransport) -> None:
        self._transport = transport

    async def list(
        self,
        limit: int | None = None,
        after: str | None = None,
        *,
        status: BroadcastStatus | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> CoffeeMailResponse[ListBroadcastsResponse]:
        params = _list_params(limit, after, status, from_date, to_date)
        res = await self._transport.request(
            "GET", BROADCASTS_PATH, params=params, permission_operation=OP_LIST
        )
        return parse_model(res, ListBroadcastsResponse, self._transport.locale)

    async def get(self, broadcast_id: str) -> CoffeeMailResponse[BroadcastDetail]:
        res = await self._transport.request(
            "GET", f"{BROADCASTS_PATH}/{broadcast_id}", permission_operation=OP_GET
        )
        return parse_model(res, BroadcastDetail, self._transport.locale)

    async def create(
        self,
        *,
        audience_id: str,
        from_email: str,
        subject: str | None = None,
        template_id: str | None = None,
        html: str | None = None,
        text: str | None = None,
        reply_to: str | None = None,
        variables: Mapping[str, object] | None = None,
    ) -> CoffeeMailResponse[BroadcastDetail]:
        body = _create_body(
            audience_id, from_email, subject, template_id, html, text, reply_to, variables
        )
        res = await self._transport.request(
            "POST", BROADCASTS_PATH, json_data=body, permission_operation=OP_CREATE
        )
        return parse_model(res, BroadcastDetail, self._transport.locale)

    async def send(self, broadcast_id: str) -> CoffeeMailResponse[SendBroadcastResult]:
        res = await self._transport.request(
            "POST", f"{BROADCASTS_PATH}/{broadcast_id}/send", permission_operation=OP_SEND
        )
        return parse_model(res, SendBroadcastResult, self._transport.locale)

    async def cancel(self, broadcast_id: str) -> CoffeeMailResponse[CancelBroadcastResult]:
        res = await self._transport.request(
            "POST", f"{BROADCASTS_PATH}/{broadcast_id}/cancel", permission_operation=OP_CANCEL
        )
        return parse_model(res, CancelBroadcastResult, self._transport.locale)

    async def test_send(
        self, broadcast_id: str, to: str, variables: Mapping[str, object] | None = None
    ) -> CoffeeMailResponse[TestSendResult]:
        res = await self._transport.request(
            "POST",
            f"{BROADCASTS_PATH}/{broadcast_id}/test-send",
            json_data=_test_send_body(to, variables),
            permission_operation=OP_TEST_SEND,
        )
        return parse_model(res, TestSendResult, self._transport.locale)
