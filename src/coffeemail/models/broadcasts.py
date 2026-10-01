from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

BroadcastStatus = Literal["draft", "scheduled", "sending", "completed", "cancelled"]


class BroadcastDetail(BaseModel):
    id: str
    name: str
    subject: str
    status: BroadcastStatus
    audience_id: str = Field(alias="audienceId")
    template_id: str | None = Field(default=None, alias="templateId")
    scheduled_at: str | None = Field(default=None, alias="scheduledAt")
    sent_at: str | None = Field(default=None, alias="sentAt")
    total_recipients: int = Field(default=0, alias="totalRecipients")
    created_at: str = Field(alias="createdAt")

    model_config = ConfigDict(populate_by_name=True)


class ListBroadcastsResponse(BaseModel):
    broadcasts: list[BroadcastDetail] = Field(default_factory=list)
    next_cursor: str | None = Field(default=None, alias="nextCursor")

    model_config = ConfigDict(populate_by_name=True)
