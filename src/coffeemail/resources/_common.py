from coffeemail.core.parsing import (
    InputError,
    build_input,
    input_failure,
    local_validation_error,
    parse_adapter,
    parse_model,
)

__all__ = [
    "InputError",
    "build_input",
    "compact",
    "input_failure",
    "local_validation_error",
    "parse_adapter",
    "parse_model",
]


def compact(**fields: object) -> dict[str, object]:
    return {key: value for key, value in fields.items() if value is not None}
