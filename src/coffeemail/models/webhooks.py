from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

WebhookEvent = Literal[
    "email.queued",
    "email.sent",
    "email.delivered",
    "email.bounced",
    "email.complained",
    "email.clicked",
    "email.opened",
    "email.failed",
]


class WebhookDetail(BaseModel):
    id: str
    url: str
    events: list[str]
    active: bool
    created_at: str = Field(alias="createdAt")
    updated_at: str | None = Field(default=None, alias="updatedAt")

    model_config = ConfigDict(populate_by_name=True)


class CreatedWebhookDetail(WebhookDetail):
    secret: str


class ListWebhooksResponse(BaseModel):
    webhooks: list[WebhookDetail] = Field(default_factory=list)


class RotateWebhookSecretResult(BaseModel):
    id: str
    secret: str


class TestWebhookResult(BaseModel):
    success: bool
    status_code: int | None = Field(default=None, alias="statusCode")
    response_body: str | None = Field(default=None, alias="responseBody")
    duration_ms: int | None = Field(default=None, alias="durationMs")

    model_config = ConfigDict(populate_by_name=True)
