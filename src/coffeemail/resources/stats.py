from coffeemail.core.http import AsyncHttpTransport, HttpTransport
from coffeemail.core.types import CoffeeMailResponse
from coffeemail.models.stats import EmailStats, StatsEmailType, StatsGranularity, StatsPeriod
from coffeemail.resources._common import compact, parse_model

STATS_PATH = "/v1/product/stats"


def _stats_params(
    start_date: str | None,
    end_date: str | None,
    domain_id: str | None,
    tag: str | None,
    granularity: StatsGranularity | None,
    period: StatsPeriod | None,
    email_type: StatsEmailType | None,
) -> dict[str, object]:
    return compact(
        startDate=start_date,
        endDate=end_date,
        domainId=domain_id,
        tag=tag,
        granularity=granularity,
        period=period,
        emailType=email_type,
    )


class Stats:
    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport

    def get(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        domain_id: str | None = None,
        tag: str | None = None,
        granularity: StatsGranularity | None = None,
        period: StatsPeriod | None = None,
        email_type: StatsEmailType | None = None,
    ) -> CoffeeMailResponse[EmailStats]:
        params = _stats_params(
            start_date, end_date, domain_id, tag, granularity, period, email_type
        )
        return parse_model(
            self._transport.request("GET", STATS_PATH, params=params),
            EmailStats,
            self._transport.locale,
        )


class AsyncStats:
    def __init__(self, transport: AsyncHttpTransport) -> None:
        self._transport = transport

    async def get(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        domain_id: str | None = None,
        tag: str | None = None,
        granularity: StatsGranularity | None = None,
        period: StatsPeriod | None = None,
        email_type: StatsEmailType | None = None,
    ) -> CoffeeMailResponse[EmailStats]:
        params = _stats_params(
            start_date, end_date, domain_id, tag, granularity, period, email_type
        )
        res = await self._transport.request("GET", STATS_PATH, params=params)
        return parse_model(res, EmailStats, self._transport.locale)
