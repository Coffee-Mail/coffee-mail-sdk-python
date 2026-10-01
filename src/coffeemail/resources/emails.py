import base64
from collections.abc import Sequence
from pathlib import Path

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


def _normalize_participant(
    item: str | EmailParticipant | dict[str, object],
) -> dict[str, object]:
    if isinstance(item, str):
        return {"email": item.strip()}
    if isinstance(item, EmailParticipant):
        payload: dict[str, object] = {"email": item.email.strip()}
        if item.name:
            payload["name"] = item.name.strip()
        return payload
    if isinstance(item, dict) and "email" in item:
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


def _serialize_attachment(
    attachment: EmailAttachment | dict[str, object],
) -> dict[str, object]:
    if isinstance(attachment, dict):
        filename = str(attachment["filename"])
        raw_content = attachment["content"]
        content_type = str(attachment.get("contentType", "application/octet-stream"))
        disposition = str(attachment.get("disposition", "attachment"))
        cid = str(attachment.get("cid")) if attachment.get("cid") else None
    else:
        filename = attachment.filename
        raw_content = attachment.content
        content_type = attachment.content_type or "application/octet-stream"
        disposition = attachment.disposition or "attachment"
        cid = attachment.cid

    if isinstance(raw_content, bytes):
        content = base64.b64encode(raw_content).decode("ascii")
    elif isinstance(raw_content, str):
        if Path(raw_content).is_file():
            content = base64.b64encode(Path(raw_content).read_bytes()).decode("ascii")
        else:
            content = raw_content
    else:
        content = str(raw_content)

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
        normalized_to = _normalize_participants(to_val)  # type: ignore
        data["to"] = (
            normalized_to[0] if normalized_to and len(normalized_to) == 1 else normalized_to
        )

    for key in ("cc", "bcc", "replyTo", "reply_to"):
        if data.get(key):
            target = "replyTo" if "reply" in key else key
            data[target] = _normalize_participants(data.pop(key))  # type: ignore

    if data.get("attachments"):
        data["attachments"] = [_serialize_attachment(a) for a in data["attachments"]]  # type: ignore

    return data


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
    ) -> CoffeeMailResponse[BatchSendEmailResult]:
        body = {"items": [_build_send_payload(e) for e in emails]}
        res = self._transport.request("POST", "/v1/product/emails/batch", json_data=body)
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=BatchSendEmailResult.model_validate(res.data),
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
    ) -> CoffeeMailResponse[BatchSendEmailResult]:
        body = {"items": [_build_send_payload(e) for e in emails]}
        res = await self._transport.request("POST", "/v1/product/emails/batch", json_data=body)
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=BatchSendEmailResult.model_validate(res.data),
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
