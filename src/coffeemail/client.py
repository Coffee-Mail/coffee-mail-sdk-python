import os

import httpx

from coffeemail.core.http import DEFAULT_TIMEOUT_SECONDS, HttpTransport
from coffeemail.core.i18n import Locale
from coffeemail.core.types import ApiKeyIntrospection, CoffeeMailResponse
from coffeemail.resources.audiences import Audiences
from coffeemail.resources.broadcasts import Broadcasts
from coffeemail.resources.domains import Domains
from coffeemail.resources.emails import Emails
from coffeemail.resources.senders import Senders
from coffeemail.resources.stats import Stats
from coffeemail.resources.suppressions import Suppressions
from coffeemail.resources.templates import Templates
from coffeemail.resources.webhooks import Webhooks


class CoffeeMail:
    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        locale: Locale = "pt-BR",
        http_client: httpx.Client | None = None,
    ) -> None:
        resolved_key = api_key or os.getenv("COFFEEMAIL_API_KEY")
        self._transport = HttpTransport(
            api_key=resolved_key,
            base_url=base_url,
            timeout=timeout,
            locale=locale,
            client=http_client,
        )

        self.emails = Emails(self._transport)
        self.domains = Domains(self._transport)
        self.templates = Templates(self._transport)
        self.audiences = Audiences(self._transport)
        self.broadcasts = Broadcasts(self._transport)
        self.senders = Senders(self._transport)
        self.suppressions = Suppressions(self._transport)
        self.webhooks = Webhooks(self._transport)
        self.stats = Stats(self._transport)

    def introspect(self, force_refresh: bool = False) -> CoffeeMailResponse[ApiKeyIntrospection]:
        return self._transport.introspect(force_refresh=force_refresh)

    def invalidate_introspection_cache(self) -> None:
        self._transport.invalidate_introspection_cache()
