from coffeemail.core.http import AsyncHttpTransport, HttpTransport
from coffeemail.core.types import CoffeeMailResponse
from coffeemail.models.domains import (
    CreateDomainResponse,
    DomainDetail,
    DomainHealthResponse,
    DomainWarmupStatus,
    ListDomainsResponse,
)
from coffeemail.resources._common import parse_model


class Domains:
    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport

    def list(self) -> CoffeeMailResponse[ListDomainsResponse]:
        res = self._transport.request("GET", "/v1/product/domains")
        return parse_model(res, ListDomainsResponse, self._transport.locale)

    def get(self, domain_id: str) -> CoffeeMailResponse[DomainDetail]:
        res = self._transport.request("GET", f"/v1/product/domains/{domain_id}")
        return parse_model(res, DomainDetail, self._transport.locale)

    def create(self, name: str) -> CoffeeMailResponse[CreateDomainResponse]:
        res = self._transport.request(
            "POST", "/v1/product/domains", json_data={"name": name.strip()}
        )
        return parse_model(res, CreateDomainResponse, self._transport.locale)

    def verify(self, domain_id: str) -> CoffeeMailResponse[DomainDetail]:
        res = self._transport.request("POST", f"/v1/product/domains/{domain_id}/verify")
        return parse_model(res, DomainDetail, self._transport.locale)

    def delete(self, domain_id: str) -> CoffeeMailResponse[dict[str, object]]:
        return self._transport.request("DELETE", f"/v1/product/domains/{domain_id}")

    def get_health(self, domain_id: str) -> CoffeeMailResponse[DomainHealthResponse]:
        res = self._transport.request("POST", f"/v1/product/domains/{domain_id}/health")
        return parse_model(res, DomainHealthResponse, self._transport.locale)

    def get_warmup_status(self, domain_id: str) -> CoffeeMailResponse[DomainWarmupStatus | None]:
        """Aquecimento do domínio; ``data`` é ``None`` quando não há aquecimento em andamento."""
        res = self._transport.request("GET", f"/v1/product/domains/{domain_id}/warmup")
        if res.error is None and not res.data:
            return CoffeeMailResponse(data=None, error=None, status_code=res.status_code)
        warmup = parse_model(res, DomainWarmupStatus, self._transport.locale)
        return CoffeeMailResponse(
            data=warmup.data, error=warmup.error, status_code=warmup.status_code
        )


class AsyncDomains:
    def __init__(self, transport: AsyncHttpTransport) -> None:
        self._transport = transport

    async def list(self) -> CoffeeMailResponse[ListDomainsResponse]:
        res = await self._transport.request("GET", "/v1/product/domains")
        return parse_model(res, ListDomainsResponse, self._transport.locale)

    async def get(self, domain_id: str) -> CoffeeMailResponse[DomainDetail]:
        res = await self._transport.request("GET", f"/v1/product/domains/{domain_id}")
        return parse_model(res, DomainDetail, self._transport.locale)

    async def create(self, name: str) -> CoffeeMailResponse[CreateDomainResponse]:
        res = await self._transport.request(
            "POST", "/v1/product/domains", json_data={"name": name.strip()}
        )
        return parse_model(res, CreateDomainResponse, self._transport.locale)

    async def verify(self, domain_id: str) -> CoffeeMailResponse[DomainDetail]:
        res = await self._transport.request("POST", f"/v1/product/domains/{domain_id}/verify")
        return parse_model(res, DomainDetail, self._transport.locale)

    async def delete(self, domain_id: str) -> CoffeeMailResponse[dict[str, object]]:
        return await self._transport.request("DELETE", f"/v1/product/domains/{domain_id}")

    async def get_health(self, domain_id: str) -> CoffeeMailResponse[DomainHealthResponse]:
        res = await self._transport.request("POST", f"/v1/product/domains/{domain_id}/health")
        return parse_model(res, DomainHealthResponse, self._transport.locale)

    async def get_warmup_status(
        self, domain_id: str
    ) -> CoffeeMailResponse[DomainWarmupStatus | None]:
        """Aquecimento do domínio; ``data`` é ``None`` quando não há aquecimento em andamento."""
        res = await self._transport.request("GET", f"/v1/product/domains/{domain_id}/warmup")
        if res.error is None and not res.data:
            return CoffeeMailResponse(data=None, error=None, status_code=res.status_code)
        warmup = parse_model(res, DomainWarmupStatus, self._transport.locale)
        return CoffeeMailResponse(
            data=warmup.data, error=warmup.error, status_code=warmup.status_code
        )
