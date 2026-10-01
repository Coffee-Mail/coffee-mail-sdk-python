from coffeemail.core.http import AsyncHttpTransport, HttpTransport
from coffeemail.core.types import CoffeeMailResponse
from coffeemail.models.stats import EmailStats


class Stats:
    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport

    def get(
        self,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> CoffeeMailResponse[EmailStats]:
        params: dict[str, object] = {}
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date

        res = self._transport.request("GET", "/v1/product/stats", params=params)
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=EmailStats.model_validate(res.data), error=None, status_code=res.status_code
        )


class AsyncStats:
    def __init__(self, transport: AsyncHttpTransport) -> None:
        self._transport = transport

    async def get(
        self,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> CoffeeMailResponse[EmailStats]:
        params: dict[str, object] = {}
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date

        res = await self._transport.request("GET", "/v1/product/stats", params=params)
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=EmailStats.model_validate(res.data), error=None, status_code=res.status_code
        )
