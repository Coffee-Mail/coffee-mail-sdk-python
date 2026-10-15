from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ContactInput(BaseModel):
    """Contato para criação em lote; aceita ``first_name`` ou ``firstName``."""

    email: str
    first_name: str | None = Field(default=None, alias="firstName")
    last_name: str | None = Field(default=None, alias="lastName")
    metadata: dict[str, object] | None = None

    model_config = ConfigDict(populate_by_name=True)


class ContactDetail(BaseModel):
    id: str
    email: str
    first_name: str | None = Field(default=None, alias="firstName")
    last_name: str | None = Field(default=None, alias="lastName")
    metadata: dict[str, object] = Field(default_factory=dict)
    created_at: str = Field(alias="createdAt")

    model_config = ConfigDict(populate_by_name=True)


class AudienceDetail(BaseModel):
    id: str
    name: str
    description: str | None = None
    active: bool = True
    total_contacts: int = Field(default=0, alias="totalContacts")
    created_at: str = Field(alias="createdAt")
    updated_at: str | None = Field(default=None, alias="updatedAt")

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="before")
    @classmethod
    def _accept_contacts_count(cls, data: Any) -> Any:
        if isinstance(data, dict) and "totalContacts" not in data and "contactsCount" in data:
            return {**data, "totalContacts": data["contactsCount"]}
        return data

    @property
    def contacts_count(self) -> int:
        return self.total_contacts


class ListAudiencesResponse(BaseModel):
    audiences: list[AudienceDetail] = Field(default_factory=list)
    total: int = 0

    model_config = ConfigDict(populate_by_name=True)


class ListContactsResponse(BaseModel):
    contacts: list[ContactDetail] = Field(default_factory=list)
    total: int = 0

    model_config = ConfigDict(populate_by_name=True)


class BulkContactError(BaseModel):
    email: str
    reason: str


class BulkAddContactsResponse(BaseModel):
    inserted: int = 0
    skipped: int = 0
    errors: list[BulkContactError] = Field(default_factory=list)


class UpdateResult(BaseModel):
    id: str
