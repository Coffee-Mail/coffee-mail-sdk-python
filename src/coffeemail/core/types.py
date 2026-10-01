from collections.abc import Iterator
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from coffeemail.core.errors import CoffeeMailError

T = TypeVar("T")


class CoffeeMailResponse(Generic[T]):
    def __init__(
        self,
        data: T | None = None,
        error: CoffeeMailError | None = None,
        status_code: int | None = None,
    ) -> None:
        self.data = data
        self.error = error
        self.status_code = status_code

    @property
    def is_success(self) -> bool:
        return self.error is None

    def unwrap(self) -> T:
        if self.error is not None:
            raise self.error
        if self.data is None:
            raise ValueError("Resposta sem dados disponíveis.")
        return self.data

    def __iter__(self) -> Iterator[object | None]:
        yield self.data
        yield self.error

    def __repr__(self) -> str:
        return f"CoffeeMailResponse(data={self.data!r}, error={self.error!r}, status_code={self.status_code})"


class ApiKeyIntrospection(BaseModel):
    id: str
    name: str
    environment: str
    scopes: list[str] = Field(default_factory=list)
    rate_limit: dict[str, object] = Field(default_factory=dict, alias="rateLimit")
    created_at: str = Field(alias="createdAt")
    expires_at: str | None = Field(default=None, alias="expiresAt")

    model_config = ConfigDict(populate_by_name=True)
