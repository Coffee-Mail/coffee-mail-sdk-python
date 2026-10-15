import base64
import re
from collections.abc import Mapping, Sequence
from pathlib import Path

from pydantic import TypeAdapter

from coffeemail.core.errors import ValidationError
from coffeemail.core.http import AsyncHttpTransport, HttpTransport, send_headers
from coffeemail.core.types import CoffeeMailResponse
from coffeemail.models.emails import (
    BatchSendEmailResult,
    EmailAttachment,
    EmailDetail,
    EmailEventsResponse,
    EmailParticipant,
    ListEmailsResponse,
    ListEmailTagsResponse,
    SendEmailPayload,
    SendEmailResponse,
)
from coffeemail.resources._common import (
    InputError,
    build_input,
    compact,
    input_failure,
    parse_adapter,
    parse_model,
)

_NAMED_EMAIL_PATTERN = re.compile(r"^(?:(?P<name>.*?)\s*<)?(?P<email>[^<>\s]+)>?$")


def _parse_participant_string(item: str) -> dict[str, object]:
    trimmed = item.strip()
    match = _NAMED_EMAIL_PATTERN.match(trimmed)
    if not match:
        return {"email": trimmed}

    email = match.group("email").strip()
    raw_name = match.group("name")
    name = raw_name.strip().strip("\"'") if raw_name else None
    if not name:
        return {"email": email}

    return {"email": email, "name": name}


def _normalize_participant(
    item: str | EmailParticipant | dict[str, object],
) -> dict[str, object]:
    if isinstance(item, str):
        return _parse_participant_string(item)

    if isinstance(item, EmailParticipant):
        payload: dict[str, object] = {"email": item.email.strip()}
        if item.name:
            payload["name"] = item.name.strip()
        return payload

    is_valid_dict = isinstance(item, dict) and "email" in item
    if is_valid_dict:
        payload = {"email": str(item["email"]).strip()}
        if item.get("name"):
            payload["name"] = str(item["name"]).strip()
        return payload

    raise InputError("invalid_recipient")


def _normalize_participants(
    items: str
    | EmailParticipant
    | dict[str, object]
    | Sequence[str | EmailParticipant | dict[str, object]]
    | None,
) -> list[dict[str, object]] | None:
    if isinstance(items, (list, tuple)):
        return [_normalize_participant(i) for i in items]
    if isinstance(items, (str, EmailParticipant, dict)):
        return [_normalize_participant(items)]
    if items is None:
        return None
    raise InputError("invalid_recipient")


def _attachment_fields(
    attachment: EmailAttachment | dict[str, object],
) -> tuple[str, object, str, str, str | None]:
    model = (
        attachment
        if isinstance(attachment, EmailAttachment)
        else EmailAttachment.model_validate(attachment)
    )
    return (
        model.filename,
        model.content,
        model.content_type or "application/octet-stream",
        model.disposition or "attachment",
        model.cid,
    )


def _encode_attachment_content(raw_content: object) -> str:
    if isinstance(raw_content, bytes):
        return base64.b64encode(raw_content).decode("ascii")
    if not isinstance(raw_content, str):
        return str(raw_content)
    if Path(raw_content).is_file():
        return base64.b64encode(Path(raw_content).read_bytes()).decode("ascii")
    return raw_content


def _serialize_attachment(
    attachment: EmailAttachment | dict[str, object],
) -> dict[str, object]:
    filename, raw_content, content_type, disposition, cid = _attachment_fields(attachment)
    content = _encode_attachment_content(raw_content)

    res: dict[str, object] = {
        "filename": filename,
        "content": content,
        "contentType": content_type,
        "disposition": disposition,
    }
    if cid:
        res["cid"] = cid
    return res


_HEADER_ONLY_KEYS = ("idempotencyKey", "idempotency_key", "sandbox", "isSandbox")


def _header_fields(data: dict[str, object]) -> tuple[str | None, bool]:
    key = data.get("idempotencyKey") or data.get("idempotency_key")
    sandbox = bool(data.get("sandbox") or data.get("isSandbox"))
    return (str(key) if key else None), sandbox


def _send_headers(payload: SendEmailPayload | Mapping[str, object]) -> dict[str, str]:
    if isinstance(payload, SendEmailPayload):
        return send_headers(payload.idempotency_key, payload.sandbox)
    key, sandbox = _header_fields(dict(payload))
    return send_headers(key, sandbox)


def _build_send_payload(payload: SendEmailPayload | Mapping[str, object]) -> dict[str, object]:
    data = (
        payload.model_dump(by_alias=True, exclude_none=True)
        if isinstance(payload, SendEmailPayload)
        else dict(payload)
    )
    for key in _HEADER_ONLY_KEYS:
        data.pop(key, None)

    from_val = data.get("from") or data.get("from_address")
    if from_val:
        data["from"] = _normalize_participant(from_val)  # type: ignore
        data.pop("from_address", None)

    to_val = data.get("to")
    if to_val:
        data["to"] = _normalize_participants(to_val)  # type: ignore

    for key in ("cc", "bcc"):
        if data.get(key):
            data[key] = _normalize_participants(data.pop(key))  # type: ignore

    for key in ("replyTo", "reply_to"):
        if data.get(key):
            data["replyTo"] = _normalize_participant(data.pop(key))  # type: ignore

    if data.get("attachments"):
        data["attachments"] = [_serialize_attachment(a) for a in data["attachments"]]  # type: ignore

    return data


def _batch_headers(emails: Sequence[SendEmailPayload | Mapping[str, object]]) -> dict[str, str]:
    merged: dict[str, str] = {}
    for email in emails:
        merged.update(_send_headers(email))
    return merged


def _list_params(
    limit: int | None,
    after: str | None,
    status: str | None,
    recipient: str | None,
    tag: str | None,
    from_date: str | None,
    to_date: str | None,
) -> dict[str, object]:
    return compact(
        limit=limit,
        after=after,
        status=status,
        recipient=recipient,
        tag=tag,
        **{"from": from_date, "to": to_date},
    )


_BATCH_RESULTS_ADAPTER: TypeAdapter[list[BatchSendEmailResult]] = TypeAdapter(
    list[BatchSendEmailResult]
)


class Emails:
    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport

    def send(
        self, payload: SendEmailPayload | Mapping[str, object]
    ) -> CoffeeMailResponse[SendEmailResponse]:
        body = build_input(lambda: _build_send_payload(payload), self._transport.locale)
        if isinstance(body, ValidationError):
            return input_failure(body)
        res = self._transport.request(
            "POST", "/v1/product/emails", json_data=body, headers=_send_headers(payload)
        )
        return parse_model(res, SendEmailResponse, self._transport.locale)

    def send_batch(
        self, emails: Sequence[SendEmailPayload | Mapping[str, object]]
    ) -> CoffeeMailResponse[list[BatchSendEmailResult]]:
        body = build_input(lambda: [_build_send_payload(e) for e in emails], self._transport.locale)
        if isinstance(body, ValidationError):
            return input_failure(body)
        res = self._transport.request_list(
            "POST", "/v1/product/emails/batch", json_data=body, headers=_batch_headers(emails)
        )
        return parse_adapter(res, _BATCH_RESULTS_ADAPTER, self._transport.locale)

    def get(self, email_id: str) -> CoffeeMailResponse[EmailDetail]:
        res = self._transport.request("GET", f"/v1/product/emails/{email_id}")
        return parse_model(res, EmailDetail, self._transport.locale)

    def list(
        self,
        limit: int | None = None,
        after: str | None = None,
        status: str | None = None,
        *,
        recipient: str | None = None,
        tag: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> CoffeeMailResponse[ListEmailsResponse]:
        params = _list_params(limit, after, status, recipient, tag, from_date, to_date)
        res = self._transport.request("GET", "/v1/product/emails", params=params)
        return parse_model(res, ListEmailsResponse, self._transport.locale)

    def cancel(self, email_id: str) -> CoffeeMailResponse[dict[str, object]]:
        return self._transport.request("POST", f"/v1/product/emails/{email_id}/cancel")

    def get_events(self, email_id: str) -> CoffeeMailResponse[EmailEventsResponse]:
        res = self._transport.request("GET", f"/v1/product/emails/{email_id}/events")
        return parse_model(res, EmailEventsResponse, self._transport.locale)

    def get_tags(self) -> CoffeeMailResponse[ListEmailTagsResponse]:
        res = self._transport.request("GET", "/v1/product/emails/tags")
        return parse_model(res, ListEmailTagsResponse, self._transport.locale)

    def resend(self, email_id: str) -> CoffeeMailResponse[SendEmailResponse]:
        res = self._transport.request("POST", f"/v1/product/emails/{email_id}/resend")
        return parse_model(res, SendEmailResponse, self._transport.locale)


class AsyncEmails:
    def __init__(self, transport: AsyncHttpTransport) -> None:
        self._transport = transport

    async def send(
        self, payload: SendEmailPayload | Mapping[str, object]
    ) -> CoffeeMailResponse[SendEmailResponse]:
        body = build_input(lambda: _build_send_payload(payload), self._transport.locale)
        if isinstance(body, ValidationError):
            return input_failure(body)
        res = await self._transport.request(
            "POST", "/v1/product/emails", json_data=body, headers=_send_headers(payload)
        )
        return parse_model(res, SendEmailResponse, self._transport.locale)

    async def send_batch(
        self, emails: Sequence[SendEmailPayload | Mapping[str, object]]
    ) -> CoffeeMailResponse[list[BatchSendEmailResult]]:
        body = build_input(lambda: [_build_send_payload(e) for e in emails], self._transport.locale)
        if isinstance(body, ValidationError):
            return input_failure(body)
        res = await self._transport.request_list(
            "POST", "/v1/product/emails/batch", json_data=body, headers=_batch_headers(emails)
        )
        return parse_adapter(res, _BATCH_RESULTS_ADAPTER, self._transport.locale)

    async def get(self, email_id: str) -> CoffeeMailResponse[EmailDetail]:
        res = await self._transport.request("GET", f"/v1/product/emails/{email_id}")
        return parse_model(res, EmailDetail, self._transport.locale)

    async def list(
        self,
        limit: int | None = None,
        after: str | None = None,
        status: str | None = None,
        *,
        recipient: str | None = None,
        tag: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> CoffeeMailResponse[ListEmailsResponse]:
        params = _list_params(limit, after, status, recipient, tag, from_date, to_date)
        res = await self._transport.request("GET", "/v1/product/emails", params=params)
        return parse_model(res, ListEmailsResponse, self._transport.locale)

    async def cancel(self, email_id: str) -> CoffeeMailResponse[dict[str, object]]:
        return await self._transport.request("POST", f"/v1/product/emails/{email_id}/cancel")

    async def get_events(self, email_id: str) -> CoffeeMailResponse[EmailEventsResponse]:
        res = await self._transport.request("GET", f"/v1/product/emails/{email_id}/events")
        return parse_model(res, EmailEventsResponse, self._transport.locale)

    async def get_tags(self) -> CoffeeMailResponse[ListEmailTagsResponse]:
        res = await self._transport.request("GET", "/v1/product/emails/tags")
        return parse_model(res, ListEmailTagsResponse, self._transport.locale)

    async def resend(self, email_id: str) -> CoffeeMailResponse[SendEmailResponse]:
        res = await self._transport.request("POST", f"/v1/product/emails/{email_id}/resend")
        return parse_model(res, SendEmailResponse, self._transport.locale)
