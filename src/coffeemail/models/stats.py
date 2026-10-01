from pydantic import BaseModel, ConfigDict, Field


class EmailStats(BaseModel):
    total_sent: int = Field(default=0, alias="totalSent")
    total_delivered: int = Field(default=0, alias="totalDelivered")
    total_bounced: int = Field(default=0, alias="totalBounced")
    total_complained: int = Field(default=0, alias="totalComplained")
    total_opened: int = Field(default=0, alias="totalOpened")
    total_clicked: int = Field(default=0, alias="totalClicked")
    delivery_rate: float = Field(default=0.0, alias="deliveryRate")
    bounce_rate: float = Field(default=0.0, alias="bounceRate")
    open_rate: float = Field(default=0.0, alias="openRate")
    click_rate: float = Field(default=0.0, alias="clickRate")

    model_config = ConfigDict(populate_by_name=True)
