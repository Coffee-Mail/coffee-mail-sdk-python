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
    """Remetente recém-criado. O token de verificação segue por e-mail ao
    endereço cadastrado; ``verification_token`` é mantido por compatibilidade
    e está depreciado (a API não o devolve mais)."""

    verification_token: str | None = Field(default=None, alias="verificationToken")


class ListSendersResponse(BaseModel):
    senders: list[SenderDetail] = Field(default_factory=list)


class VerifySenderResult(BaseModel):
    id: str
    email: str
