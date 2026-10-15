from pydantic import BaseModel, ConfigDict, Field


class SenderDetail(BaseModel):
    id: str
    email: str
    display_name: str | None = Field(default=None, alias="displayName")
    verified_at: str | None = Field(default=None, alias="verifiedAt")
    active: bool = True
    created_at: str = Field(alias="createdAt")

    model_config = ConfigDict(populate_by_name=True)


class CreatedSender(SenderDetail):
    verification_token: str = Field(alias="verificationToken")


class ListSendersResponse(BaseModel):
    senders: list[SenderDetail] = Field(default_factory=list)


class VerifySenderResult(BaseModel):
    id: str
    email: str
