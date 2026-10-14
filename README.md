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

Classificador no PyPI: `Development Status :: 4 - Beta`. A série `0.x` ainda não tem garantia de estabilidade formal, mas a política de compatibilidade descrita em [Versionamento e releases](#-versionamento-e-releases) já vale.

### Versão publicada × `main`

A versão no PyPI é a **0.1.1** (publicada em 2026-10-08). A `main` continua declarando `0.1.1` em `pyproject.toml`, mas tem mudanças posteriores que **ainda não foram publicadas**:

| Mudança na `main` | Situação no PyPI 0.1.1 |
| --- | --- |
| Métodos `emails.get_events`, `emails.get_tags`, `emails.resend` | Ausentes |
| Métodos `domains.get_health`, `domains.get_warmup_status` | Ausentes |
| Métodos `templates.format`, `templates.test_render` | Ausentes |
| Métodos `audiences.update`, `audiences.update_contact`, `audiences.contacts.update` | Ausentes |
| Método `broadcasts.test_send` | Ausente |
| Recurso `senders` inteiro | Ausente |
| Métodos `suppressions.reactivate`, `suppressions.bulk_create` | Ausentes |
| Métodos `webhooks.list_deliveries`, `webhooks.toggle` | Ausentes |
| `emails.send_batch` envia um array e retorna `list[BatchSendEmailResult]` | Envia `{"items": [...]}` e tenta validar um único `BatchSendEmailResult` |
| Erros leem o envelope `{"error": {"message", "code", "details"}}` da API | Mensagem cai para `HTTP Error <status>` e `code` fica vazio |
| `broadcasts.delete` retorna `ValidationError` local, sem chamada de rede | Faz `DELETE /v1/product/broadcasts/{id}`, rota que não existe na API |
| `DomainDetail` expõe `status_reason`, `sending_identity` e `checks` | Campos ausentes |
| `__version__` e `User-Agent` reportam `0.1.1` | Reportam `0.1.0` |
| Parâmetro `base_url` removido: o SDK só fala com `https://api.coffeemail.com.br` | `base_url` existe e aceita qualquer host |

Na tabela de [Referência](#-referência), a coluna **PyPI 0.1.1** indica se o método já está no pacote publicado.

### Limitações conhecidas

- **Verificação de webhook incompatível com a API.** `verify_signature` calcula `hex(HMAC-SHA256(secret, corpo))`. A API assina `sha256=` + `hex(HMAC-SHA256(secret, "<timestamp>.<idempotencyKey>.<corpo>"))` e envia os cabeçalhos `x-webhook-signature`, `x-webhook-timestamp` e `x-webhook-idempotency-key`. Com entregas reais, o método retorna `False`. Veja [Webhooks](#-webhooks) para a verificação correta.
- **Payloads fora do contrato da API** (spec OpenAPI da API de produto). Os métodos abaixo enviam campos que a API não conhece ou omitem campos obrigatórios:

  | Método | O SDK envia | O contrato espera |
  | --- | --- | --- |
  | `audiences.create_contact` / `audiences.contacts.create` | `email`, `name`, `subscribed`, `attributes` | `email`, `firstName`, `lastName`, `metadata` |
  | `broadcasts.create` | `name`, `subject`, `audienceId`, `scheduledAt`, sem `fromEmail` | `audienceId` e `fromEmail` obrigatórios; `templateId` ou `html`, `subject`, `text`, `replyTo`, `variables` |
  | `stats.get` | query `from` / `to` | `startDate` / `endDate` (e `domainId`, `tag`, `granularity`, `period`, `emailType`) |
  | `audiences.list` / `audiences.contacts.list` | query `after` | `limit` / `offset` |
  | `templates.list` | query `limit` / `after` | sem parâmetros de query |
  | `templates.create` / `templates.update` | `description`, `text` | sem `description`; texto em `textPayload` |
  | `templates.preview` | `templateId` opcional, `html` opcional | `html` obrigatório |
  | `suppressions.check` / `suppressions.delete` | e-mail no path | id da supressão no path |
  | `webhooks.create` | `secret` | `url`, `events`, `description` (o segredo é gerado pela API) |
  | `webhooks.update` | `PATCH` com `url` / `events` | `PUT` para `url` / `events`; `PATCH` aceita só `status` |
  | `domains.delete` | sem corpo | corpo com `method` e `credential` |
  | `SendEmailPayload` | `trackOpens` / `trackClicks` | campos inexistentes em `POST /v1/product/emails` |

- **Tipagem do desempacotamento.** `data, error = resposta` funciona em runtime, mas `__iter__` é tipado como `Iterator[object | None]`: sob mypy, `data` vira `object | None`. Para acesso tipado, use `resposta.data` (após checar `None`) ou `.unwrap()`.
- **Respostas sem modelo.** Vários métodos retornam `dict[str, object]` cru: `emails.cancel`, `get_events`, `get_tags`, `resend`; `domains.delete`, `get_health`, `get_warmup_status`; `templates.delete`, `test_send`, `format`, `test_render`; `audiences.delete`, `update`, `update_contact`; `broadcasts.send`, `cancel`, `test_send`; todo o recurso `senders`; `suppressions.delete`, `reactivate`, `bulk_create`; `webhooks.delete`, `list_deliveries`, `toggle`.
- **Sem retry automático.** Não há nova tentativa nem leitura de `Retry-After` em `429` ou `5xx`; o erro chega no envelope e a política de retry é sua.
- **Sem `close()` nem context manager** nos clientes. Para controlar o ciclo de vida da conexão, passe seu próprio `httpx.Client` / `httpx.AsyncClient` em `http_client` e feche-o você mesmo.
- **`x-request-id` e `error.meta` não são expostos** no erro.
- **Dois pontos lançam exceção em vez de usar o envelope:** o construtor lança `AuthenticationError` sem `api_key` e sem `COFFEEMAIL_API_KEY`; `emails.send`/`send_batch` lançam `ValidationError` com destinatário em formato não suportado.

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

Cabeçalhos enviados em toda requisição: `Authorization`, `Content-Type: application/json`, `Accept: application/json`, `Accept-Language` e `User-Agent: coffeemail-python/<versão>`.

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
| `status_code` | `int \| None` | Status HTTP; `None` em erro de rede ou validação local. |
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

Todas herdam de `CoffeeMailError` e são exportadas por `coffeemail`. Cada erro tem `message`, `status_code`, `code` (o código enviado pela API, quando houver) e `details` (dicionário; vazio quando a API não envia).

| Classe | Status HTTP | Quando ocorre |
| --- | --- | --- |
| `AuthenticationError` | `401` | Chave inválida, revogada ou expirada. Também lançada no construtor quando não há chave. |
| `PermissionDeniedError` | `403` | A chave não tem escopo ou permissão para a operação. |
| `NotFoundError` | `404` | Recurso inexistente ou de outra organização. |
| `ValidationError` | `400`, `422` | Corpo ou parâmetros rejeitados pela API. Também usada localmente, com `status_code=None`: retornada no envelope por `broadcasts.delete` (na `main`) e **lançada** por `emails.send`/`send_batch` quando um destinatário não é string, `EmailParticipant` nem dicionário com `email`. |
| `ConflictError` | `409` | Conflito de estado (ex.: recurso duplicado). |
| `RateLimitError` | `429` | Limite de requisições excedido. Sem retry automático. |
| `ServerError` | `>=500` | Falha do lado da API. |
| `NetworkError` | — | Timeout ou falha de conexão (`httpx.TimeoutException` / `httpx.RequestError`). `details["original_error"]` traz a mensagem original. |
| `CoffeeMailError` | outros `4xx` | Qualquer status não mapeado acima. |

---

## 📚 Referência

Os caminhos abaixo são relativos a `https://api.coffeemail.com.br`. Todos os recursos existem nos dois clientes; no `AsyncCoffeeMail` os métodos são `async`, exceto `webhooks.verify_signature` e `invalidate_introspection_cache`. A coluna **PyPI 0.1.1** indica se o método já está no pacote publicado (veja [Status do projeto](#-status-do-projeto)).

### Introspecção

| Método | Retorno | Endpoint | PyPI 0.1.1 |
| --- | --- | --- | --- |
| `client.introspect(force_refresh=False)` | `ApiKeyIntrospection` | `GET /v1/product/auth/me/api-key` | sim |
| `client.invalidate_introspection_cache()` | `None` | — | sim |

O resultado fica em cache por 300 segundos por instância de cliente. `ApiKeyIntrospection` tem `id`, `name`, `environment`, `scopes`, `rate_limit`, `created_at` e `expires_at`.

```python
info = client.introspect().unwrap()
print(info.environment, info.scopes)
```

### Emails — `client.emails`

| Método | Retorno | Endpoint | PyPI 0.1.1 |
| --- | --- | --- | --- |
| `send(payload: SendEmailPayload \| dict)` | `SendEmailResponse` | `POST /v1/product/emails` | sim |
| `send_batch(emails: list[SendEmailPayload \| dict])` | `list[BatchSendEmailResult]` | `POST /v1/product/emails/batch` | comportamento diferente |
| `get(email_id)` | `EmailDetail` | `GET /v1/product/emails/{id}` | sim |
| `list(limit=None, after=None, status=None)` | `ListEmailsResponse` | `GET /v1/product/emails` | sim |
| `cancel(email_id)` | `dict` | `POST /v1/product/emails/{id}/cancel` | sim |
| `get_events(email_id)` | `dict` | `GET /v1/product/emails/{id}/events` | não |
| `get_tags()` | `dict` | `GET /v1/product/emails/tags` | não |
| `resend(email_id)` | `dict` | `POST /v1/product/emails/{id}/resend` | não |

Campos aceitos em `send`: `from`, `to`, `subject`, `html`, `text`, `cc`, `bcc`, `replyTo` (ou `reply_to`), `headers`, `attachments`, `tags`, `templateId`, `variables`, `scheduledAt`. Anexos (`EmailAttachment` ou dicionário com `filename`, `content`, `contentType`, `disposition`, `cid`) aceitam em `content` bytes (codificados em base64 pelo SDK), o caminho de um arquivo existente (lido e codificado) ou uma string já em base64. Cada item de `send_batch` é `BatchSendEmailItemSuccess` (`ok=True`, `data`) ou `BatchSendEmailItemFailure` (`ok=False`, `error`).

```python
from coffeemail import EmailAttachment

response = client.emails.send(
    {
        "from": "contato@seudominio.com.br",
        "to": "cliente@exemplo.com.br",
        "subject": "Seu relatório",
        "text": "Segue o relatório em anexo.",
        "attachments": [EmailAttachment(filename="relatorio.pdf", content=b"%PDF-1.7 ...")],
    }
)

page = client.emails.list(limit=20, status="delivered").unwrap()
for email in page.emails:
    print(email.id, email.status)
```

### Domains — `client.domains`

| Método | Retorno | Endpoint | PyPI 0.1.1 |
| --- | --- | --- | --- |
| `list()` | `ListDomainsResponse` | `GET /v1/product/domains` | sim |
| `get(domain_id)` | `DomainDetail` | `GET /v1/product/domains/{id}` | sim |
| `create(name)` | `CreateDomainResponse` | `POST /v1/product/domains` | sim |
| `verify(domain_id)` | `DomainDetail` | `POST /v1/product/domains/{id}/verify` | sim |
| `delete(domain_id)` | `dict` | `DELETE /v1/product/domains/{id}` | sim |
| `get_health(domain_id)` | `dict` | `POST /v1/product/domains/{id}/health` | não |
| `get_warmup_status(domain_id)` | `dict` | `GET /v1/product/domains/{id}/warmup` | não |

`DomainDetail.status` é `pending`, `verified`, `failed` ou `temporary_failure`; na `main`, `status_reason` explica o motivo (`dns_records_missing`, `provider_pending`, `provider_failed`) e `checks` traz o resultado por registro DNS.

```python
created = client.domains.create("seudominio.com.br").unwrap()
for record in created.dns_records:
    print(record.record_type, record.name, record.value)

domain = client.domains.verify(created.id).unwrap()
print(domain.status)
```

### Templates — `client.templates`

| Método | Retorno | Endpoint | PyPI 0.1.1 |
| --- | --- | --- | --- |
| `list(limit=None, after=None)` | `ListTemplatesResponse` | `GET /v1/product/templates` | sim |
| `get(template_id)` | `TemplateDetail` | `GET /v1/product/templates/{id}` | sim |
| `create(name, html, subject=None, description=None, text=None)` | `TemplateDetail` | `POST /v1/product/templates` | sim |
| `update(template_id, name=None, html=None, subject=None, description=None, text=None)` | `TemplateDetail` | `PATCH /v1/product/templates/{id}` | sim |
| `delete(template_id)` | `dict` | `DELETE /v1/product/templates/{id}` | sim |
| `preview(html=None, template_id=None, variables=None)` | `PreviewTemplateResponse` | `POST /v1/product/templates/preview` | sim |
| `test_send(template_id, to, variables=None)` | `dict` | `POST /v1/product/templates/{id}/test-send` | sim |
| `format(payload: dict)` | `dict` | `POST /v1/product/templates/format` | não |
| `test_render(payload: dict)` | `dict` | `POST /v1/product/templates/test-render` | não |

```python
template = client.templates.create(
    name="boas-vindas",
    subject="Olá, {{nome}}",
    html="<p>Olá, {{nome}}!</p>",
).unwrap()

preview = client.templates.preview(html=template.html, variables={"nome": "Ana"}).unwrap()
print(preview.html)
```

### Audiences — `client.audiences`

| Método | Retorno | Endpoint | PyPI 0.1.1 |
| --- | --- | --- | --- |
| `list(limit=None, after=None)` | `ListAudiencesResponse` | `GET /v1/product/audiences` | sim |
| `get(audience_id)` | `AudienceDetail` | `GET /v1/product/audiences/{id}` | sim |
| `create(name, description=None)` | `AudienceDetail` | `POST /v1/product/audiences` | sim |
| `update(audience_id, payload: dict)` | `dict` | `PUT /v1/product/audiences/{id}` | não |
| `delete(audience_id)` | `dict` | `DELETE /v1/product/audiences/{id}` | sim |
| `list_contacts(audience_id, limit=None, after=None)` | `ListContactsResponse` | `GET /v1/product/audiences/{id}/contacts` | sim |
| `create_contact(audience_id, email, name=None, subscribed=True, attributes=None)` | `ContactDetail` | `POST /v1/product/audiences/{id}/contacts` | sim |
| `bulk_add_contacts(audience_id, contacts: list[dict])` | `BulkAddContactsResponse` | `POST /v1/product/audiences/{id}/contacts/bulk` | sim |
| `update_contact(audience_id, contact_id, payload: dict)` | `dict` | `PUT /v1/product/audiences/{id}/contacts/{contactId}` | não |

### Contacts — `client.audiences.contacts`

| Método | Retorno | Endpoint | PyPI 0.1.1 |
| --- | --- | --- | --- |
| `list(audience_id, limit=None, after=None)` | `ListContactsResponse` | `GET /v1/product/audiences/{id}/contacts` | sim |
| `create(audience_id, email, name=None, subscribed=True, attributes=None)` | `ContactDetail` | `POST /v1/product/audiences/{id}/contacts` | sim |
| `bulk_add(audience_id, contacts: list[dict])` | `BulkAddContactsResponse` | `POST /v1/product/audiences/{id}/contacts/bulk` | sim |
| `update(audience_id, contact_id, payload: dict)` | `dict` | `PUT /v1/product/audiences/{id}/contacts/{contactId}` | não |
| `delete(audience_id, contact_id)` | `dict` | `DELETE /v1/product/audiences/{id}/contacts/{contactId}` | sim |

Os métodos `*_contact(s)` de `client.audiences` delegam para `client.audiences.contacts`. Veja em [Limitações conhecidas](#limitações-conhecidas) a divergência do corpo de criação de contato.

```python
audience = client.audiences.create("Clientes ativos").unwrap()
result = client.audiences.contacts.bulk_add(
    audience.id,
    [{"email": "ana@exemplo.com.br"}, {"email": "bruno@exemplo.com.br"}],
).unwrap()
print(result.inserted, result.updated, result.failed)
```

### Broadcasts — `client.broadcasts`

| Método | Retorno | Endpoint | PyPI 0.1.1 |
| --- | --- | --- | --- |
| `list(limit=None, after=None)` | `ListBroadcastsResponse` | `GET /v1/product/broadcasts` | sim |
| `get(broadcast_id)` | `BroadcastDetail` | `GET /v1/product/broadcasts/{id}` | sim |
| `create(name, subject, audience_id, template_id=None, html=None, text=None, scheduled_at=None)` | `BroadcastDetail` | `POST /v1/product/broadcasts` | sim |
| `send(broadcast_id)` | `dict` | `POST /v1/product/broadcasts/{id}/send` | sim |
| `cancel(broadcast_id)` | `dict` | `POST /v1/product/broadcasts/{id}/cancel` | sim |
| `test_send(broadcast_id, payload: dict)` | `dict` | `POST /v1/product/broadcasts/{id}/test-send` | não |
| `delete(broadcast_id)` | `dict` | — (não suportado pela API; na `main` retorna `ValidationError` local) | sim, mas chama rota inexistente |

`BroadcastDetail.status` é `draft`, `scheduled`, `sending`, `completed` ou `cancelled`. `broadcasts.create` não envia `fromEmail`, exigido pela API (veja [Limitações conhecidas](#limitações-conhecidas)).

```python
broadcast = client.broadcasts.get("brd_123").unwrap()
if broadcast.status == "scheduled":
    client.broadcasts.cancel(broadcast.id)
```

### Senders — `client.senders`

Só na `main` (ausente no PyPI 0.1.1).

| Método | Retorno | Endpoint | PyPI 0.1.1 |
| --- | --- | --- | --- |
| `create(email, display_name)` | `dict` | `POST /v1/product/senders` | não |
| `list()` | `dict` | `GET /v1/product/senders` | não |
| `verify(token)` | `dict` | `POST /v1/product/senders/verify` | não |
| `delete(sender_id)` | `dict` | `DELETE /v1/product/senders/{id}` | não |

```python
client.senders.create("contato@seudominio.com.br", "Equipe Acme")
```

### Suppressions — `client.suppressions`

| Método | Retorno | Endpoint | PyPI 0.1.1 |
| --- | --- | --- | --- |
| `list(limit=None, after=None)` | `ListSuppressionsResponse` | `GET /v1/product/suppressions` | sim |
| `check(email)` | `CheckSuppressionResponse` | `GET /v1/product/suppressions/{email}` | sim |
| `create(email, reason="manual")` | `SuppressionDetail` | `POST /v1/product/suppressions` | sim |
| `delete(email)` | `dict` | `DELETE /v1/product/suppressions/{email}` | sim |
| `reactivate(suppression_id)` | `dict` | `POST /v1/product/suppressions/{id}/reactivate` | não |
| `bulk_create(suppressions: list[dict])` | `dict` | `POST /v1/product/suppressions/bulk` | não |

`reason` aceita `bounce`, `complaint`, `unsubscribe` ou `manual`. A API identifica supressões por id no path; `check` e `delete` enviam o e-mail (veja [Limitações conhecidas](#limitações-conhecidas)).

```python
suppression = client.suppressions.create("nao-quero@exemplo.com.br", reason="unsubscribe").unwrap()
print(suppression.id, suppression.reason)
```

### Webhooks — `client.webhooks`

| Método | Retorno | Endpoint | PyPI 0.1.1 |
| --- | --- | --- | --- |
| `list()` | `ListWebhooksResponse` | `GET /v1/product/webhooks` | sim |
| `get(webhook_id)` | `WebhookDetail` | `GET /v1/product/webhooks/{id}` | sim |
| `create(url, events: list[str], secret=None)` | `CreatedWebhookDetail` | `POST /v1/product/webhooks` | sim |
| `update(webhook_id, url=None, events=None)` | `WebhookDetail` | `PATCH /v1/product/webhooks/{id}` | sim |
| `delete(webhook_id)` | `dict` | `DELETE /v1/product/webhooks/{id}` | sim |
| `rotate_secret(webhook_id)` | `RotateWebhookSecretResult` | `POST /v1/product/webhooks/{id}/rotate-secret` | sim |
| `test(webhook_id)` | `TestWebhookResult` | `POST /v1/product/webhooks/{id}/test` | sim |
| `list_deliveries(webhook_id)` | `dict` | `GET /v1/product/webhooks/{id}/deliveries` | não |
| `toggle(webhook_id, enabled: bool)` | `dict` | `PATCH /v1/product/webhooks/{id}` com `status` `active`/`paused` | não |
| `verify_signature(payload, signature, secret)` (estático) | `bool` | — | sim |

Eventos tipados em `WebhookEvent`: `email.queued`, `email.sent`, `email.delivered`, `email.bounced`, `email.complained`, `email.clicked`, `email.opened`, `email.failed`. O segredo (`secret`) só aparece em `CreatedWebhookDetail` e `RotateWebhookSecretResult`; guarde-o na hora.

```python
webhook = client.webhooks.create(
    "https://seuapp.com.br/webhooks/coffeemail",
    ["email.delivered", "email.bounced"],
).unwrap()
print(webhook.id, webhook.secret)
```

### Stats — `client.stats`

| Método | Retorno | Endpoint | PyPI 0.1.1 |
| --- | --- | --- | --- |
| `get(from_date=None, to_date=None)` | `EmailStats` | `GET /v1/product/stats` | sim |

`EmailStats` traz `total_sent`, `total_delivered`, `total_bounced`, `total_complained`, `total_opened`, `total_clicked`, `delivery_rate`, `bounce_rate`, `open_rate` e `click_rate`. Os filtros de data são enviados como `from`/`to`, que a API não reconhece (veja [Limitações conhecidas](#limitações-conhecidas)).

```python
stats = client.stats.get().unwrap()
print(f"Entregues: {stats.total_delivered} ({stats.delivery_rate:.1%})")
```

### Modelos e tipos exportados

`coffeemail` exporta os clientes, `CoffeeMailResponse`, `ApiKeyIntrospection`, as classes de erro e os modelos: `SendEmailPayload`, `SendEmailResponse`, `BatchSendEmailResult`, `EmailDetail`, `EmailParticipant`, `EmailAttachment`, `EmailTag`, `EmailStatus`, `ListEmailsResponse`, `DomainDetail`, `CreateDomainResponse`, `DnsRecord`, `DomainStatus`, `ListDomainsResponse`, `TemplateDetail`, `ListTemplatesResponse`, `PreviewTemplateResponse`, `AudienceDetail`, `ContactDetail`, `ListAudiencesResponse`, `ListContactsResponse`, `BulkAddContactsResponse`, `BroadcastDetail`, `BroadcastStatus`, `ListBroadcastsResponse`, `SuppressionDetail`, `SuppressionReason`, `CheckSuppressionResponse`, `ListSuppressionsResponse`, `WebhookDetail`, `CreatedWebhookDetail`, `ListWebhooksResponse`, `RotateWebhookSecretResult`, `TestWebhookResult`, `WebhookEvent` e `EmailStats`. Na `main`, também `DomainStatusReason`, `DomainDnsCheck`, `DnsResolution` e `SendingIdentity`.

---

## 🔔 Webhooks

### Como a API assina as entregas

Cada entrega é um `POST` com corpo JSON e estes cabeçalhos:

| Cabeçalho | Conteúdo |
| --- | --- |
| `x-webhook-signature` | `sha256=` + HMAC-SHA256 em hex de `"<timestamp>.<idempotencyKey>.<corpo>"`, com o segredo `whsec_...` do webhook |
| `x-webhook-timestamp` | Epoch em segundos; a API usa janela de 300 segundos |
| `x-webhook-idempotency-key` | Chave aleatória por entrega; use-a também para deduplicar |
| `x-webhook-test` | `true` em entregas disparadas por `webhooks.test()` |

### `verify_signature` do SDK

`Webhooks.verify_signature(payload, signature, secret)` (também acessível como `client.webhooks.verify_signature`) compara `hex(HMAC-SHA256(secret, payload))` em tempo constante. Ele **não** considera o prefixo `sha256=`, o timestamp nem a chave de idempotência, então retorna `False` para entregas reais da API. Ele continua no pacote por compatibilidade, mas não o use para validar entregas.

### Verificação compatível com a API

Até o SDK ganhar um verificador alinhado, valide com a biblioteca padrão, usando o **corpo bruto** da requisição:

```python
import hashlib
import hmac
import time
from collections.abc import Mapping

TOLERANCE_SECONDS = 300


def verify_coffeemail_webhook(body: bytes, headers: Mapping[str, str], secret: str) -> bool:
    signature = headers.get("x-webhook-signature", "")
    timestamp = headers.get("x-webhook-timestamp", "")
    idempotency_key = headers.get("x-webhook-idempotency-key", "")
    if not signature or not timestamp.isdigit() or not idempotency_key:
        return False
    if abs(time.time() - int(timestamp)) > TOLERANCE_SECONDS:
        return False
    signed_payload = f"{timestamp}.{idempotency_key}.".encode() + body
    digest = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={digest}", signature)
```

Em frameworks como FastAPI e Starlette, `request.headers` já ignora maiúsculas/minúsculas; com um `dict` comum, normalize as chaves para minúsculas antes.

---

## 🔖 Versionamento e releases

- **SemVer.** A versão fica em três lugares que precisam bater: `pyproject.toml`, `__version__` em `src/coffeemail/__init__.py` e `SDK_VERSION` em `src/coffeemail/core/http.py` (usado no `User-Agent`). `scripts/check_version_sync.py` falha a CI se divergirem.
- **Compatibilidade retroativa.** O pacote está publicado e em uso. Mudanças na superfície pública **adicionam e depreciam; nunca renomeiam nem removem** métodos, parâmetros, modelos ou campos. Correções de contrato entram como novos parâmetros ou métodos, com o comportamento antigo mantido e marcado como depreciado. Os SDKs oficiais (Node.js, Python, PHP, Java e Go) mantêm o mesmo contrato.
- **Publicação.** O workflow [`publish.yml`](https://github.com/Coffee-Mail/coffee-mail-sdk-python/blob/main/.github/workflows/publish.yml) roda em push na `main` e em tags `v*`: executa ruff, mypy e pytest, consulta o PyPI e só constrói e publica se a versão do `pyproject.toml` ainda não existir lá. Para lançar, suba a versão nos três lugares acima e faça merge na `main`.
- **CHANGELOG.** O repositório ainda não tem `CHANGELOG.md`; o histórico está nos commits e PRs.

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
| `uv sync --extra dev` | Instala dependências de runtime e de dev (`mypy`, `pytest`, `pytest-asyncio`, `pytest-mock`, `respx`, `ruff`). |
| `uv run ruff format --check .` | Formatação (linha de 100 colunas). |
| `uv run ruff check .` | Lint: pycodestyle, pyflakes, isort, bugbear, comprehensions, pyupgrade, unused-arguments, simplify, type-checking e `RET` (sem `else` após `return`). |
| `uv run mypy src tests` | Tipagem `strict` com o plugin do Pydantic. |
| `uv run python scripts/check_version_sync.py` | Versões sincronizadas entre `pyproject.toml`, `__init__.py` e `core/http.py`. |
| `uv run pytest -v` | Suíte em `tests/` (HTTP simulado com `respx`, `asyncio_mode = "auto"`). |
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
│   │   ├── crypto.py        # verify_webhook_signature
│   │   └── i18n.py          # mensagens pt-BR / en
│   ├── models/              # modelos Pydantic por recurso
│   ├── resources/           # emails, domains, templates, audiences, broadcasts,
│   │                        # senders, suppressions, webhooks, stats (sync + async)
│   └── py.typed
├── tests/                   # pytest + respx
├── scripts/check_version_sync.py
├── specs/                   # SPEC.md e SDD_ROADMAP.md (especificação de desenvolvimento)
├── .github/workflows/       # ci.yml, publish.yml
├── pyproject.toml
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
| [coffee-mail-laravel](https://github.com/Coffee-Mail/coffee-mail-laravel) | Integração Laravel (mail driver + facade), `coffeemail/coffeemail-laravel` |
| [coffee-mail-sdk-workbench](https://github.com/Coffee-Mail/coffee-mail-sdk-workbench) | Bancada de validação dos SDKs por spec |

---

## 📄 Licença

Distribuído sob a licença [MIT](https://github.com/Coffee-Mail/coffee-mail-sdk-python/blob/main/LICENSE). Copyright (c) 2026 Dev-Etto.
