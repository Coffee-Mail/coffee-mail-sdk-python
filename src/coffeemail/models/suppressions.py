from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SuppressionReason = Literal[
    "manual", "bounce", "isp_block", "mailbox_not_found", "complaint", "unsubscribe"
]
CreateSuppressionReason = Literal["manual", "bounce", "complaint"]
SuppressionSource = Literal["manual", "auto"]
SuppressionStatus = Literal["active", "expired", "inactive"]
SuppressionCategory = Literal[
    "manual", "bounce", "block", "complaint", "unsubscribe", "invalid_email", "global"
]


class SuppressionDetail(BaseModel):
    id: str
    email: str
    reason: SuppressionReason | str
    source: SuppressionSource | str | None = None
    category: str | None = None
    status: SuppressionStatus | str | None = None
    expires_at: str | None = Field(default=None, alias="expiresAt")
    created_at: str = Field(alias="createdAt")

    model_config = ConfigDict(populate_by_name=True)


class ListSuppressionsResponse(BaseModel):
    suppressions: list[SuppressionDetail] = Field(default_factory=list)
    next_cursor: str | None = Field(default=None, alias="nextCursor")

    model_config = ConfigDict(populate_by_name=True)


class BulkSuppressionEntry(BaseModel):
    email: str
    reason: CreateSuppressionReason | None = None


class BulkCreateSuppressionsResult(BaseModel):
    inserted_count: int = Field(default=0, alias="insertedCount")

    model_config = ConfigDict(populate_by_name=True)
