import builtins

from coffeemail.core.http import AsyncHttpTransport, HttpTransport
from coffeemail.core.types import CoffeeMailResponse
from coffeemail.models.audiences import (
    AudienceDetail,
    BulkAddContactsResponse,
    ContactDetail,
    ListAudiencesResponse,
    ListContactsResponse,
)


class Contacts:
    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport

    def list(
        self,
        audience_id: str,
        limit: int | None = None,
        after: str | None = None,
    ) -> CoffeeMailResponse[ListContactsResponse]:
        params: dict[str, object] = {}
        if limit is not None:
            params["limit"] = limit
        if after is not None:
            params["after"] = after

        res = self._transport.request(
            "GET", f"/v1/product/audiences/{audience_id}/contacts", params=params
        )
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=ListContactsResponse.model_validate(res.data),
            error=None,
            status_code=res.status_code,
        )

    def create(
        self,
        audience_id: str,
        email: str,
        name: str | None = None,
        subscribed: bool = True,
        attributes: dict[str, object] | None = None,
    ) -> CoffeeMailResponse[ContactDetail]:
        body: dict[str, object] = {"email": email.strip(), "subscribed": subscribed}
        if name:
            body["name"] = name.strip()
        if attributes:
            body["attributes"] = attributes

        res = self._transport.request(
            "POST", f"/v1/product/audiences/{audience_id}/contacts", json_data=body
        )
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=ContactDetail.model_validate(res.data), error=None, status_code=res.status_code
        )

    def bulk_add(
        self,
        audience_id: str,
        contacts: builtins.list[dict[str, object]],
    ) -> CoffeeMailResponse[BulkAddContactsResponse]:
        res = self._transport.request(
            "POST",
            f"/v1/product/audiences/{audience_id}/contacts/bulk",
            json_data={"contacts": contacts},
        )
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=BulkAddContactsResponse.model_validate(res.data),
            error=None,
            status_code=res.status_code,
        )

    def delete(self, audience_id: str, contact_id: str) -> CoffeeMailResponse[dict[str, object]]:
        return self._transport.request(
            "DELETE", f"/v1/product/audiences/{audience_id}/contacts/{contact_id}"
        )

    def update(
        self, audience_id: str, contact_id: str, payload: dict[str, object]
    ) -> CoffeeMailResponse[dict[str, object]]:
        return self._transport.request(
            "PUT", f"/v1/product/audiences/{audience_id}/contacts/{contact_id}", json_data=payload
        )


class Audiences:
    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport
        self.contacts = Contacts(transport)

    def list(
        self,
        limit: int | None = None,
        after: str | None = None,
    ) -> CoffeeMailResponse[ListAudiencesResponse]:
        params: dict[str, object] = {}
        if limit is not None:
            params["limit"] = limit
        if after is not None:
            params["after"] = after

        res = self._transport.request("GET", "/v1/product/audiences", params=params)
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=ListAudiencesResponse.model_validate(res.data),
            error=None,
            status_code=res.status_code,
        )

    def get(self, audience_id: str) -> CoffeeMailResponse[AudienceDetail]:
        res = self._transport.request("GET", f"/v1/product/audiences/{audience_id}")
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=AudienceDetail.model_validate(res.data), error=None, status_code=res.status_code
        )

    def create(
        self, name: str, description: str | None = None
    ) -> CoffeeMailResponse[AudienceDetail]:
        body: dict[str, object] = {"name": name.strip()}
        if description:
            body["description"] = description.strip()

        res = self._transport.request("POST", "/v1/product/audiences", json_data=body)
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=AudienceDetail.model_validate(res.data), error=None, status_code=res.status_code
        )

    def delete(self, audience_id: str) -> CoffeeMailResponse[dict[str, object]]:
        return self._transport.request("DELETE", f"/v1/product/audiences/{audience_id}")

    def list_contacts(
        self, audience_id: str, limit: int | None = None, after: str | None = None
    ) -> CoffeeMailResponse[ListContactsResponse]:
        return self.contacts.list(audience_id, limit=limit, after=after)

    def create_contact(
        self,
        audience_id: str,
        email: str,
        name: str | None = None,
        subscribed: bool = True,
        attributes: dict[str, object] | None = None,
    ) -> CoffeeMailResponse[ContactDetail]:
        return self.contacts.create(
            audience_id, email=email, name=name, subscribed=subscribed, attributes=attributes
        )

    def bulk_add_contacts(
        self, audience_id: str, contacts: builtins.list[dict[str, object]]
    ) -> CoffeeMailResponse[BulkAddContactsResponse]:
        return self.contacts.bulk_add(audience_id, contacts)

    def update(
        self, audience_id: str, payload: dict[str, object]
    ) -> CoffeeMailResponse[dict[str, object]]:
        return self._transport.request(
            "PUT", f"/v1/product/audiences/{audience_id}", json_data=payload
        )

    def update_contact(
        self, audience_id: str, contact_id: str, payload: dict[str, object]
    ) -> CoffeeMailResponse[dict[str, object]]:
        return self._transport.request(
            "PUT", f"/v1/product/audiences/{audience_id}/contacts/{contact_id}", json_data=payload
        )


class AsyncContacts:
    def __init__(self, transport: AsyncHttpTransport) -> None:
        self._transport = transport

    async def list(
        self,
        audience_id: str,
        limit: int | None = None,
        after: str | None = None,
    ) -> CoffeeMailResponse[ListContactsResponse]:
        params: dict[str, object] = {}
        if limit is not None:
            params["limit"] = limit
        if after is not None:
            params["after"] = after

        res = await self._transport.request(
            "GET", f"/v1/product/audiences/{audience_id}/contacts", params=params
        )
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=ListContactsResponse.model_validate(res.data),
            error=None,
            status_code=res.status_code,
        )

    async def create(
        self,
        audience_id: str,
        email: str,
        name: str | None = None,
        subscribed: bool = True,
        attributes: dict[str, object] | None = None,
    ) -> CoffeeMailResponse[ContactDetail]:
        body: dict[str, object] = {"email": email.strip(), "subscribed": subscribed}
        if name:
            body["name"] = name.strip()
        if attributes:
            body["attributes"] = attributes

        res = await self._transport.request(
            "POST", f"/v1/product/audiences/{audience_id}/contacts", json_data=body
        )
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=ContactDetail.model_validate(res.data), error=None, status_code=res.status_code
        )

    async def bulk_add(
        self,
        audience_id: str,
        contacts: builtins.list[dict[str, object]],
    ) -> CoffeeMailResponse[BulkAddContactsResponse]:
        res = await self._transport.request(
            "POST",
            f"/v1/product/audiences/{audience_id}/contacts/bulk",
            json_data={"contacts": contacts},
        )
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=BulkAddContactsResponse.model_validate(res.data),
            error=None,
            status_code=res.status_code,
        )

    async def delete(
        self, audience_id: str, contact_id: str
    ) -> CoffeeMailResponse[dict[str, object]]:
        return await self._transport.request(
            "DELETE", f"/v1/product/audiences/{audience_id}/contacts/{contact_id}"
        )

    async def update(
        self, audience_id: str, contact_id: str, payload: dict[str, object]
    ) -> CoffeeMailResponse[dict[str, object]]:
        return await self._transport.request(
            "PUT", f"/v1/product/audiences/{audience_id}/contacts/{contact_id}", json_data=payload
        )


class AsyncAudiences:
    def __init__(self, transport: AsyncHttpTransport) -> None:
        self._transport = transport
        self.contacts = AsyncContacts(transport)

    async def list(
        self,
        limit: int | None = None,
        after: str | None = None,
    ) -> CoffeeMailResponse[ListAudiencesResponse]:
        params: dict[str, object] = {}
        if limit is not None:
            params["limit"] = limit
        if after is not None:
            params["after"] = after

        res = await self._transport.request("GET", "/v1/product/audiences", params=params)
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=ListAudiencesResponse.model_validate(res.data),
            error=None,
            status_code=res.status_code,
        )

    async def get(self, audience_id: str) -> CoffeeMailResponse[AudienceDetail]:
        res = await self._transport.request("GET", f"/v1/product/audiences/{audience_id}")
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=AudienceDetail.model_validate(res.data), error=None, status_code=res.status_code
        )

    async def create(
        self, name: str, description: str | None = None
    ) -> CoffeeMailResponse[AudienceDetail]:
        body: dict[str, object] = {"name": name.strip()}
        if description:
            body["description"] = description.strip()

        res = await self._transport.request("POST", "/v1/product/audiences", json_data=body)
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=AudienceDetail.model_validate(res.data), error=None, status_code=res.status_code
        )

    async def delete(self, audience_id: str) -> CoffeeMailResponse[dict[str, object]]:
        return await self._transport.request("DELETE", f"/v1/product/audiences/{audience_id}")

    async def list_contacts(
        self, audience_id: str, limit: int | None = None, after: str | None = None
    ) -> CoffeeMailResponse[ListContactsResponse]:
        return await self.contacts.list(audience_id, limit=limit, after=after)

    async def create_contact(
        self,
        audience_id: str,
        email: str,
        name: str | None = None,
        subscribed: bool = True,
        attributes: dict[str, object] | None = None,
    ) -> CoffeeMailResponse[ContactDetail]:
        return await self.contacts.create(
            audience_id, email=email, name=name, subscribed=subscribed, attributes=attributes
        )

    async def bulk_add_contacts(
        self, audience_id: str, contacts: builtins.list[dict[str, object]]
    ) -> CoffeeMailResponse[BulkAddContactsResponse]:
        return await self.contacts.bulk_add(audience_id, contacts)

    async def update(
        self, audience_id: str, payload: dict[str, object]
    ) -> CoffeeMailResponse[dict[str, object]]:
        return await self._transport.request(
            "PUT", f"/v1/product/audiences/{audience_id}", json_data=payload
        )

    async def update_contact(
        self, audience_id: str, contact_id: str, payload: dict[str, object]
    ) -> CoffeeMailResponse[dict[str, object]]:
        return await self._transport.request(
            "PUT", f"/v1/product/audiences/{audience_id}/contacts/{contact_id}", json_data=payload
        )
