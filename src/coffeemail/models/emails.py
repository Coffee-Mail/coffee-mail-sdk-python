from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

EmailStatus = Literal[
    "queued",
    "processing",
    "sent",
    "delivered",
    "bounced",
    "complained",
    "failed",
    "skipped",
    "scheduled",
    "cancelled",
]
EmailType = Literal["transactional", "broadcast"]


class EmailParticipant(BaseModel):
    email: str
    name: str | None = None


class EmailAttachment(BaseModel):
    filename: str
    content: str | bytes
    content_type: str | None = Field(default=None, alias="contentType")
    disposition: Literal["attachment", "inline"] | None = "attachment"
    cid: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class EmailTag(BaseModel):
    name: str
    value: str


class SendEmailPayload(BaseModel):
    """Dados de um envio.

    ``idempotency_key`` e ``sandbox`` viram os headers ``X-Idempotency-Key`` e
    ``X-Coffeemail-Sandbox`` e não vão no corpo. Sem chave de idempotência, a API trata
    envios com payload idêntico como o mesmo envio.
    """

    from_address: str | EmailParticipant = Field(alias="from")
    to: str | EmailParticipant | list[str | EmailParticipant]
    subject: str | None = None
    html: str | None = None
    text: str | None = None
    cc: str | EmailParticipant | list[str | EmailParticipant] | None = None
    bcc: str | EmailParticipant | list[str | EmailParticipant] | None = None
    reply_to: str | EmailParticipant | None = Field(default=None, alias="replyTo")
    headers: dict[str, str] | None = None
    attachments: list[EmailAttachment] | None = None
    tags: list[EmailTag] | None = None
    template_id: str | None = Field(default=None, alias="templateId")
    variables: dict[str, object] | None = None
    email_type: EmailType | None = Field(default=None, alias="emailType")
    suppression_category: str | None = Field(default=None, alias="suppressionCategory")
    scheduled_at: str | None = Field(default=None, alias="scheduledAt")
    metadata: dict[str, object] | None = None
    idempotency_key: str | None = Field(default=None, alias="idempotencyKey", exclude=True)
    sandbox: bool = Field(default=False, exclude=True)

    model_config = ConfigDict(populate_by_name=True)


class SendEmailResponse(BaseModel):
    id: str
    status: EmailStatus | str
    queued_at: str | None = Field(default=None, alias="queuedAt")

    model_config = ConfigDict(populate_by_name=True)


class BatchSendEmailItemSuccess(BaseModel):
    ok: Literal[True]
    data: SendEmailResponse

    model_config = ConfigDict(populate_by_name=True)


class BatchSendEmailItemFailure(BaseModel):
    ok: Literal[False]
    error: str

    model_config = ConfigDict(populate_by_name=True)


BatchSendEmailResult = Annotated[
    BatchSendEmailItemSuccess | BatchSendEmailItemFailure,
    Field(discriminator="ok"),
]


class ApiKeyRef(BaseModel):
    id: str
    name: str


class EmailDetail(BaseModel):
    id: str
    from_address: str = Field(alias="from")
    to: list[str] = Field(default_factory=list)
    cc: list[str] | None = None
    bcc: list[str] | None = None
    subject: str | None = None
    status: EmailStatus | str
    attempts: int = 0
    last_error: str | None = Field(default=None, alias="lastError")
    message_id: str | None = Field(default=None, alias="messageId")
    api_key: ApiKeyRef | None = Field(default=None, alias="apiKey")
    created_at: str = Field(alias="createdAt")
    scheduled_at: str | None = Field(default=None, alias="scheduledAt")
    sent_at: str | None = Field(default=None, alias="sentAt")
    delivered_at: str | None = Field(default=None, alias="deliveredAt")
    bounced_at: str | None = Field(default=None, alias="bouncedAt")
    failed_at: str | None = Field(default=None, alias="failedAt")
    complained_at: str | None = Field(default=None, alias="complainedAt")
    suppressed_at: str | None = Field(default=None, alias="suppressedAt")
    opened_at: str | None = Field(default=None, alias="openedAt")
    first_clicked_at: str | None = Field(default=None, alias="firstClickedAt")
    open_count: int = Field(default=0, alias="openCount")
    click_count: int = Field(default=0, alias="clickCount")
    proxy_open_count: int = Field(default=0, alias="proxyOpenCount")
    tags: list[EmailTag] | None = None
    html: str | None = None
    text: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class ListEmailsResponse(BaseModel):
    emails: list[EmailDetail] = Field(default_factory=list)
    next_cursor: str | None = Field(default=None, alias="nextCursor")

    model_config = ConfigDict(populate_by_name=True)


class EmailEvent(BaseModel):
    type: str
    timestamp: str
    metadata: dict[str, object] | None = None


class EmailEventsResponse(BaseModel):
    id: str
    events: list[EmailEvent] = Field(default_factory=list)


class EmailTagValues(BaseModel):
    name: str
    values: list[str] = Field(default_factory=list)


class ListEmailTagsResponse(BaseModel):
    tags: list[EmailTagValues] = Field(default_factory=list)
