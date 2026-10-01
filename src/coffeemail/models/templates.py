from pydantic import BaseModel, ConfigDict, Field


class TemplateDetail(BaseModel):
    id: str
    name: str
    description: str | None = None
    subject: str | None = None
    html: str
    text: str | None = None
    variables: list[str] = Field(default_factory=list)
    created_at: str = Field(alias="createdAt")
    updated_at: str | None = Field(default=None, alias="updatedAt")

    model_config = ConfigDict(populate_by_name=True)


class ListTemplatesResponse(BaseModel):
    templates: list[TemplateDetail] = Field(default_factory=list)
    next_cursor: str | None = Field(default=None, alias="nextCursor")

    model_config = ConfigDict(populate_by_name=True)

    @property
    def data(self) -> list[TemplateDetail]:
        return self.templates


class PreviewTemplateResponse(BaseModel):
    html: str
    text: str | None = None
