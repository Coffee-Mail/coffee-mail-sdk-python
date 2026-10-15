from typing import Literal

Locale = Literal["pt-BR", "en"]

DEFAULT_LOCALE: Locale = "pt-BR"

MESSAGES: dict[str, dict[Locale, str]] = {
    "missing_api_key": {
        "pt-BR": (
            "A chave de API não foi informada. Forneça uma chave válida (ex: cm_live_...) "
            "no construtor CoffeeMail ou na variável de ambiente COFFEEMAIL_API_KEY."
        ),
        "en": (
            "API key was not provided. Pass a valid API key (e.g. cm_live_...) to the "
            "CoffeeMail constructor or set the COFFEEMAIL_API_KEY environment variable."
        ),
    },
    "request_timeout": {
        "pt-BR": "A requisição excedeu o tempo limite configurado de {timeoutMs}ms.",
        "en": "The request timed out after {timeoutMs}ms.",
    },
    "network_error": {
        "pt-BR": "Falha de rede ao tentar se comunicar com os servidores do CoffeeMail: {details}",
        "en": "Network error while attempting to communicate with CoffeeMail API: {details}",
    },
    "unexpected_error": {
        "pt-BR": "Ocorreu um erro inesperado durante a comunicação com a API do CoffeeMail.",
        "en": "An unexpected error occurred while communicating with CoffeeMail API.",
    },
    "invalid_json": {
        "pt-BR": "A resposta do servidor não pôde ser interpretada como JSON válido.",
        "en": "The server response could not be parsed as valid JSON.",
    },
    "rate_limit_exceeded": {
        "pt-BR": "Limite de requisições excedido (Rate Limit). Tente novamente em alguns segundos.",
        "en": "Rate limit exceeded. Please retry in a few moments.",
    },
    "permission_denied": {
        "pt-BR": (
            "Esta chave de API não possui a permissão necessária ({requiredPermission}) para "
            "executar esta operação. Crie uma chave com permissão 'full_access' no dashboard."
        ),
        "en": (
            "This API key lacks the required permission ({requiredPermission}) for this "
            "operation. Create a key with 'full_access' permission in the dashboard."
        ),
    },
    "invalid_input": {
        "pt-BR": "Dados de entrada inválidos: {details}",
        "en": "Invalid input: {details}",
    },
    "invalid_recipient": {
        "pt-BR": (
            "Destinatário inválido. Forneça uma string com e-mail ou um objeto com o campo 'email'."
        ),
        "en": "Invalid recipient. Pass an e-mail string or an object with an 'email' field.",
    },
    "suppression_id_expected": {
        "pt-BR": (
            "A rota de supressões usa o id da supressão, não o e-mail. "
            "Use suppressions.list() para encontrar o id."
        ),
        "en": (
            "The suppressions route takes the suppression id, not the e-mail address. "
            "Use suppressions.list() to find the id."
        ),
    },
}


def get_message(
    key: str, locale: Locale = DEFAULT_LOCALE, params: dict[str, str] | None = None
) -> str:
    entry = MESSAGES.get(key)
    if not entry:
        return key
    template = entry.get(locale, entry[DEFAULT_LOCALE])
    for name, value in (params or {}).items():
        template = template.replace("{" + name + "}", value)
    return template
