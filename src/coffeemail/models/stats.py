from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

StatsGranularity = Literal["day", "week", "month"]
StatsPeriod = Literal["last7d", "last30d", "last90d"]
StatsEmailType = Literal["all", "transactional", "broadcast"]


class StatsBreakdownItem(BaseModel):
    sent: int = 0
    delivered: int = 0
    bounced: int = 0
    opened: int = 0
    clicked: int = 0


class StatsBreakdown(BaseModel):
    transactional: StatsBreakdownItem = Field(default_factory=StatsBreakdownItem)
    broadcast: StatsBreakdownItem = Field(default_factory=StatsBreakdownItem)


class StatsClient(BaseModel):
    name: str
    count: int = 0
    percentage: float = 0.0
    device_type: str | None = Field(default=None, alias="deviceType")

    model_config = ConfigDict(populate_by_name=True)


class StatsPoint(BaseModel):
    period: str
    sent: int = 0
    delivered: int = 0
    bounced: int = 0
    failed: int = 0
    opened: int = 0
    clicked: int = 0
    transactional: int = 0
    broadcast: int = 0


class EmailStats(BaseModel):
    total_sent: int = Field(default=0, alias="totalSent")
    total_delivered: int = Field(default=0, alias="totalDelivered")
    total_bounced: int = Field(default=0, alias="totalBounced")
    total_failed: int = Field(default=0, alias="totalFailed")
    total_opened: int = Field(default=0, alias="totalOpened")
    total_clicked: int = Field(default=0, alias="totalClicked")
    delivery_rate: float = Field(default=0.0, alias="deliveryRate")
    open_rate: float = Field(default=0.0, alias="openRate")
    click_rate: float = Field(default=0.0, alias="clickRate")
    breakdown: StatsBreakdown | None = None
    top_clients: list[StatsClient] = Field(default_factory=list, alias="topClients")
    data: list[StatsPoint] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)
