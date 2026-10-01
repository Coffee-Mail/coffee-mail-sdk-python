from coffeemail.core.http import AsyncHttpTransport, HttpTransport
from coffeemail.core.types import CoffeeMailResponse
from coffeemail.models.domains import (
    CreateDomainResponse,
    DomainDetail,
    ListDomainsResponse,
)


class Domains:
    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport

    def list(self) -> CoffeeMailResponse[ListDomainsResponse]:
        res = self._transport.request("GET", "/v1/product/domains")
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=ListDomainsResponse.model_validate(res.data),
            error=None,
            status_code=res.status_code,
        )

    def get(self, domain_id: str) -> CoffeeMailResponse[DomainDetail]:
        res = self._transport.request("GET", f"/v1/product/domains/{domain_id}")
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=DomainDetail.model_validate(res.data), error=None, status_code=res.status_code
        )

    def create(self, name: str) -> CoffeeMailResponse[CreateDomainResponse]:
        res = self._transport.request(
            "POST", "/v1/product/domains", json_data={"name": name.strip()}
        )
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=CreateDomainResponse.model_validate(res.data),
            error=None,
            status_code=res.status_code,
        )

    def verify(self, domain_id: str) -> CoffeeMailResponse[DomainDetail]:
        res = self._transport.request("POST", f"/v1/product/domains/{domain_id}/verify")
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=DomainDetail.model_validate(res.data), error=None, status_code=res.status_code
        )

    def delete(self, domain_id: str) -> CoffeeMailResponse[dict[str, object]]:
        return self._transport.request("DELETE", f"/v1/product/domains/{domain_id}")


class AsyncDomains:
    def __init__(self, transport: AsyncHttpTransport) -> None:
        self._transport = transport

    async def list(self) -> CoffeeMailResponse[ListDomainsResponse]:
        res = await self._transport.request("GET", "/v1/product/domains")
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=ListDomainsResponse.model_validate(res.data),
            error=None,
            status_code=res.status_code,
        )

    async def get(self, domain_id: str) -> CoffeeMailResponse[DomainDetail]:
        res = await self._transport.request("GET", f"/v1/product/domains/{domain_id}")
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=DomainDetail.model_validate(res.data), error=None, status_code=res.status_code
        )

    async def create(self, name: str) -> CoffeeMailResponse[CreateDomainResponse]:
        res = await self._transport.request(
            "POST", "/v1/product/domains", json_data={"name": name.strip()}
        )
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=CreateDomainResponse.model_validate(res.data),
            error=None,
            status_code=res.status_code,
        )

    async def verify(self, domain_id: str) -> CoffeeMailResponse[DomainDetail]:
        res = await self._transport.request("POST", f"/v1/product/domains/{domain_id}/verify")
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=DomainDetail.model_validate(res.data), error=None, status_code=res.status_code
        )

    async def delete(self, domain_id: str) -> CoffeeMailResponse[dict[str, object]]:
        return await self._transport.request("DELETE", f"/v1/product/domains/{domain_id}")
