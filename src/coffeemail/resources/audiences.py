import builtins
from collections.abc import Mapping, Sequence

from coffeemail.core.errors import ValidationError
from coffeemail.core.http import AsyncHttpTransport, HttpTransport
from coffeemail.core.types import CoffeeMailResponse
from coffeemail.models.audiences import (
    AudienceDetail,
    BulkAddContactsResponse,
    ContactDetail,
    ContactInput,
    ListAudiencesResponse,
    ListContactsResponse,
    UpdateResult,
)
from coffeemail.resources._common import build_input, compact, input_failure, parse_model

ContactLike = ContactInput | Mapping[str, object]


def _contacts_path(audience_id: str) -> str:
    return f"/v1/product/audiences/{audience_id}/contacts"


def _contact_path(audience_id: str, contact_id: str) -> str:
    return f"{_contacts_path(audience_id)}/{contact_id}"


def _contact_body(
    email: str,
    first_name: str | None,
    last_name: str | None,
    metadata: Mapping[str, object] | None,
) -> dict[str, object]:
    return compact(
        email=email.strip(),
        firstName=first_name,
        lastName=last_name,
        metadata=dict(metadata) if metadata is not None else None,
    )


def _serialize_contact(contact: ContactLike) -> dict[str, object]:
    model = contact if isinstance(contact, ContactInput) else ContactInput.model_validate(contact)
    return model.model_dump(by_alias=True, exclude_none=True)


def _bulk_body(contacts: Sequence[ContactLike]) -> dict[str, object]:
    return {"contacts": [_serialize_contact(c) for c in contacts]}


def _offset_params(limit: int | None, offset: int | None) -> dict[str, object]:
    return compact(limit=limit, offset=offset)


class Contacts:
    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport

    def list(
        self, audience_id: str, limit: int | None = None, offset: int | None = None
    ) -> CoffeeMailResponse[ListContactsResponse]:
        res = self._transport.request(
            "GET", _contacts_path(audience_id), params=_offset_params(limit, offset)
        )
        return parse_model(res, ListContactsResponse, self._transport.locale)

    def create(
        self,
        audience_id: str,
        email: str,
        *,
        first_name: str | None = None,
        last_name: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> CoffeeMailResponse[ContactDetail]:
        body = _contact_body(email, first_name, last_name, metadata)
        res = self._transport.request("POST", _contacts_path(audience_id), json_data=body)
        return parse_model(res, ContactDetail, self._transport.locale)

    def bulk_add(
        self, audience_id: str, contacts: Sequence[ContactLike]
    ) -> CoffeeMailResponse[BulkAddContactsResponse]:
        body = build_input(lambda: _bulk_body(contacts), self._transport.locale)
        if isinstance(body, ValidationError):
            return input_failure(body)
        res = self._transport.request("POST", f"{_contacts_path(audience_id)}/bulk", json_data=body)
        return parse_model(res, BulkAddContactsResponse, self._transport.locale)

    def update(
        self,
        audience_id: str,
        contact_id: str,
        *,
        first_name: str | None = None,
        last_name: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> CoffeeMailResponse[UpdateResult]:
        body = compact(
            firstName=first_name,
            lastName=last_name,
            metadata=dict(metadata) if metadata is not None else None,
        )
        res = self._transport.request("PUT", _contact_path(audience_id, contact_id), json_data=body)
        return parse_model(res, UpdateResult, self._transport.locale)

    def delete(self, audience_id: str, contact_id: str) -> CoffeeMailResponse[dict[str, object]]:
        return self._transport.request("DELETE", _contact_path(audience_id, contact_id))


class Audiences:
    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport
        self.contacts = Contacts(transport)

    def list(
        self, limit: int | None = None, offset: int | None = None
    ) -> CoffeeMailResponse[ListAudiencesResponse]:
        res = self._transport.request(
            "GET", "/v1/product/audiences", params=_offset_params(limit, offset)
        )
        return parse_model(res, ListAudiencesResponse, self._transport.locale)

    def get(self, audience_id: str) -> CoffeeMailResponse[AudienceDetail]:
        res = self._transport.request("GET", f"/v1/product/audiences/{audience_id}")
        return parse_model(res, AudienceDetail, self._transport.locale)

    def create(
        self, name: str, description: str | None = None
    ) -> CoffeeMailResponse[AudienceDetail]:
        body = compact(name=name.strip(), description=description)
        res = self._transport.request("POST", "/v1/product/audiences", json_data=body)
        return parse_model(res, AudienceDetail, self._transport.locale)

    def update(
        self,
        audience_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        active: bool | None = None,
    ) -> CoffeeMailResponse[UpdateResult]:
        body = compact(name=name, description=description, active=active)
        res = self._transport.request("PUT", f"/v1/product/audiences/{audience_id}", json_data=body)
        return parse_model(res, UpdateResult, self._transport.locale)

    def delete(self, audience_id: str) -> CoffeeMailResponse[dict[str, object]]:
        return self._transport.request("DELETE", f"/v1/product/audiences/{audience_id}")

    def list_contacts(
        self, audience_id: str, limit: int | None = None, offset: int | None = None
    ) -> CoffeeMailResponse[ListContactsResponse]:
        return self.contacts.list(audience_id, limit=limit, offset=offset)

    def create_contact(
        self,
        audience_id: str,
        email: str,
        *,
        first_name: str | None = None,
        last_name: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> CoffeeMailResponse[ContactDetail]:
        return self.contacts.create(
            audience_id, email, first_name=first_name, last_name=last_name, metadata=metadata
        )

    def bulk_add_contacts(
        self, audience_id: str, contacts: builtins.list[ContactLike]
    ) -> CoffeeMailResponse[BulkAddContactsResponse]:
        return self.contacts.bulk_add(audience_id, contacts)

    def update_contact(
        self,
        audience_id: str,
        contact_id: str,
        *,
        first_name: str | None = None,
        last_name: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> CoffeeMailResponse[UpdateResult]:
        return self.contacts.update(
            audience_id, contact_id, first_name=first_name, last_name=last_name, metadata=metadata
        )


class AsyncContacts:
    def __init__(self, transport: AsyncHttpTransport) -> None:
        self._transport = transport

    async def list(
        self, audience_id: str, limit: int | None = None, offset: int | None = None
    ) -> CoffeeMailResponse[ListContactsResponse]:
        res = await self._transport.request(
            "GET", _contacts_path(audience_id), params=_offset_params(limit, offset)
        )
        return parse_model(res, ListContactsResponse, self._transport.locale)

    async def create(
        self,
        audience_id: str,
        email: str,
        *,
        first_name: str | None = None,
        last_name: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> CoffeeMailResponse[ContactDetail]:
        body = _contact_body(email, first_name, last_name, metadata)
        res = await self._transport.request("POST", _contacts_path(audience_id), json_data=body)
        return parse_model(res, ContactDetail, self._transport.locale)

    async def bulk_add(
        self, audience_id: str, contacts: Sequence[ContactLike]
    ) -> CoffeeMailResponse[BulkAddContactsResponse]:
        body = build_input(lambda: _bulk_body(contacts), self._transport.locale)
        if isinstance(body, ValidationError):
            return input_failure(body)
        res = await self._transport.request(
            "POST", f"{_contacts_path(audience_id)}/bulk", json_data=body
        )
        return parse_model(res, BulkAddContactsResponse, self._transport.locale)

    async def update(
        self,
        audience_id: str,
        contact_id: str,
        *,
        first_name: str | None = None,
        last_name: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> CoffeeMailResponse[UpdateResult]:
        body = compact(
            firstName=first_name,
            lastName=last_name,
            metadata=dict(metadata) if metadata is not None else None,
        )
        res = await self._transport.request(
            "PUT", _contact_path(audience_id, contact_id), json_data=body
        )
        return parse_model(res, UpdateResult, self._transport.locale)

    async def delete(
        self, audience_id: str, contact_id: str
    ) -> CoffeeMailResponse[dict[str, object]]:
        return await self._transport.request("DELETE", _contact_path(audience_id, contact_id))


class AsyncAudiences:
    def __init__(self, transport: AsyncHttpTransport) -> None:
        self._transport = transport
        self.contacts = AsyncContacts(transport)

    async def list(
        self, limit: int | None = None, offset: int | None = None
    ) -> CoffeeMailResponse[ListAudiencesResponse]:
        res = await self._transport.request(
            "GET", "/v1/product/audiences", params=_offset_params(limit, offset)
        )
        return parse_model(res, ListAudiencesResponse, self._transport.locale)

    async def get(self, audience_id: str) -> CoffeeMailResponse[AudienceDetail]:
        res = await self._transport.request("GET", f"/v1/product/audiences/{audience_id}")
        return parse_model(res, AudienceDetail, self._transport.locale)

    async def create(
        self, name: str, description: str | None = None
    ) -> CoffeeMailResponse[AudienceDetail]:
        body = compact(name=name.strip(), description=description)
        res = await self._transport.request("POST", "/v1/product/audiences", json_data=body)
        return parse_model(res, AudienceDetail, self._transport.locale)

    async def update(
        self,
        audience_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        active: bool | None = None,
    ) -> CoffeeMailResponse[UpdateResult]:
        body = compact(name=name, description=description, active=active)
        res = await self._transport.request(
            "PUT", f"/v1/product/audiences/{audience_id}", json_data=body
        )
        return parse_model(res, UpdateResult, self._transport.locale)

    async def delete(self, audience_id: str) -> CoffeeMailResponse[dict[str, object]]:
        return await self._transport.request("DELETE", f"/v1/product/audiences/{audience_id}")

    async def list_contacts(
        self, audience_id: str, limit: int | None = None, offset: int | None = None
    ) -> CoffeeMailResponse[ListContactsResponse]:
        return await self.contacts.list(audience_id, limit=limit, offset=offset)

    async def create_contact(
        self,
        audience_id: str,
        email: str,
        *,
        first_name: str | None = None,
        last_name: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> CoffeeMailResponse[ContactDetail]:
        return await self.contacts.create(
            audience_id, email, first_name=first_name, last_name=last_name, metadata=metadata
        )

    async def bulk_add_contacts(
        self, audience_id: str, contacts: builtins.list[ContactLike]
    ) -> CoffeeMailResponse[BulkAddContactsResponse]:
        return await self.contacts.bulk_add(audience_id, contacts)

    async def update_contact(
        self,
        audience_id: str,
        contact_id: str,
        *,
        first_name: str | None = None,
        last_name: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> CoffeeMailResponse[UpdateResult]:
        return await self.contacts.update(
            audience_id, contact_id, first_name=first_name, last_name=last_name, metadata=metadata
        )
