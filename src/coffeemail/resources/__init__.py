from coffeemail.resources.audiences import AsyncAudiences, AsyncContacts, Audiences, Contacts
from coffeemail.resources.broadcasts import AsyncBroadcasts, Broadcasts
from coffeemail.resources.domains import AsyncDomains, Domains
from coffeemail.resources.emails import AsyncEmails, Emails
from coffeemail.resources.stats import AsyncStats, Stats
from coffeemail.resources.suppressions import AsyncSuppressions, Suppressions
from coffeemail.resources.templates import AsyncTemplates, Templates
from coffeemail.resources.webhooks import AsyncWebhooks, Webhooks

__all__ = [
    "Emails",
    "AsyncEmails",
    "Domains",
    "AsyncDomains",
    "Templates",
    "AsyncTemplates",
    "Audiences",
    "AsyncAudiences",
    "Contacts",
    "AsyncContacts",
    "Broadcasts",
    "AsyncBroadcasts",
    "Suppressions",
    "AsyncSuppressions",
    "Webhooks",
    "AsyncWebhooks",
    "Stats",
    "AsyncStats",
]
