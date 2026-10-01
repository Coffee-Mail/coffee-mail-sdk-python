from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SuppressionReason = Literal["bounce", "complaint", "unsubscribe", "manual"]


class SuppressionDetail(BaseModel):
    id: str
    email: str
    reason: SuppressionReason
    created_at: str = Field(alias="createdAt")

    model_config = ConfigDict(populate_by_name=True)


class ListSuppressionsResponse(BaseModel):
    suppressions: list[SuppressionDetail] = Field(default_factory=list)
    next_cursor: str | None = Field(default=None, alias="nextCursor")

    model_config = ConfigDict(populate_by_name=True)


class CheckSuppressionResponse(BaseModel):
    suppressed: bool
    reason: SuppressionReason | None = None
    created_at: str | None = Field(default=None, alias="createdAt")

    model_config = ConfigDict(populate_by_name=True)
