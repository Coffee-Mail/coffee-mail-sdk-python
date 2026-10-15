from coffeemail.core.http import AsyncHttpTransport, HttpTransport
from coffeemail.core.i18n import Locale
from coffeemail.core.parsing import M
from coffeemail.core.types import CoffeeMailResponse
from coffeemail.models.domains import (
    CreateDomainResponse,
    CustomHostStatus,
    DkimRotation,
    DomainDetail,
    DomainHealthResponse,
    DomainWarmupStatus,
    ListDomainsResponse,
)
from coffeemail.resources._common import parse_model


def _optional_model(
    res: CoffeeMailResponse[dict[str, object]], model: type[M], locale: Locale
) -> CoffeeMailResponse[M | None]:
    if res.error is None and not res.data:
        return CoffeeMailResponse(data=None, error=None, status_code=res.status_code)
    parsed = parse_model(res, model, locale)
    return CoffeeMailResponse(data=parsed.data, error=parsed.error, status_code=parsed.status_code)


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
        return _optional_model(res, DomainWarmupStatus, self._transport.locale)

    def rotate_dkim(self, domain_id: str) -> CoffeeMailResponse[DkimRotation]:
        """Inicia (ou devolve, se já pendente) a rotação da chave DKIM do domínio verificado.

        Publique ``record`` no DNS; a chave em uso só muda quando o novo seletor propagar.
        """
        res = self._transport.request("POST", f"/v1/product/domains/{domain_id}/dkim/rotate")
        return parse_model(res, DkimRotation, self._transport.locale)

    def set_tracking_domain(
        self, domain_id: str, host: str
    ) -> CoffeeMailResponse[CustomHostStatus]:
        """Define o host próprio (subdomínio do domínio de envio) dos links de abertura e clique."""
        res = self._transport.request(
            "PUT",
            f"/v1/product/domains/{domain_id}/tracking-domain",
            json_data={"host": host.strip()},
        )
        return parse_model(res, CustomHostStatus, self._transport.locale)

    def remove_tracking_domain(self, domain_id: str) -> CoffeeMailResponse[CustomHostStatus | None]:
        """Remove o host de tracking próprio; ``data`` é ``None`` quando não havia host."""
        res = self._transport.request("DELETE", f"/v1/product/domains/{domain_id}/tracking-domain")
        return _optional_model(res, CustomHostStatus, self._transport.locale)


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
        return _optional_model(res, DomainWarmupStatus, self._transport.locale)

    async def rotate_dkim(self, domain_id: str) -> CoffeeMailResponse[DkimRotation]:
        """Inicia (ou devolve, se já pendente) a rotação da chave DKIM do domínio verificado.

        Publique ``record`` no DNS; a chave em uso só muda quando o novo seletor propagar.
        """
        res = await self._transport.request("POST", f"/v1/product/domains/{domain_id}/dkim/rotate")
        return parse_model(res, DkimRotation, self._transport.locale)

    async def set_tracking_domain(
        self, domain_id: str, host: str
    ) -> CoffeeMailResponse[CustomHostStatus]:
        """Define o host próprio (subdomínio do domínio de envio) dos links de abertura e clique."""
        res = await self._transport.request(
            "PUT",
            f"/v1/product/domains/{domain_id}/tracking-domain",
            json_data={"host": host.strip()},
        )
        return parse_model(res, CustomHostStatus, self._transport.locale)

    async def remove_tracking_domain(
        self, domain_id: str
    ) -> CoffeeMailResponse[CustomHostStatus | None]:
        """Remove o host de tracking próprio; ``data`` é ``None`` quando não havia host."""
        res = await self._transport.request(
            "DELETE", f"/v1/product/domains/{domain_id}/tracking-domain"
        )
        return _optional_model(res, CustomHostStatus, self._transport.locale)
