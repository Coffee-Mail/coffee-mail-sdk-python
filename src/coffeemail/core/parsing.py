from collections.abc import Callable
from typing import Any, TypeVar

import pydantic
from pydantic import BaseModel

from coffeemail.core.errors import CODE_INVALID_RESPONSE, CoffeeMailError, ValidationError
from coffeemail.core.i18n import DEFAULT_LOCALE, Locale, get_message
from coffeemail.core.types import CoffeeMailResponse

M = TypeVar("M", bound=BaseModel)
B = TypeVar("B")

LOCAL_STATUS_CODE = 0
_SUMMARY_LIMIT = 3


class InputError(Exception):
    def __init__(self, key: str) -> None:
        super().__init__(key)
        self.key = key


def local_validation_error(
    message: str, details: dict[str, object] | None = None
) -> ValidationError:
    return ValidationError(message, status_code=LOCAL_STATUS_CODE, details=details)


def _summary(exc: pydantic.ValidationError) -> str:
    return "; ".join(
        f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
        for error in exc.errors()[:_SUMMARY_LIMIT]
    )


def build_input(build: Callable[[], B], locale: Locale) -> B | ValidationError:
    try:
        return build()
    except pydantic.ValidationError as exc:
        return local_validation_error(
            get_message("invalid_input", locale, {"details": _summary(exc)}),
            {"errors": exc.errors(include_url=False)},
        )
    except InputError as exc:
        return local_validation_error(get_message(exc.key, locale))


def input_failure(error: ValidationError) -> CoffeeMailResponse[Any]:
    return CoffeeMailResponse(data=None, error=error, status_code=LOCAL_STATUS_CODE)


def parse_model(
    res: CoffeeMailResponse[dict[str, object]],
    model: type[M],
    locale: Locale = DEFAULT_LOCALE,
) -> CoffeeMailResponse[M]:
    if res.error or res.data is None:
        return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
    try:
        parsed = model.model_validate(res.data)
    except pydantic.ValidationError as exc:
        error = invalid_response(res.status_code, exc, locale)
        return CoffeeMailResponse(data=None, error=error, status_code=res.status_code)
    return CoffeeMailResponse(data=parsed, error=None, status_code=res.status_code)


def invalid_response(
    status_code: int | None, exc: pydantic.ValidationError, locale: Locale
) -> CoffeeMailError:
    return CoffeeMailError(
        get_message("invalid_json", locale),
        status_code=status_code,
        code=CODE_INVALID_RESPONSE,
        details={"errors": exc.errors(include_url=False)},
    )


def parse_adapter(
    res: CoffeeMailResponse[Any], adapter: pydantic.TypeAdapter[Any], locale: Locale
) -> CoffeeMailResponse[Any]:
    if res.error or res.data is None:
        return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
    try:
        parsed = adapter.validate_python(res.data)
    except pydantic.ValidationError as exc:
        error = invalid_response(res.status_code, exc, locale)
        return CoffeeMailResponse(data=None, error=error, status_code=res.status_code)
    return CoffeeMailResponse(data=parsed, error=None, status_code=res.status_code)
