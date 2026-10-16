from collections.abc import Sequence

from coffeemail.core.http import AsyncHttpTransport, HttpTransport
from coffeemail.core.types import CoffeeMailResponse
from coffeemail.models.validation import ValidateEmailsResponse
from coffeemail.resources._common import parse_model

VALIDATE_PATH = "/v1/product/validate"


def _validate_body(emails: Sequence[str]) -> dict[str, object]:
    return {"emails": [email.strip() for email in emails]}


class Validation:
    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport

    def validate(self, emails: Sequence[str]) -> CoffeeMailResponse[ValidateEmailsResponse]:
        """Valida de 1 a 100 endereços (formato, MX e domínio descartável).

        Cada endereço consome um crédito de validação do mês. Créditos esgotados
        respondem ``RateLimitError`` com ``api_code="VALIDATION_CREDITS_EXHAUSTED"``:
        repetir a chamada não resolve até a virada do mês ou a troca de plano.
        """
        res = self._transport.request("POST", VALIDATE_PATH, json_data=_validate_body(emails))
        return parse_model(res, ValidateEmailsResponse, self._transport.locale)


class AsyncValidation:
    def __init__(self, transport: AsyncHttpTransport) -> None:
        self._transport = transport

    async def validate(self, emails: Sequence[str]) -> CoffeeMailResponse[ValidateEmailsResponse]:
        """Valida de 1 a 100 endereços. Veja :meth:`Validation.validate`."""
        res = await self._transport.request("POST", VALIDATE_PATH, json_data=_validate_body(emails))
        return parse_model(res, ValidateEmailsResponse, self._transport.locale)
