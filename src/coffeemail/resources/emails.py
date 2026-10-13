import base64
import re
from collections.abc import Sequence
from pathlib import Path

from pydantic import TypeAdapter

from coffeemail.core.errors import ValidationError
from coffeemail.core.http import AsyncHttpTransport, HttpTransport
from coffeemail.core.types import CoffeeMailResponse
from coffeemail.models.emails import (
    BatchSendEmailResult,
    EmailAttachment,
    EmailDetail,
    EmailParticipant,
    ListEmailsResponse,
    SendEmailPayload,
    SendEmailResponse,
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

    raise ValidationError(
        "Destinatário inválido. Forneça uma string com e-mail ou objeto com campo 'email'."
    )


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
    return None


def _attachment_fields(
    attachment: EmailAttachment | dict[str, object],
) -> tuple[str, object, str, str, str | None]:
    if isinstance(attachment, dict):
        return (
            str(attachment["filename"]),
            attachment["content"],
            str(attachment.get("contentType", "application/octet-stream")),
            str(attachment.get("disposition", "attachment")),
            str(attachment.get("cid")) if attachment.get("cid") else None,
        )
    return (
        attachment.filename,
        attachment.content,
        attachment.content_type or "application/octet-stream",
        attachment.disposition or "attachment",
        attachment.cid,
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


def _build_send_payload(payload: SendEmailPayload | dict[str, object]) -> dict[str, object]:
    data = (
        payload.model_dump(by_alias=True, exclude_none=True)
        if isinstance(payload, SendEmailPayload)
        else payload.copy()
    )

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


_BATCH_RESULTS_ADAPTER: TypeAdapter[list[BatchSendEmailResult]] = TypeAdapter(
    list[BatchSendEmailResult]
)


class Emails:
    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport

    def send(
        self, payload: SendEmailPayload | dict[str, object]
    ) -> CoffeeMailResponse[SendEmailResponse]:
        body = _build_send_payload(payload)
        res = self._transport.request("POST", "/v1/product/emails", json_data=body)
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=SendEmailResponse.model_validate(res.data), error=None, status_code=res.status_code
        )

    def send_batch(
        self, emails: list[SendEmailPayload | dict[str, object]]
    ) -> CoffeeMailResponse[list[BatchSendEmailResult]]:
        body: list[object] = [_build_send_payload(e) for e in emails]
        res = self._transport.request_list("POST", "/v1/product/emails/batch", json_data=body)
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=_BATCH_RESULTS_ADAPTER.validate_python(res.data),
            error=None,
            status_code=res.status_code,
        )

    def get(self, email_id: str) -> CoffeeMailResponse[EmailDetail]:
        res = self._transport.request("GET", f"/v1/product/emails/{email_id}")
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=EmailDetail.model_validate(res.data), error=None, status_code=res.status_code
        )

    def list(
        self,
        limit: int | None = None,
        after: str | None = None,
        status: str | None = None,
    ) -> CoffeeMailResponse[ListEmailsResponse]:
        params: dict[str, object] = {}
        if limit is not None:
            params["limit"] = limit
        if after is not None:
            params["after"] = after
        if status is not None:
            params["status"] = status

        res = self._transport.request("GET", "/v1/product/emails", params=params)
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=ListEmailsResponse.model_validate(res.data),
            error=None,
            status_code=res.status_code,
        )

    def cancel(self, email_id: str) -> CoffeeMailResponse[dict[str, object]]:
        return self._transport.request("POST", f"/v1/product/emails/{email_id}/cancel")

    def get_events(self, email_id: str) -> CoffeeMailResponse[dict[str, object]]:
        return self._transport.request("GET", f"/v1/product/emails/{email_id}/events")

    def get_tags(self) -> CoffeeMailResponse[dict[str, object]]:
        return self._transport.request("GET", "/v1/product/emails/tags")

    def resend(self, email_id: str) -> CoffeeMailResponse[dict[str, object]]:
        return self._transport.request("POST", f"/v1/product/emails/{email_id}/resend")


class AsyncEmails:
    def __init__(self, transport: AsyncHttpTransport) -> None:
        self._transport = transport

    async def send(
        self, payload: SendEmailPayload | dict[str, object]
    ) -> CoffeeMailResponse[SendEmailResponse]:
        body = _build_send_payload(payload)
        res = await self._transport.request("POST", "/v1/product/emails", json_data=body)
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=SendEmailResponse.model_validate(res.data), error=None, status_code=res.status_code
        )

    async def send_batch(
        self, emails: list[SendEmailPayload | dict[str, object]]
    ) -> CoffeeMailResponse[list[BatchSendEmailResult]]:
        body: list[object] = [_build_send_payload(e) for e in emails]
        res = await self._transport.request_list("POST", "/v1/product/emails/batch", json_data=body)
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=_BATCH_RESULTS_ADAPTER.validate_python(res.data),
            error=None,
            status_code=res.status_code,
        )

    async def get(self, email_id: str) -> CoffeeMailResponse[EmailDetail]:
        res = await self._transport.request("GET", f"/v1/product/emails/{email_id}")
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=EmailDetail.model_validate(res.data), error=None, status_code=res.status_code
        )

    async def list(
        self,
        limit: int | None = None,
        after: str | None = None,
        status: str | None = None,
    ) -> CoffeeMailResponse[ListEmailsResponse]:
        params: dict[str, object] = {}
        if limit is not None:
            params["limit"] = limit
        if after is not None:
            params["after"] = after
        if status is not None:
            params["status"] = status

        res = await self._transport.request("GET", "/v1/product/emails", params=params)
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=ListEmailsResponse.model_validate(res.data),
            error=None,
            status_code=res.status_code,
        )

    async def cancel(self, email_id: str) -> CoffeeMailResponse[dict[str, object]]:
        return await self._transport.request("POST", f"/v1/product/emails/{email_id}/cancel")

    async def get_events(self, email_id: str) -> CoffeeMailResponse[dict[str, object]]:
        return await self._transport.request("GET", f"/v1/product/emails/{email_id}/events")

    async def get_tags(self) -> CoffeeMailResponse[dict[str, object]]:
        return await self._transport.request("GET", "/v1/product/emails/tags")

    async def resend(self, email_id: str) -> CoffeeMailResponse[dict[str, object]]:
        return await self._transport.request("POST", f"/v1/product/emails/{email_id}/resend")
