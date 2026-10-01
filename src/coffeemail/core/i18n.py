from typing import Literal

Locale = Literal["pt-BR", "en"]

MESSAGES: dict[str, dict[Locale, str]] = {
    "missing_api_key": {
        "pt-BR": "Chave de API ausente. Forneça a chave no construtor ou defina a variável COFFEEMAIL_API_KEY.",
        "en": "Missing API key. Pass it to the constructor or define COFFEEMAIL_API_KEY environment variable.",
    },
    "timeout_error": {
        "pt-BR": "Tempo limite de conexão esgotado ao contatar o servidor da CoffeeMail.",
        "en": "Connection timed out while contacting CoffeeMail server.",
    },
    "network_error": {
        "pt-BR": "Falha na comunicação de rede com o servidor da CoffeeMail.",
        "en": "Network communication failure with CoffeeMail server.",
    },
    "invalid_webhook_signature": {
        "pt-BR": "Assinatura de webhook inválida ou corrompida.",
        "en": "Invalid or corrupted webhook signature.",
    },
    "webhook_timestamp_expired": {
        "pt-BR": "Timestamp do webhook expirou em relação à tolerância configurada.",
        "en": "Webhook timestamp expired according to configured tolerance.",
    },
}


def get_message(key: str, locale: Locale = "pt-BR") -> str:
    entry = MESSAGES.get(key)
    if not entry:
        return key
    return entry.get(locale, entry.get("pt-BR", key))
