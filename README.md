<div align="center">

# ☕ coffeemail (SDK Python)

**SDK oficial da CoffeeMail para Python: clientes síncrono e assíncrono, modelos Pydantic v2 e tipagem estrita, para quem envia e-mail transacional pela API CoffeeMail.**

[![PyPI](https://img.shields.io/pypi/v/coffeemail?style=flat-square&color=3178C6)](https://pypi.org/project/coffeemail/)
[![Python](https://img.shields.io/pypi/pyversions/coffeemail?style=flat-square&color=3776AB)](https://pypi.org/project/coffeemail/)
[![CI](https://github.com/Coffee-Mail/coffee-mail-sdk-python/actions/workflows/ci.yml/badge.svg)](https://github.com/Coffee-Mail/coffee-mail-sdk-python/actions/workflows/ci.yml)
[![mypy strict](https://img.shields.io/badge/mypy-strict-blue?style=flat-square)](https://mypy-lang.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg?style=flat-square)](https://github.com/Coffee-Mail/coffee-mail-sdk-python/blob/main/LICENSE)

[Início rápido](#-início-rápido) · [Configuração](#️-configuração) · [Erros](#️-tratamento-de-erros) · [Referência](#-referência) · [Webhooks](#-webhooks) · [Status](#-status-do-projeto)

</div>

---

## 📑 Sumário

- [✨ Visão geral](#-visão-geral)
- [🚦 Status do projeto](#-status-do-projeto)
- [📋 Requisitos](#-requisitos)
- [📦 Instalação](#-instalação)
- [🚀 Início rápido](#-início-rápido)
- [⚙️ Configuração](#️-configuração)
- [🛡️ Tratamento de erros](#️-tratamento-de-erros)
- [📚 Referência](#-referência)
- [🔔 Webhooks](#-webhooks)
- [🔖 Versionamento e releases](#-versionamento-e-releases)
- [🧪 Testes e qualidade](#-testes-e-qualidade)
- [🗂️ Estrutura do repositório](#️-estrutura-do-repositório)
- [🤝 Contribuição](#-contribuição)
- [🔗 Projetos relacionados](#-projetos-relacionados)
- [📄 Licença](#-licença)

---

## ✨ Visão geral

`coffeemail` é a biblioteca cliente da API de produto da CoffeeMail (`/v1/product/*`).

- **Dois clientes com a mesma superfície:** `CoffeeMail` (síncrono, sobre `httpx.Client`) e `AsyncCoffeeMail` (assíncrono, sobre `httpx.AsyncClient`). Cada método do cliente síncrono existe no assíncrono com o mesmo nome, como corrotina.
- **Envelope em vez de exceção:** toda chamada de recurso retorna `CoffeeMailResponse[T]` com `data`, `error` e `status_code`. Erros HTTP e de rede viram `error`; nada é lançado, exceto quando você chama `.unwrap()`.
- **Modelos Pydantic v2:** as respostas tipadas usam campos `snake_case` mapeados para o `camelCase` da API. O pacote traz o marcador PEP 561 (`py.typed`).
- **Mensagens locais em pt-BR ou en** e cabeçalho `Accept-Language` conforme o `locale` escolhido.
- **Introspecção da chave de API** com cache em memória de 300 segundos.

Recursos expostos no cliente: `emails`, `domains`, `templates`, `audiences` (com `audiences.contacts`), `broadcasts`, `senders`, `suppressions`, `webhooks` e `stats`, além de `introspect()`.

---

## 🚦 Status do projeto

Classificador no PyPI: `Development Status :: 4 - Beta`.

### Versão publicada × `main`

A versão no PyPI é a **0.1.1** (publicada em 2026-10-08). A `main` declara a **0.2.0**, ainda não publicada, que corrige o contrato com a API e **quebra a compatibilidade** com a 0.1.1 em vários pontos (verificação de webhook, `code` dos erros, parâmetros de contatos, campanhas, estatísticas e supressões). Como o SDK ainda não tinha usuários ativos, a correção foi feita direto, sem camada de depreciação. A lista completa está no [CHANGELOG.md](CHANGELOG.md).

A [Referência](#-referência) descreve a `main` (0.2.0).

### Limitações conhecidas

- **Tipagem do desempacotamento.** `data, error = resposta` funciona em runtime, mas `__iter__` é tipado como `Iterator[object | None]`: sob mypy, `data` vira `object | None`. Para acesso tipado, use `resposta.data` (após checar `None`) ou `.unwrap()`.
- **Sem retry automático.** `429` e `5xx` chegam no envelope; `RateLimitError.retry_after_seconds` traz o `Retry-After` da API (hoje sempre `60`). Um `429` com `api_code == "PLAN_QUOTA_EXCEEDED"` é cota do plano esgotada e não adianta repetir.
- **Sem `close()` nem context manager** nos clientes. Para controlar o ciclo de vida da conexão, passe seu próprio `httpx.Client` / `httpx.AsyncClient` em `http_client` e feche-o você mesmo.
- **Respostas sem modelo.** Exclusões e algumas ações sem corpo útil (`emails.cancel`, `*.delete`, `suppressions.reactivate`) retornam `dict[str, object]`.
- **Único ponto que lança exceção:** o construtor lança `AuthenticationError` sem `api_key` e sem `COFFEEMAIL_API_KEY`. Entrada malformada (destinatário, anexo, contatos em lote, supressões em lote, variáveis de template) volta no envelope como `ValidationError` local, sem chamada de rede. Construir um modelo Pydantic do SDK com dados inválidos (`SendEmailPayload(...)`, `ContactInput(...)`) continua lançando `pydantic.ValidationError` no seu código, antes de chegar ao SDK.
- **Deduplicação de envio.** Sem `idempotency_key`, a API trata envios com payload idêntico como o mesmo envio e devolve o id original.

---

## 📋 Requisitos

| Item | Versão |
| --- | --- |
| Python | `>=3.10` (CI e classificadores cobrem 3.10, 3.11 e 3.12) |
| `httpx` | `>=0.27.0` |
| `pydantic` | `>=2.6.0` |
| `typing-extensions` | `>=4.10.0` |

Você também precisa de uma chave de API da CoffeeMail (`cm_live_...` ou `cm_test_...`), gerada no dashboard.

---

## 📦 Instalação

```bash
uv add coffeemail
```

```bash
pip install coffeemail
```

```bash
poetry add coffeemail
```

---

## 🚀 Início rápido

### Cliente síncrono (Django, Flask, scripts)

```python
from coffeemail import CoffeeMail

client = CoffeeMail("cm_live_sua_chave_aqui")

response = client.emails.send(
    {
        "from": "Equipe Acme <contato@seudominio.com.br>",
        "to": "cliente@exemplo.com.br",
        "subject": "Boas-vindas!",
        "html": "<h1>Olá!</h1><p>Seu cadastro foi concluído.</p>",
    }
)

if response.error is not None:
    print(f"Falha no envio [{response.error.code}]: {response.error.message}")
elif response.data is not None:
    print(f"E-mail enfileirado: {response.data.id} ({response.data.status})")
```

Os campos `from`, `to`, `cc`, `bcc` e `replyTo` aceitam uma string (`"email@x.com"` ou `"Nome <email@x.com>"`), um `EmailParticipant`, um dicionário `{"email", "name"}` ou, para `to`/`cc`/`bcc`, uma lista desses valores.

### Cliente assíncrono (FastAPI, Starlette, workers)

```python
import asyncio

from coffeemail import AsyncCoffeeMail


async def main() -> None:
    client = AsyncCoffeeMail()

    response = await client.emails.send(
        {
            "from": {"email": "financeiro@seudominio.com.br", "name": "Financeiro"},
            "to": ["destinatario@exemplo.com.br"],
            "subject": "Sua fatura foi gerada",
            "html": "<p>Acesse o painel para ver o comprovante.</p>",
        }
    )

    if response.error is not None:
        print(f"Erro: {response.error.message}")
        return

    if response.data is not None:
        print(f"Status: {response.data.status}")


asyncio.run(main())
```

`AsyncCoffeeMail()` sem argumentos lê a chave de `COFFEEMAIL_API_KEY`.

---

## ⚙️ Configuração

`CoffeeMail` e `AsyncCoffeeMail` aceitam os mesmos parâmetros:

| Parâmetro | Tipo | Default | Descrição |
| --- | --- | --- | --- |
| `api_key` | `str \| None` (posicional) | `None` → `COFFEEMAIL_API_KEY` | Chave de API, enviada como `Authorization: Bearer <chave>`. Espaços nas pontas são removidos. Vazia ou ausente lança `AuthenticationError`. |
| `timeout` | `float` (keyword) | `10.0` | Timeout em segundos do cliente HTTP criado pelo SDK. Ignorado quando você passa `http_client`. |
| `locale` | `"pt-BR" \| "en"` (keyword) | `"pt-BR"` | Idioma das mensagens locais do SDK e valor do cabeçalho `Accept-Language`. |
| `http_client` | `httpx.Client` (síncrono) / `httpx.AsyncClient` (assíncrono) | `None` | Cliente HTTP próprio (proxy, transporte, limites de conexão, mocks). |

| Variável de ambiente | Uso |
| --- | --- |
| `COFFEEMAIL_API_KEY` | Chave usada quando `api_key` não é informado. |

O host da API é fixo em `https://api.coffeemail.com.br` e não é configurável. É uma decisão de segurança: a chave de API só trafega para o host oficial. Passar `base_url` lança `TypeError`.

Cabeçalhos enviados em toda requisição: `Authorization`, `Accept: application/json`, `Accept-Language` e `User-Agent: coffeemail-python/<versão>`; `Content-Type: application/json` só quando há corpo. No envio de e-mail, `idempotency_key` vira `X-Idempotency-Key` e `sandbox=True` vira `X-Coffeemail-Sandbox: true`. O cliente HTTP criado pelo SDK não segue redirecionamentos.

```python
import httpx

from coffeemail import CoffeeMail

client = CoffeeMail(
    locale="en",
    http_client=httpx.Client(timeout=30.0),
)
```

---

## 🛡️ Tratamento de erros

Todo método de recurso retorna `CoffeeMailResponse[T]`:

| Membro | Tipo | Descrição |
| --- | --- | --- |
| `data` | `T \| None` | Resultado em caso de sucesso. |
| `error` | `CoffeeMailError \| None` | Erro HTTP, de rede ou de validação local. |
| `status_code` | `int \| None` | Status HTTP; `0` em validação local; `None` em erro de rede. |
| `is_success` | `bool` | `True` quando `error is None`. |
| `unwrap()` | `T` | Retorna `data`; lança o `error` se houver, ou `ValueError` se `data` for `None`. |
| `__iter__` | — | Permite `data, error = resposta`. |

### Três formas de consumir

Desempacotamento em tupla, acesso por atributo e `.unwrap()`. Como o desempacotamento é tipado como `object | None`, use `isinstance` para o mypy enxergar o tipo do erro.

```python
from coffeemail import CoffeeMail, CoffeeMailError, NotFoundError

client = CoffeeMail()

data, error = client.emails.get("eml_123456")
if isinstance(error, CoffeeMailError):
    print(f"Erro {error.status_code} [{error.code}]: {error.message}")

response = client.emails.get("eml_123456")
if response.data is not None:
    print(f"Status atual: {response.data.status}")

try:
    email = client.emails.get("eml_123456").unwrap()
    print(f"Entregue em: {email.delivered_at}")
except NotFoundError:
    print("E-mail não encontrado")
except CoffeeMailError as err:
    print(f"Falha: {err}")
```

### Classes de erro

Todas herdam de `CoffeeMailError` e são exportadas por `coffeemail`. Cada erro tem:

| Atributo | Descrição |
| --- | --- |
| `message` | Mensagem da API ou, na falta dela, a mensagem local no idioma configurado. |
| `status_code` | Status HTTP; `0` em validação local; `None` em erro de rede. |
| `code` | Código canônico, igual em todos os SDKs oficiais (tabela abaixo). |
| `api_code` | Código original enviado pela API (ex.: `PLAN_QUOTA_EXCEEDED`, `EMAIL_NOT_FOUND`). |
| `details` | `meta` + `details` do corpo de erro (em validação, `details["issues"]` lista os campos). |
| `request_id` | Valor do header `x-request-id` da resposta, quando houver. |

| Classe | Status HTTP | `code` |
| --- | --- | --- |
| `ValidationError` | `400`, ou `0` em validação local (mensagem localizada; `details["errors"]` lista os campos) | `VALIDATION_ERROR` |
| `AuthenticationError` | `401` (e construtor sem chave) | `UNAUTHORIZED` |
| `PaymentRequiredError` | `402` | `PAYMENT_REQUIRED` |
| `ForbiddenError` | `403` | `FORBIDDEN` |
| `PermissionDeniedError` (subclasse de `ForbiddenError`) | `403` em `broadcasts` | `PERMISSION_DENIED`, com `required_permission="full_access"` |
| `NotFoundError` | `404` | `NOT_FOUND` |
| `ConflictError` | `409` | `CONFLICT` |
| `RateLimitError` | `429` | `RATE_LIMIT_EXCEEDED`, com `retry_after_seconds` |
| `ServerError` | `500`, `502`, `503`, `504` | `INTERNAL_SERVER_ERROR` |
| `NetworkError` | — (timeout ou falha de conexão) | `NETWORK_ERROR` |
| `CoffeeMailError` | outros status | código da API ou `API_ERROR`; `INVALID_RESPONSE` quando um 2xx vem ilegível |

---

## 📚 Referência

Os caminhos abaixo são relativos a `https://api.coffeemail.com.br`. Todos os recursos existem nos dois clientes; no `AsyncCoffeeMail` os métodos são `async`, exceto `webhooks.verify_signature` e `invalidate_introspection_cache`. A tabela descreve a `main` (0.2.0).

### Introspecção

| Método | Retorno | Endpoint |
| --- | --- | --- |
| `client.introspect(force_refresh=False)` | `ApiKeyIntrospection` | `GET /v1/product/auth/me/api-key` |
| `client.invalidate_introspection_cache()` | `None` | — |

O resultado fica em cache por 300 segundos por instância de cliente. `ApiKeyIntrospection` tem `id`, `name`, `organisation_id` e `scopes`.

### Emails — `client.emails`

| Método | Retorno | Endpoint |
| --- | --- | --- |
| `send(payload: SendEmailPayload \| dict)` | `SendEmailResponse` | `POST /v1/product/emails` |
| `send_batch(emails: list[SendEmailPayload \| dict])` | `list[BatchSendEmailResult]` | `POST /v1/product/emails/batch` |
| `get(email_id)` | `EmailDetail` | `GET /v1/product/emails/{id}` |
| `list(limit=None, after=None, status=None, *, recipient, tag, from_date, to_date)` | `ListEmailsResponse` | `GET /v1/product/emails` |
| `get_events(email_id)` | `EmailEventsResponse` | `GET /v1/product/emails/{id}/events` |
| `get_tags()` | `ListEmailTagsResponse` | `GET /v1/product/emails/tags` |
| `cancel(email_id)` | `dict` | `POST /v1/product/emails/{id}/cancel` |
| `resend(email_id)` | `SendEmailResponse` | `POST /v1/product/emails/{id}/resend` |

Campos de `SendEmailPayload` (ou chaves do dicionário): `from`, `to`, `subject`, `html`, `text`, `cc`, `bcc`, `replyTo`, `headers`, `attachments`, `tags`, `templateId`, `variables`, `emailType`, `suppressionCategory`, `scheduledAt` e `metadata`, além de `idempotency_key` e `sandbox`, que viram headers. Anexos (`EmailAttachment` ou dicionário com `filename`, `content`, `contentType`, `disposition`, `cid`) aceitam em `content` bytes (codificados em base64 pelo SDK), o caminho de um arquivo existente ou uma string já em base64. Em `send_batch`, o lote usa um único conjunto de headers (vale a última `idempotency_key` informada).

```python
from coffeemail import EmailAttachment, SendEmailPayload

response = client.emails.send(
    SendEmailPayload(
        from_address="contato@seudominio.com.br",
        to="cliente@exemplo.com.br",
        subject="Seu relatório",
        text="Segue o relatório em anexo.",
        attachments=[EmailAttachment(filename="relatorio.pdf", content=b"%PDF-1.7 ...")],
        idempotency_key="relatorio-2026-10",
    )
)

page = client.emails.list(limit=20, status="delivered").unwrap()
for email in page.emails:
    print(email.id, email.to, email.status)
```

### Domains — `client.domains`

| Método | Retorno | Endpoint |
| --- | --- | --- |
| `list()` | `ListDomainsResponse` | `GET /v1/product/domains` |
| `get(domain_id)` | `DomainDetail` | `GET /v1/product/domains/{id}` |
| `create(name)` | `CreateDomainResponse` | `POST /v1/product/domains` |
| `verify(domain_id)` | `DomainDetail` (com `checks` e `required_checks`) | `POST /v1/product/domains/{id}/verify` |
| `delete(domain_id)` | `dict` | `DELETE /v1/product/domains/{id}` |
| `get_health(domain_id)` | `DomainHealthResponse` | `POST /v1/product/domains/{id}/health` |
| `get_warmup_status(domain_id)` | `DomainWarmupStatus \| None` | `GET /v1/product/domains/{id}/warmup` |
| `rotate_dkim(domain_id)` | `DkimRotation` | `POST /v1/product/domains/{id}/dkim/rotate` |
| `set_tracking_domain(domain_id, host)` | `CustomHostStatus` | `PUT /v1/product/domains/{id}/tracking-domain` |
| `remove_tracking_domain(domain_id)` | `CustomHostStatus \| None` | `DELETE /v1/product/domains/{id}/tracking-domain` |

```python
created = client.domains.create("seudominio.com.br").unwrap()
for record in created.dkim_records_to_publish:
    print(record.type, record.host, record.value)

domain = client.domains.verify(created.id).unwrap()
print(domain.status, domain.status_reason)
```

`DomainDetail` traz também `dkim_rotation` (`DkimRotation | None`), `return_path` e `tracking_domain` (`CustomHostStatus | None`, com `host`, `target`, `verified`, `verified_at` e o `record` CNAME a publicar) e `tracking_domains_available`. `DomainWarmupStatus` informa `status` (`warming` ou `completed`), `total_days`, `started_at` e `completed_at`.

```python
rotation = client.domains.rotate_dkim(domain.id).unwrap()
print(rotation.selector, rotation.record.host, rotation.record.value)

tracking = client.domains.set_tracking_domain(domain.id, "links.seudominio.com.br").unwrap()
print(tracking.record.type, tracking.record.host, tracking.record.value, tracking.verified)
```

`rotate_dkim` é idempotente: enquanto houver rotação pendente, devolve a mesma. A chave em uso só muda quando o TXT do novo seletor é encontrado no DNS. Erros: `NotFoundError` (`api_code="DOMAIN_NOT_FOUND"`) e `ConflictError` (`api_code="DOMAIN_NOT_VERIFIED"`). `set_tracking_domain` responde `ValidationError` (`api_code="INVALID_TRACKING_HOST"`) para host fora do domínio de envio e `ConflictError` (`api_code="TRACKING_DOMAINS_DISABLED"`) quando a plataforma não oferece tracking próprio.

### Templates — `client.templates`

| Método | Retorno | Endpoint |
| --- | --- | --- |
| `list()` | `ListTemplatesResponse` (`data`) | `GET /v1/product/templates` |
| `get(template_id)` | `TemplateDetail` | `GET /v1/product/templates/{id}` |
| `create(name, html, *, alias, subject, preheader, content_json, text_payload, variables, format, source_locale)` | `TemplateDetail` | `POST /v1/product/templates` |
| `update(template_id, *, ...mesmos campos..., is_active)` | `TemplateDetail` | `PATCH /v1/product/templates/{id}` |
| `delete(template_id)` | `dict` | `DELETE /v1/product/templates/{id}` |
| `preview(html, *, format=None, variables=None)` | `PreviewTemplateResponse` | `POST /v1/product/templates/preview` |
| `preview_by_id(template_id, variables=None)` | `PreviewTemplateResponse` | `GET /templates/{id}` + `POST /templates/preview` |
| `format(html, *, format=None)` | `FormatTemplateResponse` | `POST /v1/product/templates/format` |
| `test_render(html, *, format=None, variables=None)` | `TestRenderTemplateResponse` | `POST /v1/product/templates/test-render` |
| `test_send(template_id, to, *, from_email, subject, variables)` | `TestSendResult` | `POST /v1/product/templates/{id}/test-send` |

```python
template = client.templates.create(
    "boas-vindas",
    "<p>Olá, {{nome}}!</p>",
    subject="Olá, {{nome}}",
    variables=[{"name": "nome", "fallbackValue": "cliente"}],
).unwrap()

preview = client.templates.preview_by_id(template.id, {"nome": "Ana"}).unwrap()
print(preview.html)
```

### Audiences — `client.audiences`

| Método | Retorno | Endpoint |
| --- | --- | --- |
| `list(limit=None, offset=None)` | `ListAudiencesResponse` | `GET /v1/product/audiences` |
| `get(audience_id)` | `AudienceDetail` | `GET /v1/product/audiences/{id}` |
| `create(name, description=None)` | `AudienceDetail` | `POST /v1/product/audiences` |
| `update(audience_id, *, name, description, active)` | `UpdateResult` | `PUT /v1/product/audiences/{id}` |
| `delete(audience_id)` | `dict` | `DELETE /v1/product/audiences/{id}` |
| `list_contacts`, `create_contact`, `bulk_add_contacts`, `update_contact` | — | atalhos para `client.audiences.contacts` |

### Contacts — `client.audiences.contacts`

| Método | Retorno | Endpoint |
| --- | --- | --- |
| `list(audience_id, limit=None, offset=None)` | `ListContactsResponse` (`contacts`, `total`) | `GET /v1/product/audiences/{id}/contacts` |
| `create(audience_id, email, *, first_name, last_name, metadata)` | `ContactDetail` | `POST /v1/product/audiences/{id}/contacts` |
| `bulk_add(audience_id, contacts: list[ContactInput \| dict])` | `BulkAddContactsResponse` | `POST /v1/product/audiences/{id}/contacts/bulk` (até 10 000) |
| `update(audience_id, contact_id, *, first_name, last_name, metadata)` | `UpdateResult` | `PUT /v1/product/audiences/{id}/contacts/{contactId}` |
| `delete(audience_id, contact_id)` | `dict` | `DELETE /v1/product/audiences/{id}/contacts/{contactId}` |

```python
audience = client.audiences.create("Clientes ativos").unwrap()
result = client.audiences.contacts.bulk_add(
    audience.id,
    [{"email": "ana@exemplo.com.br", "first_name": "Ana"}, {"email": "bruno@exemplo.com.br"}],
).unwrap()
print(result.inserted, result.skipped, result.errors)
```

### Broadcasts — `client.broadcasts`

Toda operação exige chave `full_access`; sem ela, o erro é `PermissionDeniedError` (`code == "PERMISSION_DENIED"`).

| Método | Retorno | Endpoint |
| --- | --- | --- |
| `list(limit=None, after=None, *, status, from_date, to_date)` | `ListBroadcastsResponse` | `GET /v1/product/broadcasts` |
| `get(broadcast_id)` | `BroadcastDetail` | `GET /v1/product/broadcasts/{id}` |
| `create(*, audience_id, from_email, subject, template_id, html, text, reply_to, variables)` | `BroadcastDetail` | `POST /v1/product/broadcasts` |
| `send(broadcast_id)` | `SendBroadcastResult` | `POST /v1/product/broadcasts/{id}/send` |
| `cancel(broadcast_id)` | `CancelBroadcastResult` | `POST /v1/product/broadcasts/{id}/cancel` |
| `test_send(broadcast_id, to, variables=None)` | `TestSendResult` | `POST /v1/product/broadcasts/{id}/test-send` |

`BroadcastDetail.status` é `draft`, `scheduled`, `sending`, `sent`, `failed` ou `cancelled`.

```python
broadcast = client.broadcasts.create(
    audience_id=audience.id,
    from_email="news@seudominio.com.br",
    template_id=template.id,
).unwrap()
client.broadcasts.send(broadcast.id)
```

### Senders — `client.senders`

| Método | Retorno | Endpoint |
| --- | --- | --- |
| `create(email, display_name=None)` | `CreatedSender` (com `verification_token`) | `POST /v1/product/senders` |
| `list()` | `ListSendersResponse` (`senders: list[SenderDetail]`) | `GET /v1/product/senders` |
| `verify(token)` | `VerifySenderResult` | `POST /v1/product/senders/verify` |
| `delete(sender_id)` | `dict` | `DELETE /v1/product/senders/{id}` |

### Suppressions — `client.suppressions`

| Método | Retorno | Endpoint |
| --- | --- | --- |
| `list(limit=None, after=None, *, status, reason, source, category)` | `ListSuppressionsResponse` | `GET /v1/product/suppressions` |
| `get(suppression_id)` | `SuppressionDetail` | `GET /v1/product/suppressions/{id}` |
| `create(email, reason="manual", expires_at=None)` | `SuppressionDetail` | `POST /v1/product/suppressions` |
| `delete(suppression_id)` | `dict` | `DELETE /v1/product/suppressions/{id}` |
| `reactivate(suppression_id)` | `dict` | `POST /v1/product/suppressions/{id}/reactivate` |
| `bulk_create(entries: list[BulkSuppressionEntry \| dict])` | `BulkCreateSuppressionsResult` | `POST /v1/product/suppressions/bulk` (até 1000) |

Na criação, `reason` aceita `manual`, `bounce` ou `complaint`. A rota usa o **id** da supressão: passar um e-mail para `get`/`delete` retorna `ValidationError` local, sem chamada de rede.

### Webhooks — `client.webhooks`

| Método | Retorno | Endpoint |
| --- | --- | --- |
| `list(status=None)` | `ListWebhooksResponse` | `GET /v1/product/webhooks` |
| `get(webhook_id)` | `WebhookDetail` | `GET /v1/product/webhooks/{id}` |
| `create(url, events, description=None)` | `CreatedWebhookDetail` | `POST /v1/product/webhooks` |
| `update(webhook_id, *, url, events, description)` | `WebhookDetail` | `PUT /v1/product/webhooks/{id}` |
| `toggle(webhook_id, enabled: bool)` | `ToggleWebhookResult` | `PATCH /v1/product/webhooks/{id}` |
| `delete(webhook_id)` | `dict` | `DELETE /v1/product/webhooks/{id}` |
| `rotate_secret(webhook_id)` | `RotateWebhookSecretResult` | `POST /v1/product/webhooks/{id}/rotate-secret` |
| `list_deliveries(webhook_id, *, event_type, status, from_date, to_date, limit)` | `ListWebhookDeliveriesResponse` | `GET /v1/product/webhooks/{id}/deliveries` |
| `test(webhook_id)` | `TestWebhookResult` | `POST /v1/product/webhooks/{id}/test` |
| `verify_signature(payload, secret, *, headers, ...)` (estático) | `bool` | — (ver [Webhooks](#-webhooks)) |

O segredo (`secret`) só aparece em `CreatedWebhookDetail` e `RotateWebhookSecretResult`; guarde-o na hora.

### Stats — `client.stats`

| Método | Retorno | Endpoint |
| --- | --- | --- |
| `get(*, start_date, end_date, domain_id, tag, granularity, period, email_type)` | `EmailStats` | `GET /v1/product/stats` |

`EmailStats` traz os totais, `delivery_rate`, `open_rate` e `click_rate` (de 0 a 100), `breakdown`, `top_clients` e a série em `data`.

```python
stats = client.stats.get(period="last30d", granularity="day").unwrap()
print(f"Entregues: {stats.total_delivered} ({stats.delivery_rate:.1f}%)")
```

### Modelos e tipos exportados

`coffeemail` exporta os clientes, `CoffeeMailResponse`, `ApiKeyIntrospection`, as classes de erro, `verify_webhook_signature`, `sign_webhook` e todos os modelos de `coffeemail.models` (entradas como `SendEmailPayload`, `ContactInput`, `BulkSuppressionEntry`, `TemplateVariable`; respostas; e os tipos `Literal` dos enums). Os campos de enum das respostas aceitam valores novos da API sem falhar.

---

## 🔔 Webhooks

Cada entrega é um `POST` com corpo JSON (`event_type`, `webhook_id`, `data`) e estes cabeçalhos:

| Cabeçalho | Conteúdo |
| --- | --- |
| `x-webhook-signature` | `sha256=` + HMAC-SHA256 em hex de `"<timestamp>.<idempotencyKey>.<corpo>"`, com o segredo `whsec_...` do webhook |
| `x-webhook-timestamp` | Epoch em segundos; janela de 300 segundos |
| `x-webhook-idempotency-key` | Muda a cada tentativa de entrega; não serve para deduplicar retentativas |
| `x-webhook-test` | `true` em entregas disparadas por `webhooks.test()` |

Valide com o **corpo bruto** da requisição, nunca com o JSON re-serializado:

```python
from fastapi import FastAPI, HTTPException, Request

from coffeemail import verify_webhook_signature

app = FastAPI()


@app.post("/webhooks/coffeemail")
async def coffeemail_webhook(request: Request) -> None:
    body = await request.body()
    if not verify_webhook_signature(body, WEBHOOK_SECRET, headers=request.headers):
        raise HTTPException(status_code=401)
```

- `headers` aceita qualquer mapeamento (a busca ignora maiúsculas/minúsculas). Também é possível passar `signature`, `timestamp` e `idempotency_key` diretamente.
- `tolerance_seconds` (padrão 300) e `now` (relógio, útil em testes) são configuráveis.
- `sign_webhook(body, secret, timestamp, idempotency_key)` calcula a assinatura esperada, para testar o seu handler.
- `client.webhooks.verify_signature` e `Webhooks.verify_signature` são o mesmo verificador.
- O verificador passa nos vetores de teste compartilhados entre os SDKs oficiais (`tests/fixtures/webhook_vectors.json`), gerados pelo assinador da API.

---

## 🔖 Versionamento e releases

- **SemVer.** A versão fica em três lugares que precisam bater: `pyproject.toml`, `__version__` em `src/coffeemail/__init__.py` e `SDK_VERSION` em `src/coffeemail/core/http.py` (usado no `User-Agent`). `scripts/check_version_sync.py` falha a CI se divergirem.
- **Compatibilidade retroativa.** A partir da 0.2.0, mudanças na superfície pública **adicionam e depreciam; nunca renomeiam nem removem** métodos, parâmetros, modelos ou campos. A 0.2.0 foi a exceção: corrigiu o contrato direto porque o SDK ainda não tinha usuários ativos. Os SDKs oficiais (Node.js, Python, PHP, Java, Go e Ruby) mantêm o mesmo contrato.
- **Publicação.** O workflow [`publish.yml`](https://github.com/Coffee-Mail/coffee-mail-sdk-python/blob/main/.github/workflows/publish.yml) roda em push na `main` e em tags `v*`: executa ruff, mypy e pytest, consulta o PyPI e só constrói e publica se a versão do `pyproject.toml` ainda não existir lá. Para lançar, suba a versão nos três lugares acima e faça merge na `main`.
- **CHANGELOG.** As mudanças ficam no [CHANGELOG.md](CHANGELOG.md) (Keep a Changelog); toda mudança de comportamento entra em "Não lançado".

---

## 🧪 Testes e qualidade

```bash
uv sync --extra dev
uv run ruff format --check .
uv run ruff check .
uv run mypy src tests
uv run python scripts/check_version_sync.py
uv run pytest -v
uv build
```

| Comando | O que garante |
| --- | --- |
| `uv sync --extra dev` | Instala dependências de runtime e de dev (`mypy`, `openapi-core`, `pytest`, `pytest-asyncio`, `pytest-mock`, `respx`, `ruff`). |
| `uv run ruff format --check .` | Formatação (linha de 100 colunas). |
| `uv run ruff check .` | Lint: pycodestyle, pyflakes, isort, bugbear, comprehensions, pyupgrade, unused-arguments, simplify, type-checking e `RET` (sem `else` após `return`). |
| `uv run mypy src tests` | Tipagem `strict` com o plugin do Pydantic. |
| `uv run python scripts/check_version_sync.py` | Versões sincronizadas entre `pyproject.toml`, `__init__.py` e `core/http.py`. |
| `uv run pytest -v` | Suíte em `tests/` (HTTP simulado com `httpx.MockTransport`/`respx`, `asyncio_mode = "auto"`). Inclui o teste de contrato (`tests/test_contract.py`), que valida toda requisição do SDK contra `spec/product.json` com `openapi-core` e falha se alguma operação do spec ficar sem método, e os vetores de webhook compartilhados. |
| `uv run python scripts/sync_openapi.py [--check]` | Atualiza (ou só verifica) o snapshot `spec/product.json` a partir do spec público, ou de `COFFEEMAIL_OPENAPI_SPEC` (caminho local ou URL). |
| `uv run pytest tests/test_emails.py -k nome_do_teste` | Um arquivo ou caso específico. |
| `uv build` | Gera wheel e sdist em `dist/`. |

A CI ([`ci.yml`](https://github.com/Coffee-Mail/coffee-mail-sdk-python/blob/main/.github/workflows/ci.yml)) roda todos esses passos em push e PR para a `main`, nas versões 3.10, 3.11 e 3.12 do Python.

---

## 🗂️ Estrutura do repositório

```text
coffee-mail-sdk-python/
├── src/coffeemail/
│   ├── __init__.py          # exports públicos e __version__
│   ├── client.py            # CoffeeMail (síncrono)
│   ├── async_client.py      # AsyncCoffeeMail
│   ├── core/
│   │   ├── http.py          # transportes httpx, cabeçalhos, introspecção, SDK_VERSION
│   │   ├── errors.py        # hierarquia CoffeeMailError e mapeamento por status
│   │   ├── types.py         # CoffeeMailResponse e ApiKeyIntrospection
│   │   ├── parsing.py       # corpo → modelo; formato inválido vira INVALID_RESPONSE
│   │   ├── crypto.py        # verify_webhook_signature e sign_webhook
│   │   └── i18n.py          # mensagens pt-BR / en
│   ├── models/              # modelos Pydantic por recurso
│   ├── resources/           # emails, domains, templates, audiences, broadcasts,
│   │                        # senders, suppressions, webhooks, stats (sync + async)
│   └── py.typed
├── tests/                   # pytest; fixtures/webhook_vectors.json; test_contract.py
├── spec/product.json        # snapshot do OpenAPI de produto
├── scripts/                 # check_version_sync.py, sync_openapi.py
├── specs/                   # SPEC.md e SDD_ROADMAP.md (especificação de desenvolvimento)
├── .github/workflows/       # ci.yml, publish.yml
├── pyproject.toml
├── CHANGELOG.md
├── CONTRIBUTING.md
├── SECURITY.md
└── LICENSE
```

---

## 🤝 Contribuição

Leia o [CONTRIBUTING.md](https://github.com/Coffee-Mail/coffee-mail-sdk-python/blob/main/CONTRIBUTING.md). Em resumo: código em inglês e documentação, commits e PRs em pt-BR; sem comentários fora da documentação da API pública; sem `else`/`elif`, com retorno antecipado; sem valores mágicos; cada comportamento novo com testes do caminho feliz e de ao menos dois caminhos de erro; e todos os comandos de [Testes e qualidade](#-testes-e-qualidade) passando antes do PR. Mudanças na API pública começam por uma issue.

Vulnerabilidades: não abra issue pública; siga o [SECURITY.md](https://github.com/Coffee-Mail/coffee-mail-sdk-python/blob/main/SECURITY.md).

---

## 🔗 Projetos relacionados

| Repositório | Papel |
| --- | --- |
| [coffee-mail-sdk-node](https://github.com/Coffee-Mail/coffee-mail-sdk-node) | SDK oficial Node.js/TypeScript (`@coffeemail/node`) |
| **coffee-mail-sdk-python** (você está aqui) | SDK oficial Python (`coffeemail`) |
| [coffee-mail-sdk-php](https://github.com/Coffee-Mail/coffee-mail-sdk-php) | SDK oficial PHP (`coffeemail/coffeemail-php`) |
| [coffee-mail-sdk-java](https://github.com/Coffee-Mail/coffee-mail-sdk-java) | SDK oficial Java (`br.com.coffeemail:coffeemail-java`) |
| [coffee-mail-sdk-go](https://github.com/Coffee-Mail/coffee-mail-sdk-go) | SDK oficial Go (`github.com/Coffee-Mail/coffee-mail-sdk-go`) |
| [coffee-mail-sdk-ruby](https://github.com/Coffee-Mail/coffee-mail-sdk-ruby) | SDK oficial Ruby (`coffeemail`) |
| [coffee-mail-laravel](https://github.com/Coffee-Mail/coffee-mail-laravel) | Integração Laravel (mail driver + facade), `coffeemail/coffeemail-laravel` |
| [coffee-mail-sdk-workbench](https://github.com/Coffee-Mail/coffee-mail-sdk-workbench) | Bancada de validação dos SDKs por spec |

---

## 📄 Licença

Distribuído sob a licença [MIT](https://github.com/Coffee-Mail/coffee-mail-sdk-python/blob/main/LICENSE). Copyright (c) 2026 Dev-Etto.
