from collections.abc import Mapping, Sequence

from coffeemail.core.errors import ValidationError
from coffeemail.core.http import AsyncHttpTransport, HttpTransport
from coffeemail.core.types import CoffeeMailResponse
from coffeemail.models.broadcasts import TestSendResult
from coffeemail.models.templates import (
    FormatTemplateResponse,
    ListTemplatesResponse,
    ListTemplateVersionsResponse,
    PreviewTemplateResponse,
    TemplateDetail,
    TemplateFormat,
    TemplateLocale,
    TemplateVariable,
    TemplateVersionDetail,
    TestRenderTemplateResponse,
)
from coffeemail.resources._common import build_input, compact, input_failure, parse_model

TEMPLATES_PATH = "/v1/product/templates"

VariableLike = TemplateVariable | Mapping[str, object]


def _variables(variables: Sequence[VariableLike] | None) -> list[dict[str, object]] | None:
    if variables is None:
        return None
    models = [
        v if isinstance(v, TemplateVariable) else TemplateVariable.model_validate(v)
        for v in variables
    ]
    return [m.model_dump(by_alias=True, exclude_none=True) for m in models]


def _versions_path(template_id: str) -> str:
    return f"{TEMPLATES_PATH}/{template_id}/versions"


def _version_path(template_id: str, version: int) -> str:
    return f"{_versions_path(template_id)}/{version}"


def _mapping(value: Mapping[str, object] | None) -> dict[str, object] | None:
    return dict(value) if value is not None else None


def _template_body(
    *,
    name: str | None,
    html: str | None,
    alias: str | None,
    subject: str | None,
    preheader: str | None,
    content_json: Mapping[str, object] | None,
    text_payload: str | None,
    variables: Sequence[VariableLike] | None,
    format: TemplateFormat | None,
    source_locale: TemplateLocale | None,
    is_active: bool | None = None,
) -> dict[str, object]:
    return compact(
        name=name,
        html=html,
        alias=alias,
        subject=subject,
        preheader=preheader,
        contentJson=_mapping(content_json),
        textPayload=text_payload,
        variables=_variables(variables),
        format=format,
        sourceLocale=source_locale,
        isActive=is_active,
    )


def _render_body(
    html: str, format: TemplateFormat | None, variables: Mapping[str, object] | None
) -> dict[str, object]:
    return compact(html=html, format=format, variables=_mapping(variables))


def _test_send_body(
    to: str, from_email: str | None, subject: str | None, variables: Mapping[str, object] | None
) -> dict[str, object]:
    return compact(
        to=to.strip(), subject=subject, variables=_mapping(variables), **{"from": from_email}
    )


class Templates:
    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport

    def list(self) -> CoffeeMailResponse[ListTemplatesResponse]:
        return parse_model(
            self._transport.request("GET", TEMPLATES_PATH),
            ListTemplatesResponse,
            self._transport.locale,
        )

    def get(self, template_id: str) -> CoffeeMailResponse[TemplateDetail]:
        res = self._transport.request("GET", f"{TEMPLATES_PATH}/{template_id}")
        return parse_model(res, TemplateDetail, self._transport.locale)

    def create(
        self,
        name: str,
        html: str,
        *,
        alias: str | None = None,
        subject: str | None = None,
        preheader: str | None = None,
        content_json: Mapping[str, object] | None = None,
        text_payload: str | None = None,
        variables: Sequence[VariableLike] | None = None,
        format: TemplateFormat | None = None,
        source_locale: TemplateLocale | None = None,
    ) -> CoffeeMailResponse[TemplateDetail]:
        body = build_input(
            lambda: _template_body(
                name=name,
                html=html,
                alias=alias,
                subject=subject,
                preheader=preheader,
                content_json=content_json,
                text_payload=text_payload,
                variables=variables,
                format=format,
                source_locale=source_locale,
            ),
            self._transport.locale,
        )
        if isinstance(body, ValidationError):
            return input_failure(body)
        res = self._transport.request("POST", TEMPLATES_PATH, json_data=body)
        return parse_model(res, TemplateDetail, self._transport.locale)

    def update(
        self,
        template_id: str,
        *,
        name: str | None = None,
        html: str | None = None,
        alias: str | None = None,
        subject: str | None = None,
        preheader: str | None = None,
        content_json: Mapping[str, object] | None = None,
        text_payload: str | None = None,
        variables: Sequence[VariableLike] | None = None,
        format: TemplateFormat | None = None,
        source_locale: TemplateLocale | None = None,
        is_active: bool | None = None,
    ) -> CoffeeMailResponse[TemplateDetail]:
        body = build_input(
            lambda: _template_body(
                name=name,
                html=html,
                alias=alias,
                subject=subject,
                preheader=preheader,
                content_json=content_json,
                text_payload=text_payload,
                variables=variables,
                format=format,
                source_locale=source_locale,
                is_active=is_active,
            ),
            self._transport.locale,
        )
        if isinstance(body, ValidationError):
            return input_failure(body)
        res = self._transport.request("PATCH", f"{TEMPLATES_PATH}/{template_id}", json_data=body)
        return parse_model(res, TemplateDetail, self._transport.locale)

    def delete(self, template_id: str) -> CoffeeMailResponse[dict[str, object]]:
        return self._transport.request("DELETE", f"{TEMPLATES_PATH}/{template_id}")

    def preview(
        self,
        html: str,
        *,
        format: TemplateFormat | None = None,
        variables: Mapping[str, object] | None = None,
    ) -> CoffeeMailResponse[PreviewTemplateResponse]:
        res = self._transport.request(
            "POST", f"{TEMPLATES_PATH}/preview", json_data=_render_body(html, format, variables)
        )
        return parse_model(res, PreviewTemplateResponse, self._transport.locale)

    def preview_by_id(
        self, template_id: str, variables: Mapping[str, object] | None = None
    ) -> CoffeeMailResponse[PreviewTemplateResponse]:
        """Busca o template salvo e o renderiza (duas requisições: get + preview)."""
        template = self.get(template_id)
        if template.error or template.data is None:
            return CoffeeMailResponse(
                data=None, error=template.error, status_code=template.status_code
            )
        stored = template.data
        return self.preview(stored.html, format=_known_format(stored.format), variables=variables)

    def format(
        self, html: str, *, format: TemplateFormat | None = None
    ) -> CoffeeMailResponse[FormatTemplateResponse]:
        res = self._transport.request(
            "POST", f"{TEMPLATES_PATH}/format", json_data=compact(html=html, format=format)
        )
        return parse_model(res, FormatTemplateResponse, self._transport.locale)

    def test_render(
        self,
        html: str,
        *,
        format: TemplateFormat | None = None,
        variables: Mapping[str, object] | None = None,
    ) -> CoffeeMailResponse[TestRenderTemplateResponse]:
        res = self._transport.request(
            "POST",
            f"{TEMPLATES_PATH}/test-render",
            json_data=_render_body(html, format, variables),
        )
        return parse_model(res, TestRenderTemplateResponse, self._transport.locale)

    def test_send(
        self,
        template_id: str,
        to: str,
        *,
        from_email: str | None = None,
        subject: str | None = None,
        variables: Mapping[str, object] | None = None,
    ) -> CoffeeMailResponse[TestSendResult]:
        res = self._transport.request(
            "POST",
            f"{TEMPLATES_PATH}/{template_id}/test-send",
            json_data=_test_send_body(to, from_email, subject, variables),
        )
        return parse_model(res, TestSendResult, self._transport.locale)

    def list_versions(
        self, template_id: str, *, limit: int | None = None, offset: int | None = None
    ) -> CoffeeMailResponse[ListTemplateVersionsResponse]:
        """Lista as versões do template, da mais recente para a mais antiga."""
        res = self._transport.request(
            "GET", _versions_path(template_id), params=compact(limit=limit, offset=offset)
        )
        return parse_model(res, ListTemplateVersionsResponse, self._transport.locale)

    def get_version(
        self, template_id: str, version: int
    ) -> CoffeeMailResponse[TemplateVersionDetail]:
        res = self._transport.request("GET", _version_path(template_id, version))
        return parse_model(res, TemplateVersionDetail, self._transport.locale)

    def restore_version(self, template_id: str, version: int) -> CoffeeMailResponse[TemplateDetail]:
        """Restaura o conteúdo de uma versão; a restauração gera uma versão nova."""
        res = self._transport.request("POST", f"{_version_path(template_id, version)}/restore")
        return parse_model(res, TemplateDetail, self._transport.locale)


class AsyncTemplates:
    def __init__(self, transport: AsyncHttpTransport) -> None:
        self._transport = transport

    async def list(self) -> CoffeeMailResponse[ListTemplatesResponse]:
        res = await self._transport.request("GET", TEMPLATES_PATH)
        return parse_model(res, ListTemplatesResponse, self._transport.locale)

    async def get(self, template_id: str) -> CoffeeMailResponse[TemplateDetail]:
        res = await self._transport.request("GET", f"{TEMPLATES_PATH}/{template_id}")
        return parse_model(res, TemplateDetail, self._transport.locale)

    async def create(
        self,
        name: str,
        html: str,
        *,
        alias: str | None = None,
        subject: str | None = None,
        preheader: str | None = None,
        content_json: Mapping[str, object] | None = None,
        text_payload: str | None = None,
        variables: Sequence[VariableLike] | None = None,
        format: TemplateFormat | None = None,
        source_locale: TemplateLocale | None = None,
    ) -> CoffeeMailResponse[TemplateDetail]:
        body = build_input(
            lambda: _template_body(
                name=name,
                html=html,
                alias=alias,
                subject=subject,
                preheader=preheader,
                content_json=content_json,
                text_payload=text_payload,
                variables=variables,
                format=format,
                source_locale=source_locale,
            ),
            self._transport.locale,
        )
        if isinstance(body, ValidationError):
            return input_failure(body)
        res = await self._transport.request("POST", TEMPLATES_PATH, json_data=body)
        return parse_model(res, TemplateDetail, self._transport.locale)

    async def update(
        self,
        template_id: str,
        *,
        name: str | None = None,
        html: str | None = None,
        alias: str | None = None,
        subject: str | None = None,
        preheader: str | None = None,
        content_json: Mapping[str, object] | None = None,
        text_payload: str | None = None,
        variables: Sequence[VariableLike] | None = None,
        format: TemplateFormat | None = None,
        source_locale: TemplateLocale | None = None,
        is_active: bool | None = None,
    ) -> CoffeeMailResponse[TemplateDetail]:
        body = build_input(
            lambda: _template_body(
                name=name,
                html=html,
                alias=alias,
                subject=subject,
                preheader=preheader,
                content_json=content_json,
                text_payload=text_payload,
                variables=variables,
                format=format,
                source_locale=source_locale,
                is_active=is_active,
            ),
            self._transport.locale,
        )
        if isinstance(body, ValidationError):
            return input_failure(body)
        res = await self._transport.request(
            "PATCH", f"{TEMPLATES_PATH}/{template_id}", json_data=body
        )
        return parse_model(res, TemplateDetail, self._transport.locale)

    async def delete(self, template_id: str) -> CoffeeMailResponse[dict[str, object]]:
        return await self._transport.request("DELETE", f"{TEMPLATES_PATH}/{template_id}")

    async def preview(
        self,
        html: str,
        *,
        format: TemplateFormat | None = None,
        variables: Mapping[str, object] | None = None,
    ) -> CoffeeMailResponse[PreviewTemplateResponse]:
        res = await self._transport.request(
            "POST", f"{TEMPLATES_PATH}/preview", json_data=_render_body(html, format, variables)
        )
        return parse_model(res, PreviewTemplateResponse, self._transport.locale)

    async def preview_by_id(
        self, template_id: str, variables: Mapping[str, object] | None = None
    ) -> CoffeeMailResponse[PreviewTemplateResponse]:
        """Busca o template salvo e o renderiza (duas requisições: get + preview)."""
        template = await self.get(template_id)
        if template.error or template.data is None:
            return CoffeeMailResponse(
                data=None, error=template.error, status_code=template.status_code
            )
        stored = template.data
        return await self.preview(
            stored.html, format=_known_format(stored.format), variables=variables
        )

    async def format(
        self, html: str, *, format: TemplateFormat | None = None
    ) -> CoffeeMailResponse[FormatTemplateResponse]:
        res = await self._transport.request(
            "POST", f"{TEMPLATES_PATH}/format", json_data=compact(html=html, format=format)
        )
        return parse_model(res, FormatTemplateResponse, self._transport.locale)

    async def test_render(
        self,
        html: str,
        *,
        format: TemplateFormat | None = None,
        variables: Mapping[str, object] | None = None,
    ) -> CoffeeMailResponse[TestRenderTemplateResponse]:
        res = await self._transport.request(
            "POST",
            f"{TEMPLATES_PATH}/test-render",
            json_data=_render_body(html, format, variables),
        )
        return parse_model(res, TestRenderTemplateResponse, self._transport.locale)

    async def test_send(
        self,
        template_id: str,
        to: str,
        *,
        from_email: str | None = None,
        subject: str | None = None,
        variables: Mapping[str, object] | None = None,
    ) -> CoffeeMailResponse[TestSendResult]:
        res = await self._transport.request(
            "POST",
            f"{TEMPLATES_PATH}/{template_id}/test-send",
            json_data=_test_send_body(to, from_email, subject, variables),
        )
        return parse_model(res, TestSendResult, self._transport.locale)

    async def list_versions(
        self, template_id: str, *, limit: int | None = None, offset: int | None = None
    ) -> CoffeeMailResponse[ListTemplateVersionsResponse]:
        """Lista as versões do template, da mais recente para a mais antiga."""
        res = await self._transport.request(
            "GET", _versions_path(template_id), params=compact(limit=limit, offset=offset)
        )
        return parse_model(res, ListTemplateVersionsResponse, self._transport.locale)

    async def get_version(
        self, template_id: str, version: int
    ) -> CoffeeMailResponse[TemplateVersionDetail]:
        res = await self._transport.request("GET", _version_path(template_id, version))
        return parse_model(res, TemplateVersionDetail, self._transport.locale)

    async def restore_version(
        self, template_id: str, version: int
    ) -> CoffeeMailResponse[TemplateDetail]:
        """Restaura o conteúdo de uma versão; a restauração gera uma versão nova."""
        res = await self._transport.request(
            "POST", f"{_version_path(template_id, version)}/restore"
        )
        return parse_model(res, TemplateDetail, self._transport.locale)


_KNOWN_FORMATS: dict[str, TemplateFormat] = {"html": "html", "react": "react"}


def _known_format(value: str) -> TemplateFormat | None:
    return _KNOWN_FORMATS.get(value)
