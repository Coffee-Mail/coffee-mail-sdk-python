from typing import ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field

TemplateFormat = Literal["html", "react"]
TemplateLocale = Literal["pt-BR", "en", "es"]


class TemplateVariable(BaseModel):
    name: str
    description: str | None = None
    type: Literal["string", "number", "color"] | None = None
    fallback_value: str | None = Field(default=None, alias="fallbackValue")

    model_config = ConfigDict(populate_by_name=True)


class TemplateDetail(BaseModel):
    id: str
    organisation_id: str | None = Field(default=None, alias="organisationId")
    name: str
    alias: str | None = None
    subject: str | None = None
    preheader: str | None = None
    html: str
    content_json: dict[str, object] | None = Field(default=None, alias="contentJson")
    text_payload: str | None = Field(default=None, alias="textPayload")
    variables: list[TemplateVariable] = Field(default_factory=list)
    is_active: bool = Field(default=True, alias="isActive")
    format: TemplateFormat | str = "html"
    source_locale: TemplateLocale | str | None = Field(default=None, alias="sourceLocale")
    created_at: str = Field(alias="createdAt")
    updated_at: str | None = Field(default=None, alias="updatedAt")

    model_config = ConfigDict(populate_by_name=True)


class ListTemplatesResponse(BaseModel):
    data: list[TemplateDetail] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)

    @property
    def templates(self) -> list[TemplateDetail]:
        return self.data


class PreviewTemplateResponse(BaseModel):
    html: str
    text: str | None = None


class FormatTemplateResponse(BaseModel):
    html: str


class SanitizeReport(BaseModel):
    scripts: int = 0
    iframes: int = 0
    javascript_hrefs: int = Field(default=0, alias="javascriptHrefs")
    event_handlers: int = Field(default=0, alias="eventHandlers")

    model_config = ConfigDict(populate_by_name=True)


class TestRenderTemplateResponse(BaseModel):
    __test__: ClassVar[bool] = False

    html: str
    text: str | None = None
    sanitize_report: SanitizeReport = Field(default_factory=SanitizeReport, alias="sanitizeReport")

    model_config = ConfigDict(populate_by_name=True)


class TemplateVersionSummary(BaseModel):
    version: int
    name: str
    subject: str | None = None
    created_by: str | None = Field(default=None, alias="createdBy")
    created_at: str = Field(alias="createdAt")

    model_config = ConfigDict(populate_by_name=True)


class ListTemplateVersionsResponse(BaseModel):
    data: list[TemplateVersionSummary] = Field(default_factory=list)
    total: int = 0

    model_config = ConfigDict(populate_by_name=True)

    @property
    def versions(self) -> list[TemplateVersionSummary]:
        return self.data


class TemplateVersionDetail(TemplateVersionSummary):
    template_id: str = Field(alias="templateId")
    preheader: str | None = None
    html: str
    content_json: dict[str, object] | None = Field(default=None, alias="contentJson")
    text_payload: str | None = Field(default=None, alias="textPayload")
    variables: list[TemplateVariable] = Field(default_factory=list)
    format: TemplateFormat | str = "html"
    source_locale: TemplateLocale | str | None = Field(default=None, alias="sourceLocale")
