from collections.abc import Mapping, Sequence

from coffeemail.core.errors import ValidationError
from coffeemail.core.http import AsyncHttpTransport, HttpTransport
from coffeemail.core.i18n import Locale, get_message
from coffeemail.core.types import CoffeeMailResponse
from coffeemail.models.suppressions import (
    BulkCreateSuppressionsResult,
    BulkSuppressionEntry,
    CreateSuppressionReason,
    ListSuppressionsResponse,
    SuppressionCategory,
    SuppressionDetail,
    SuppressionReason,
    SuppressionSource,
    SuppressionStatus,
)
from coffeemail.resources._common import (
    build_input,
    compact,
    input_failure,
    local_validation_error,
    parse_model,
)

SUPPRESSIONS_PATH = "/v1/product/suppressions"
_EMAIL_MARKER = "@"

EntryLike = BulkSuppressionEntry | Mapping[str, object]


def _email_instead_of_id(suppression_id: str, locale: Locale) -> ValidationError | None:
    if _EMAIL_MARKER not in suppression_id:
        return None
    return local_validation_error(get_message("suppression_id_expected", locale))


def _list_params(
    limit: int | None,
    after: str | None,
    status: SuppressionStatus | None,
    reason: SuppressionReason | None,
    source: SuppressionSource | None,
    category: SuppressionCategory | None,
) -> dict[str, object]:
    return compact(
        limit=limit, after=after, status=status, reason=reason, source=source, category=category
    )


def _create_body(
    email: str, reason: CreateSuppressionReason, expires_at: str | None
) -> dict[str, object]:
    return compact(email=email.strip(), reason=reason, expiresAt=expires_at)


def _bulk_body(entries: Sequence[EntryLike]) -> dict[str, object]:
    models = [
        e if isinstance(e, BulkSuppressionEntry) else BulkSuppressionEntry.model_validate(e)
        for e in entries
    ]
    return {"suppressions": [m.model_dump(exclude_none=True) for m in models]}


class Suppressions:
    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport

    def list(
        self,
        limit: int | None = None,
        after: str | None = None,
        *,
        status: SuppressionStatus | None = None,
        reason: SuppressionReason | None = None,
        source: SuppressionSource | None = None,
        category: SuppressionCategory | None = None,
    ) -> CoffeeMailResponse[ListSuppressionsResponse]:
        params = _list_params(limit, after, status, reason, source, category)
        res = self._transport.request("GET", SUPPRESSIONS_PATH, params=params)
        return parse_model(res, ListSuppressionsResponse, self._transport.locale)

    def get(self, suppression_id: str) -> CoffeeMailResponse[SuppressionDetail]:
        rejected = _email_instead_of_id(suppression_id, self._transport.locale)
        if rejected is not None:
            return input_failure(rejected)
        res = self._transport.request("GET", f"{SUPPRESSIONS_PATH}/{suppression_id}")
        return parse_model(res, SuppressionDetail, self._transport.locale)

    def create(
        self,
        email: str,
        reason: CreateSuppressionReason = "manual",
        expires_at: str | None = None,
    ) -> CoffeeMailResponse[SuppressionDetail]:
        body = _create_body(email, reason, expires_at)
        res = self._transport.request("POST", SUPPRESSIONS_PATH, json_data=body)
        return parse_model(res, SuppressionDetail, self._transport.locale)

    def delete(self, suppression_id: str) -> CoffeeMailResponse[dict[str, object]]:
        rejected = _email_instead_of_id(suppression_id, self._transport.locale)
        if rejected is not None:
            return input_failure(rejected)
        return self._transport.request("DELETE", f"{SUPPRESSIONS_PATH}/{suppression_id}")

    def reactivate(self, suppression_id: str) -> CoffeeMailResponse[dict[str, object]]:
        return self._transport.request("POST", f"{SUPPRESSIONS_PATH}/{suppression_id}/reactivate")

    def bulk_create(
        self, entries: Sequence[EntryLike]
    ) -> CoffeeMailResponse[BulkCreateSuppressionsResult]:
        body = build_input(lambda: _bulk_body(entries), self._transport.locale)
        if isinstance(body, ValidationError):
            return input_failure(body)
        res = self._transport.request("POST", f"{SUPPRESSIONS_PATH}/bulk", json_data=body)
        return parse_model(res, BulkCreateSuppressionsResult, self._transport.locale)


class AsyncSuppressions:
    def __init__(self, transport: AsyncHttpTransport) -> None:
        self._transport = transport

    async def list(
        self,
        limit: int | None = None,
        after: str | None = None,
        *,
        status: SuppressionStatus | None = None,
        reason: SuppressionReason | None = None,
        source: SuppressionSource | None = None,
        category: SuppressionCategory | None = None,
    ) -> CoffeeMailResponse[ListSuppressionsResponse]:
        params = _list_params(limit, after, status, reason, source, category)
        res = await self._transport.request("GET", SUPPRESSIONS_PATH, params=params)
        return parse_model(res, ListSuppressionsResponse, self._transport.locale)

    async def get(self, suppression_id: str) -> CoffeeMailResponse[SuppressionDetail]:
        rejected = _email_instead_of_id(suppression_id, self._transport.locale)
        if rejected is not None:
            return input_failure(rejected)
        res = await self._transport.request("GET", f"{SUPPRESSIONS_PATH}/{suppression_id}")
        return parse_model(res, SuppressionDetail, self._transport.locale)

    async def create(
        self,
        email: str,
        reason: CreateSuppressionReason = "manual",
        expires_at: str | None = None,
    ) -> CoffeeMailResponse[SuppressionDetail]:
        body = _create_body(email, reason, expires_at)
        res = await self._transport.request("POST", SUPPRESSIONS_PATH, json_data=body)
        return parse_model(res, SuppressionDetail, self._transport.locale)

    async def delete(self, suppression_id: str) -> CoffeeMailResponse[dict[str, object]]:
        rejected = _email_instead_of_id(suppression_id, self._transport.locale)
        if rejected is not None:
            return input_failure(rejected)
        return await self._transport.request("DELETE", f"{SUPPRESSIONS_PATH}/{suppression_id}")

    async def reactivate(self, suppression_id: str) -> CoffeeMailResponse[dict[str, object]]:
        return await self._transport.request(
            "POST", f"{SUPPRESSIONS_PATH}/{suppression_id}/reactivate"
        )

    async def bulk_create(
        self, entries: Sequence[EntryLike]
    ) -> CoffeeMailResponse[BulkCreateSuppressionsResult]:
        body = build_input(lambda: _bulk_body(entries), self._transport.locale)
        if isinstance(body, ValidationError):
            return input_failure(body)
        res = await self._transport.request("POST", f"{SUPPRESSIONS_PATH}/bulk", json_data=body)
        return parse_model(res, BulkCreateSuppressionsResult, self._transport.locale)
