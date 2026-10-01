from pydantic import BaseModel, ConfigDict, Field


class ContactDetail(BaseModel):
    id: str
    email: str
    name: str | None = None
    subscribed: bool = True
    attributes: dict[str, object] = Field(default_factory=dict)
    created_at: str = Field(alias="createdAt")
    updated_at: str | None = Field(default=None, alias="updatedAt")

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

    @property
    def contacts_count(self) -> int:
        return self.total_contacts


class ListAudiencesResponse(BaseModel):
    audiences: list[AudienceDetail] = Field(default_factory=list)
    next_cursor: str | None = Field(default=None, alias="nextCursor")

    model_config = ConfigDict(populate_by_name=True)


class ListContactsResponse(BaseModel):
    contacts: list[ContactDetail] = Field(default_factory=list)
    total: int = 0
    next_cursor: str | None = Field(default=None, alias="nextCursor")

    model_config = ConfigDict(populate_by_name=True)


class BulkAddContactsResponse(BaseModel):
    inserted: int
    updated: int
    failed: int
