import builtins

from coffeemail.core.http import AsyncHttpTransport, HttpTransport
from coffeemail.core.types import CoffeeMailResponse
from coffeemail.models.suppressions import (
    CheckSuppressionResponse,
    ListSuppressionsResponse,
    SuppressionDetail,
    SuppressionReason,
)


class Suppressions:
    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport

    def list(
        self,
        limit: int | None = None,
        after: str | None = None,
    ) -> CoffeeMailResponse[ListSuppressionsResponse]:
        params: dict[str, object] = {}
        if limit is not None:
            params["limit"] = limit
        if after is not None:
            params["after"] = after

        res = self._transport.request("GET", "/v1/product/suppressions", params=params)
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=ListSuppressionsResponse.model_validate(res.data),
            error=None,
            status_code=res.status_code,
        )

    def check(self, email: str) -> CoffeeMailResponse[CheckSuppressionResponse]:
        res = self._transport.request("GET", f"/v1/product/suppressions/{email.strip()}")
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=CheckSuppressionResponse.model_validate(res.data),
            error=None,
            status_code=res.status_code,
        )

    def create(
        self, email: str, reason: SuppressionReason = "manual"
    ) -> CoffeeMailResponse[SuppressionDetail]:
        res = self._transport.request(
            "POST", "/v1/product/suppressions", json_data={"email": email.strip(), "reason": reason}
        )
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=SuppressionDetail.model_validate(res.data), error=None, status_code=res.status_code
        )

    def delete(self, email: str) -> CoffeeMailResponse[dict[str, object]]:
        return self._transport.request("DELETE", f"/v1/product/suppressions/{email.strip()}")

    def reactivate(self, suppression_id: str) -> CoffeeMailResponse[dict[str, object]]:
        return self._transport.request(
            "POST", f"/v1/product/suppressions/{suppression_id}/reactivate"
        )

    def bulk_create(
        self, suppressions: builtins.list[dict[str, object]]
    ) -> CoffeeMailResponse[dict[str, object]]:
        return self._transport.request(
            "POST", "/v1/product/suppressions/bulk", json_data={"suppressions": suppressions}
        )


class AsyncSuppressions:
    def __init__(self, transport: AsyncHttpTransport) -> None:
        self._transport = transport

    async def list(
        self,
        limit: int | None = None,
        after: str | None = None,
    ) -> CoffeeMailResponse[ListSuppressionsResponse]:
        params: dict[str, object] = {}
        if limit is not None:
            params["limit"] = limit
        if after is not None:
            params["after"] = after

        res = await self._transport.request("GET", "/v1/product/suppressions", params=params)
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=ListSuppressionsResponse.model_validate(res.data),
            error=None,
            status_code=res.status_code,
        )

    async def check(self, email: str) -> CoffeeMailResponse[CheckSuppressionResponse]:
        res = await self._transport.request("GET", f"/v1/product/suppressions/{email.strip()}")
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=CheckSuppressionResponse.model_validate(res.data),
            error=None,
            status_code=res.status_code,
        )

    async def create(
        self, email: str, reason: SuppressionReason = "manual"
    ) -> CoffeeMailResponse[SuppressionDetail]:
        res = await self._transport.request(
            "POST", "/v1/product/suppressions", json_data={"email": email.strip(), "reason": reason}
        )
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=SuppressionDetail.model_validate(res.data), error=None, status_code=res.status_code
        )

    async def delete(self, email: str) -> CoffeeMailResponse[dict[str, object]]:
        return await self._transport.request("DELETE", f"/v1/product/suppressions/{email.strip()}")

    async def reactivate(self, suppression_id: str) -> CoffeeMailResponse[dict[str, object]]:
        return await self._transport.request(
            "POST", f"/v1/product/suppressions/{suppression_id}/reactivate"
        )

    async def bulk_create(
        self, suppressions: builtins.list[dict[str, object]]
    ) -> CoffeeMailResponse[dict[str, object]]:
        return await self._transport.request(
            "POST", "/v1/product/suppressions/bulk", json_data={"suppressions": suppressions}
        )
