from typing import ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field

WebhookEvent = Literal[
    "email.queued",
    "email.processing",
    "email.sent",
    "email.delivered",
    "email.delivery_delayed",
    "email.opened",
    "email.clicked",
    "email.bounced",
    "email.complained",
    "email.failed",
    "email.suppressed",
    "email.scheduled",
    "email.cancelled",
    "email.unsubscribed",
    "billing.plan_changed",
]
WebhookStatus = Literal["active", "paused", "disabled"]
WebhookDeliveryStatus = Literal["pending", "success", "failed", "exhausted"]


class WebhookDetail(BaseModel):
    id: str
    url: str
    events: list[str] = Field(default_factory=list)
    status: WebhookStatus | str
    description: str | None = None
    has_secret: bool | None = Field(default=None, alias="hasSecret")
    secret: str | None = None
    secret_preview: str | None = Field(default=None, alias="secretPreview")
    created_at: str = Field(alias="createdAt")

    model_config = ConfigDict(populate_by_name=True)

    @property
    def active(self) -> bool:
        return self.status == "active"


class CreatedWebhookDetail(WebhookDetail):
    secret: str


class ListWebhooksResponse(BaseModel):
    webhooks: list[WebhookDetail] = Field(default_factory=list)


class ToggleWebhookResult(BaseModel):
    id: str
    status: WebhookStatus | str


class RotateWebhookSecretResult(BaseModel):
    webhook_id: str = Field(alias="webhookId")
    secret: str

    model_config = ConfigDict(populate_by_name=True)


class TestWebhookResult(BaseModel):
    __test__: ClassVar[bool] = False

    status: Literal["success", "failed"] | str
    status_code: int | None = Field(default=None, alias="statusCode")
    body: str | None = None
    error: str | None = None

    model_config = ConfigDict(populate_by_name=True)

    @property
    def success(self) -> bool:
        return self.status == "success"


class WebhookDelivery(BaseModel):
    id: str
    webhook_id: str = Field(alias="webhookId")
    email_event_id: str | None = Field(default=None, alias="emailEventId")
    event_type: str = Field(alias="eventType")
    response_status: int | None = Field(default=None, alias="responseStatus")
    response_body: str | None = Field(default=None, alias="responseBody")
    attempts: int = 0
    last_error: str | None = Field(default=None, alias="lastError")
    status: WebhookDeliveryStatus | str
    next_run_at: str | None = Field(default=None, alias="nextRunAt")
    created_at: str = Field(alias="createdAt")

    model_config = ConfigDict(populate_by_name=True)


class ListWebhookDeliveriesResponse(BaseModel):
    deliveries: list[WebhookDelivery] = Field(default_factory=list)
