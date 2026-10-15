# Changelog

Todas as mudanças relevantes deste projeto são documentadas aqui. O formato segue o [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e o projeto adota o [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Não lançado]

## [0.2.0] - Não publicado

Correções de contrato com a API. Como o SDK ainda não tinha usuários ativos, esta versão corrige o comportamento diretamente, sem camada de depreciação: há quebras de compatibilidade, listadas em **Alterado** e **Removido**.

### Adicionado

- Teste de contrato: toda requisição do SDK é validada contra o OpenAPI de produto (`spec/product.json`), e o teste falha se alguma operação do spec ficar sem método. O snapshot é atualizado com `scripts/sync_openapi.py` (`COFFEEMAIL_OPENAPI_SPEC` aceita caminho local ou URL).
- Erros com `api_code` (código original da API), `request_id` (header `x-request-id`) e `details` reunindo `meta` e `details` do corpo de erro.
- `PaymentRequiredError` (402), `ForbiddenError` (403) e `RateLimitError.retry_after_seconds` (header `Retry-After`).
- `PermissionDeniedError` em toda operação de `broadcasts` quando a chave não tem `full_access`, com `required_permission` e `details["operation"]`.
- Resposta 2xx ilegível ou fora do formato esperado vira erro `INVALID_RESPONSE` no envelope, em vez de lançar exceção.
- `SendEmailPayload` ganha `email_type`, `suppression_category`, `metadata`, `idempotency_key` (header `X-Idempotency-Key`) e `sandbox` (header `X-Coffeemail-Sandbox`).
- `templates.preview_by_id`, e parâmetros completos do contrato em `templates.create`/`update` (`alias`, `preheader`, `content_json`, `text_payload`, `variables`, `format`, `source_locale`, `is_active`).
- Filtros do contrato em `emails.list`, `broadcasts.list`, `suppressions.list`, `webhooks.list` e `webhooks.list_deliveries`.
- Modelos tipados para respostas antes cruas: eventos e tags de email, saúde e aquecimento de domínio, envio/cancelamento/teste de campanha, entregas de webhook, criação em lote de supressões, entre outros.
- `sign_webhook`, para testar o próprio handler de webhook.
- Entrada malformada (destinatário, anexo, contatos e supressões em lote, variáveis de template) volta no envelope como `ValidationError` local (`code` `VALIDATION_ERROR`, `status_code` 0, mensagem em pt-BR ou en, `details["errors"]` com os campos), sem chamada de rede, nos clientes síncrono e assíncrono.
- Modelos tipados para remetentes: `SenderDetail`, `CreatedSender` (com `verification_token`), `ListSendersResponse` e `VerifySenderResult`.

### Alterado

- **Webhook:** `verify_webhook_signature` e `webhooks.verify_signature` usam o algoritmo da API: `sha256=` + HMAC-SHA256 de `timestamp.idempotencyKey.corpo`, janela de 300s configurável (`tolerance_seconds`), relógio injetável (`now`) e comparação exata em tempo constante. A assinatura passa a ser `verify_signature(payload, secret, *, headers=None, signature=None, timestamp=None, idempotency_key=None, ...)`; a chamada antiga `(payload, signature, secret)` lança `TypeError`.
- **Erros:** `code` passa a ser o código canônico, igual nos SDKs oficiais (`VALIDATION_ERROR`, `NOT_FOUND`...). O código da API está em `api_code`. 422 e outros status não mapeados viram `CoffeeMailError` com o código da API; só 500, 502, 503 e 504 viram `ServerError`.
- `PermissionDeniedError` passa a representar a falta de permissão de broadcasts (`PERMISSION_DENIED`); o 403 genérico é `ForbiddenError`, superclasse dela.
- Contatos usam `first_name`, `last_name` e `metadata` (keyword-only) em `create`, `update` e no lote (`ContactInput`).
- `broadcasts.create` recebe só argumentos nomeados e exige `audience_id` e `from_email`; aceita `subject`, `template_id`, `html`, `text`, `reply_to` e `variables`.
- `stats.get` usa `start_date`, `end_date`, `domain_id`, `tag`, `granularity`, `period` e `email_type` (keyword-only).
- `audiences.list` e `audiences.contacts.list` paginam por `limit`/`offset`.
- `suppressions.get`/`delete` recebem o id da supressão; um e-mail retorna `ValidationError` local (`status_code` 0), sem chamada de rede.
- `emails.send`/`send_batch` não lançam mais exceção com destinatário em formato não suportado; o erro volta no envelope. `senders.create` passa a ter `display_name` opcional.
- `webhooks.create` aceita `description` (o segredo é gerado pela API); `webhooks.update` usa `PUT` com `url`, `events` e `description`.
- `templates.preview`, `format` e `test_render` recebem `html` como argumento; `test_send` aceita `from_email` e `subject`.
- Modelos de resposta alinhados ao spec, com enums abertos (valores novos da API não quebram a validação): `EmailDetail.to` é lista, `BroadcastDetail`, `ContactDetail`, `BulkAddContactsResponse`, `SuppressionDetail`, `WebhookDetail` (`status` no lugar de `active`, que vira propriedade), `TemplateDetail`, `ListTemplatesResponse.data`, `DomainDetail`, `CreateDomainResponse.dkim_records_to_publish`, `DnsRecord`, `ApiKeyIntrospection` (`organisation_id`).
- `Content-Type` só é enviado em requisições com corpo; o cliente HTTP padrão não segue redirecionamentos.
- Mensagens locais com os textos canônicos dos SDKs oficiais.

### Removido

- `broadcasts.delete` (a API não tem a rota) e `suppressions.check` (use `get` com o id).
- Parâmetros fora do contrato: `name`, `subscribed` e `attributes` de contatos; `name` e `scheduled_at` de campanhas; `from_date`/`to_date` de `stats.get`; `after` em listas por offset; `limit`/`after` de `templates.list`; `secret` em `webhooks.create`; `description` e `text` em templates; `template_id` em `templates.preview`; `track_opens`/`track_clicks` em `SendEmailPayload`.
- `CheckSuppressionResponse` e os campos de modelo que a API não envia.

## [0.1.1] - 2026-10-08

Versão publicada no PyPI. O histórico anterior está nos commits e PRs.
