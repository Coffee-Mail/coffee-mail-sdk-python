from typing import ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field

BroadcastStatus = Literal["draft", "scheduled", "sending", "sent", "failed", "cancelled"]


class BroadcastMetrics(BaseModel):
    delivered: int = 0
    opened: int = 0
    clicked: int = 0
    bounced: int = 0
    failed: int = 0
    suppressed: int = 0


class BroadcastDetail(BaseModel):
    id: str
    audience_id: str = Field(alias="audienceId")
    audience_name: str | None = Field(default=None, alias="audienceName")
    template_id: str | None = Field(default=None, alias="templateId")
    subject: str = ""
    from_email: str = Field(default="", alias="fromEmail")
    reply_to: str | None = Field(default=None, alias="replyTo")
    status: BroadcastStatus | str
    scheduled_at: str | None = Field(default=None, alias="scheduledAt")
    sent_at: str | None = Field(default=None, alias="sentAt")
    cancelled_at: str | None = Field(default=None, alias="cancelledAt")
    recipients_total: int = Field(default=0, alias="recipientsTotal")
    recipients_queued: int = Field(default=0, alias="recipientsQueued")
    recipients_failed: int = Field(default=0, alias="recipientsFailed")
    metrics: BroadcastMetrics | None = None
    created_at: str = Field(alias="createdAt")
    updated_at: str | None = Field(default=None, alias="updatedAt")

    model_config = ConfigDict(populate_by_name=True)


class ListBroadcastsResponse(BaseModel):
    broadcasts: list[BroadcastDetail] = Field(default_factory=list)
    next_cursor: str | None = Field(default=None, alias="nextCursor")

    model_config = ConfigDict(populate_by_name=True)


class SendBroadcastResult(BaseModel):
    id: str
    status: BroadcastStatus | str
    recipients_total: int = Field(default=0, alias="recipientsTotal")
    recipients_queued: int = Field(default=0, alias="recipientsQueued")

    model_config = ConfigDict(populate_by_name=True)


class CancelBroadcastResult(BaseModel):
    id: str
    status: BroadcastStatus | str
    cancelled_at: str | None = Field(default=None, alias="cancelledAt")

    model_config = ConfigDict(populate_by_name=True)


class TestSendResult(BaseModel):
    __test__: ClassVar[bool] = False

    success: bool
    message_id: str = Field(default="", alias="messageId")
    recipient: str = ""

    model_config = ConfigDict(populate_by_name=True)
