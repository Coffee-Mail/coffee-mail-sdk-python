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
    from_address: str | EmailParticipant = Field(alias="from")
    to: str | EmailParticipant
    subject: str
    html: str | None = None
    text: str | None = None
    cc: str | EmailParticipant | list[str | EmailParticipant] | None = None
    bcc: str | EmailParticipant | list[str | EmailParticipant] | None = None
    reply_to: str | EmailParticipant | list[str | EmailParticipant] | None = Field(
        default=None, alias="replyTo"
    )
    headers: dict[str, str] | None = None
    attachments: list[EmailAttachment] | None = None
    tags: list[EmailTag] | None = None
    template_id: str | None = Field(default=None, alias="templateId")
    variables: dict[str, object] | None = None
    scheduled_at: str | None = Field(default=None, alias="scheduledAt")
    track_opens: bool | None = Field(default=None, alias="trackOpens")
    track_clicks: bool | None = Field(default=None, alias="trackClicks")

    model_config = ConfigDict(populate_by_name=True)


class SendEmailResponse(BaseModel):
    id: str
    status: EmailStatus
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


class EmailDetail(BaseModel):
    id: str
    from_address: str = Field(alias="from")
    to: str
    subject: str
    status: EmailStatus
    created_at: str = Field(alias="createdAt")
    sent_at: str | None = Field(default=None, alias="sentAt")
    delivered_at: str | None = Field(default=None, alias="deliveredAt")
    opened_at: str | None = Field(default=None, alias="openedAt")
    clicked_at: str | None = Field(default=None, alias="clickedAt")

    model_config = ConfigDict(populate_by_name=True)


class ListEmailsResponse(BaseModel):
    emails: list[EmailDetail] = Field(default_factory=list)
    next_cursor: str | None = Field(default=None, alias="nextCursor")

    model_config = ConfigDict(populate_by_name=True)
