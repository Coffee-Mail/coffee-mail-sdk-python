from coffeemail.core.http import AsyncHttpTransport, HttpTransport
from coffeemail.core.types import CoffeeMailResponse
from coffeemail.models.templates import (
    ListTemplatesResponse,
    PreviewTemplateResponse,
    TemplateDetail,
)


class Templates:
    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport

    def list(
        self,
        limit: int | None = None,
        after: str | None = None,
    ) -> CoffeeMailResponse[ListTemplatesResponse]:
        params: dict[str, object] = {}
        if limit is not None:
            params["limit"] = limit
        if after is not None:
            params["after"] = after

        res = self._transport.request("GET", "/v1/product/templates", params=params)
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=ListTemplatesResponse.model_validate(res.data),
            error=None,
            status_code=res.status_code,
        )

    def get(self, template_id: str) -> CoffeeMailResponse[TemplateDetail]:
        res = self._transport.request("GET", f"/v1/product/templates/{template_id}")
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=TemplateDetail.model_validate(res.data), error=None, status_code=res.status_code
        )

    def create(
        self,
        name: str,
        html: str,
        subject: str | None = None,
        description: str | None = None,
        text: str | None = None,
    ) -> CoffeeMailResponse[TemplateDetail]:
        body: dict[str, object] = {"name": name, "html": html}
        if subject is not None:
            body["subject"] = subject
        if description is not None:
            body["description"] = description
        if text is not None:
            body["text"] = text

        res = self._transport.request("POST", "/v1/product/templates", json_data=body)
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=TemplateDetail.model_validate(res.data), error=None, status_code=res.status_code
        )

    def update(
        self,
        template_id: str,
        name: str | None = None,
        html: str | None = None,
        subject: str | None = None,
        description: str | None = None,
        text: str | None = None,
    ) -> CoffeeMailResponse[TemplateDetail]:
        body: dict[str, object] = {}
        if name is not None:
            body["name"] = name
        if html is not None:
            body["html"] = html
        if subject is not None:
            body["subject"] = subject
        if description is not None:
            body["description"] = description
        if text is not None:
            body["text"] = text

        res = self._transport.request(
            "PATCH", f"/v1/product/templates/{template_id}", json_data=body
        )
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=TemplateDetail.model_validate(res.data), error=None, status_code=res.status_code
        )

    def delete(self, template_id: str) -> CoffeeMailResponse[dict[str, object]]:
        return self._transport.request("DELETE", f"/v1/product/templates/{template_id}")

    def preview(
        self,
        html: str | None = None,
        template_id: str | None = None,
        variables: dict[str, object] | None = None,
    ) -> CoffeeMailResponse[PreviewTemplateResponse]:
        body: dict[str, object] = {}
        if html:
            body["html"] = html
        if template_id:
            body["templateId"] = template_id
        if variables:
            body["variables"] = variables

        res = self._transport.request("POST", "/v1/product/templates/preview", json_data=body)
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=PreviewTemplateResponse.model_validate(res.data),
            error=None,
            status_code=res.status_code,
        )

    def test_send(
        self,
        template_id: str,
        to: str,
        variables: dict[str, object] | None = None,
    ) -> CoffeeMailResponse[dict[str, object]]:
        body: dict[str, object] = {"to": to}
        if variables:
            body["variables"] = variables
        return self._transport.request(
            "POST", f"/v1/product/templates/{template_id}/test-send", json_data=body
        )

    def format(self, payload: dict[str, object]) -> CoffeeMailResponse[dict[str, object]]:
        return self._transport.request("POST", "/v1/product/templates/format", json_data=payload)

    def test_render(self, payload: dict[str, object]) -> CoffeeMailResponse[dict[str, object]]:
        return self._transport.request(
            "POST", "/v1/product/templates/test-render", json_data=payload
        )


class AsyncTemplates:
    def __init__(self, transport: AsyncHttpTransport) -> None:
        self._transport = transport

    async def list(
        self,
        limit: int | None = None,
        after: str | None = None,
    ) -> CoffeeMailResponse[ListTemplatesResponse]:
        params: dict[str, object] = {}
        if limit is not None:
            params["limit"] = limit
        if after is not None:
            params["after"] = after

        res = await self._transport.request("GET", "/v1/product/templates", params=params)
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=ListTemplatesResponse.model_validate(res.data),
            error=None,
            status_code=res.status_code,
        )

    async def get(self, template_id: str) -> CoffeeMailResponse[TemplateDetail]:
        res = await self._transport.request("GET", f"/v1/product/templates/{template_id}")
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=TemplateDetail.model_validate(res.data), error=None, status_code=res.status_code
        )

    async def create(
        self,
        name: str,
        html: str,
        subject: str | None = None,
        description: str | None = None,
        text: str | None = None,
    ) -> CoffeeMailResponse[TemplateDetail]:
        body: dict[str, object] = {"name": name, "html": html}
        if subject is not None:
            body["subject"] = subject
        if description is not None:
            body["description"] = description
        if text is not None:
            body["text"] = text

        res = await self._transport.request("POST", "/v1/product/templates", json_data=body)
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=TemplateDetail.model_validate(res.data), error=None, status_code=res.status_code
        )

    async def update(
        self,
        template_id: str,
        name: str | None = None,
        html: str | None = None,
        subject: str | None = None,
        description: str | None = None,
        text: str | None = None,
    ) -> CoffeeMailResponse[TemplateDetail]:
        body: dict[str, object] = {}
        if name is not None:
            body["name"] = name
        if html is not None:
            body["html"] = html
        if subject is not None:
            body["subject"] = subject
        if description is not None:
            body["description"] = description
        if text is not None:
            body["text"] = text

        res = await self._transport.request(
            "PATCH", f"/v1/product/templates/{template_id}", json_data=body
        )
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=TemplateDetail.model_validate(res.data), error=None, status_code=res.status_code
        )

    async def delete(self, template_id: str) -> CoffeeMailResponse[dict[str, object]]:
        return await self._transport.request("DELETE", f"/v1/product/templates/{template_id}")

    async def preview(
        self,
        html: str | None = None,
        template_id: str | None = None,
        variables: dict[str, object] | None = None,
    ) -> CoffeeMailResponse[PreviewTemplateResponse]:
        body: dict[str, object] = {}
        if html:
            body["html"] = html
        if template_id:
            body["templateId"] = template_id
        if variables:
            body["variables"] = variables

        res = await self._transport.request("POST", "/v1/product/templates/preview", json_data=body)
        if res.error or res.data is None:
            return CoffeeMailResponse(data=None, error=res.error, status_code=res.status_code)
        return CoffeeMailResponse(
            data=PreviewTemplateResponse.model_validate(res.data),
            error=None,
            status_code=res.status_code,
        )

    async def test_send(
        self,
        template_id: str,
        to: str,
        variables: dict[str, object] | None = None,
    ) -> CoffeeMailResponse[dict[str, object]]:
        body: dict[str, object] = {"to": to}
        if variables:
            body["variables"] = variables
        return await self._transport.request(
            "POST", f"/v1/product/templates/{template_id}/test-send", json_data=body
        )

    async def format(self, payload: dict[str, object]) -> CoffeeMailResponse[dict[str, object]]:
        return await self._transport.request(
            "POST", "/v1/product/templates/format", json_data=payload
        )

    async def test_render(
        self, payload: dict[str, object]
    ) -> CoffeeMailResponse[dict[str, object]]:
        return await self._transport.request(
            "POST", "/v1/product/templates/test-render", json_data=payload
        )
