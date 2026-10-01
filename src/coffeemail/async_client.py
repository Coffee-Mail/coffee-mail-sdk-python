import os

import httpx

from coffeemail.core.http import DEFAULT_TIMEOUT_SECONDS, AsyncHttpTransport
from coffeemail.core.i18n import Locale
from coffeemail.core.types import ApiKeyIntrospection, CoffeeMailResponse
from coffeemail.resources.audiences import AsyncAudiences
from coffeemail.resources.broadcasts import AsyncBroadcasts
from coffeemail.resources.domains import AsyncDomains
from coffeemail.resources.emails import AsyncEmails
from coffeemail.resources.stats import AsyncStats
from coffeemail.resources.suppressions import AsyncSuppressions
from coffeemail.resources.templates import AsyncTemplates
from coffeemail.resources.webhooks import AsyncWebhooks


class AsyncCoffeeMail:
    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        locale: Locale = "pt-BR",
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        resolved_key = api_key or os.getenv("COFFEEMAIL_API_KEY")
        self._transport = AsyncHttpTransport(
            api_key=resolved_key,
            base_url=base_url,
            timeout=timeout,
            locale=locale,
            client=http_client,
        )

        self.emails = AsyncEmails(self._transport)
        self.domains = AsyncDomains(self._transport)
        self.templates = AsyncTemplates(self._transport)
        self.audiences = AsyncAudiences(self._transport)
        self.broadcasts = AsyncBroadcasts(self._transport)
        self.suppressions = AsyncSuppressions(self._transport)
        self.webhooks = AsyncWebhooks(self._transport)
        self.stats = AsyncStats(self._transport)

    async def introspect(
        self, force_refresh: bool = False
    ) -> CoffeeMailResponse[ApiKeyIntrospection]:
        return await self._transport.introspect(force_refresh=force_refresh)

    def invalidate_introspection_cache(self) -> None:
        self._transport.invalidate_introspection_cache()
