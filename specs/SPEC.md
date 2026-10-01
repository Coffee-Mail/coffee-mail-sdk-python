# Especificação Técnica de Desenvolvimento (SDD): CoffeeMail Python SDK (`coffeemail`)

- **Pacote**: `coffeemail`
- **Repositório**: `coffee-mail-sdk-python`
- **Versão Alvo Inicial**: `0.1.0`
- **Metodologia**: Spec-Driven Development (SDD)
- **Alinhamento**: Paridade funcional com `@coffeemail/node` (v0.2.0) e Runner Specification API

---

## 1. Visão Geral e Objetivos de DX

O **CoffeeMail Python SDK** tem como meta fornecer uma biblioteca de alta performance, tipada estritamente e ergonômica para desenvolvedores Python, atendendo desde aplicações tradicionais síncronas (Django, Flask, scripts) até ecossistemas modernos assíncronos (FastAPI, Starlette, Celery, Temporal).

### Pilares de Developer Experience (DX):
1. **Dualidade Síncrona e Assíncrona**:
   - `CoffeeMail`: Cliente síncrono padrão baseado em `httpx.Client`.
   - `AsyncCoffeeMail`: Cliente assíncrono nativo baseado em `httpx.AsyncClient`.
2. **Envelope Previsível com Desempacotamento Amigável**:
   - Respostas encapsuladas em `CoffeeMailResponse[T]`.
   - Acesso seguro via atributos `res.data` e `res.error`, além de suporte a desempacotamento de tupla `data, error = client.emails.send(...)` e método de conveniência `res.unwrap()`.
3. **Tipagem Estrita e Modelos Pydantic v2**:
   - PEP 561 compliance com arquivo marcador `py.typed`.
   - Modelagem de dados com Pydantic v2 garantindo auto-complete total em VS Code / PyCharm / Cursor.
   - Conversão transparente entre convenções: código Python usa `snake_case` e a API recebe/emite `camelCase`.
4. **Resiliência e Tratamento de Erros Semântico**:
   - Hierarquia clara de exceções herdando de `CoffeeMailError` (`AuthenticationError`, `ValidationError`, `NotFoundError`, `RateLimitError`, `NetworkError`).
   - Validações locais antecipadas para evitar viagens de rede desnecessárias (ex: API key ausente, e-mail mal formatado).
5. **Utilitários de Segurança**:
   - Módulo criptográfico `webhooks.verify_signature(payload, signature, secret, tolerance)` utilizando HMAC-SHA256 em tempo constante (`hmac.compare_digest`).

---

## 2. Arquitetura da Solução

O SDK é estruturado em camadas independentes e modulares:

```text
coffee-mail-sdk-python/
├── specs/                          # Especificações SDD e Roadmap
│   ├── SPEC.md                     # Especificação técnica dos módulos e contratos
│   └── SDD_ROADMAP.md              # Planejamento das fases de implementação
├── src/
│   └── coffeemail/
│       ├── __init__.py             # Exportações públicas (CoffeeMail, AsyncCoffeeMail, erros, DTOs)
│       ├── py.typed                # Marcador PEP 561 para type checkers
│       ├── client.py               # Cliente síncrono principal
│       ├── async_client.py         # Cliente assíncrono principal
│       ├── core/                   # Núcleo de infraestrutura e utilidades
│       │   ├── __init__.py
│       │   ├── http.py             # Adaptadores de transporte HTTP síncrono/assíncrono
│       │   ├── errors.py           # Hierarquia de exceções customizadas
│       │   ├── types.py            # Envelopes de resposta genéricos e tipos base
│       │   ├── i18n.py             # Mensagens localizadas (pt-BR e en)
│       │   └── crypto.py           # Validação de assinaturas HMAC de Webhooks
│       ├── models/                 # Schemas e DTOs Pydantic v2
│       │   ├── __init__.py
│       │   ├── emails.py
│       │   ├── domains.py
│       │   ├── templates.py
│       │   ├── audiences.py
│       │   ├── broadcasts.py
│       │   ├── suppressions.py
│       │   ├── webhooks.py
│       │   └── stats.py
│       └── resources/              # Classes de serviço por recurso da API
│           ├── __init__.py
│           ├── emails.py
│           ├── domains.py
│           ├── templates.py
│           ├── audiences.py
│           ├── broadcasts.py
│           ├── suppressions.py
│           ├── webhooks.py
│           └── stats.py
├── tests/                          # Suíte de testes com pytest e respx
│   ├── conftest.py
│   ├── test_client.py
│   ├── test_emails.py
│   ├── test_domains.py
│   ├── test_webhooks.py
│   └── test_async_client.py
├── pyproject.toml
└── README.md
```

---

## 3. Matriz de Paridade de Recursos com `@coffeemail/node`

| Recurso | Métodos Planejados | Assinatura Resumida |
| :--- | :--- | :--- |
| **Auth / Introspect** | `introspect(force_refresh=False)` | Retorna `ApiKeyIntrospection` com escopos e ambiente. |
| **Emails** | `send()`, `send_batch()`, `get()`, `list()`, `cancel()`, `get_events()`, `list_tags()` | Suporte a strings, listas, dicts, anexos binários/base64/caminho. |
| **Domains** | `list()`, `get()`, `create()`, `verify()`, `get_health()`, `delete()` | Validação DNS completa (SPF, DKIM, DMARC). |
| **Templates** | `list()`, `get()`, `create()`, `update()`, `delete()`, `preview()`, `test_send()` | Renderização por ID ou HTML bruto. |
| **Audiences** | `list()`, `get()`, `create()`, `update()`, `delete()` + atalhos de contatos | Gestão de listas de destinatários. |
| **Contacts** | `list()`, `create()`, `bulk_add()`, `delete()` | Integrado em `audiences.contacts` e atalhos na raiz de `audiences`. |
| **Broadcasts** | `list()`, `get()`, `create()`, `send()`, `cancel()`, `delete()` | Disparos em massa. |
| **Suppressions** | `list()`, `check()`, `create()`, `delete()` | Gestão de bloqueios (bounces/unsubscribes). |
| **Webhooks** | `list()`, `get()`, `create()`, `update()`, `toggle()`, `rotate_secret()`, `test()`, `list_deliveries()` | Gestão de endpoints e validação de assinatura `verify_signature`. |
| **Stats** | `get()` | Agregação temporal por período (`from_date`, `to_date`). |

---

## 4. Contrato do Envelope de Resposta (`CoffeeMailResponse`)

Para entregar ergonomia superior em Python, `CoffeeMailResponse` implementará:

```python
from typing import Generic, TypeVar, Optional, Tuple

T = TypeVar("T")


class CoffeeMailResponse(Generic[T]):
    data: Optional[T]
    error: Optional[CoffeeMailError]

    def __iter__(self) -> Tuple[Optional[T], Optional[CoffeeMailError]]:
        """Permite desempacotamento direto: data, error = client.emails.send(...)"""
        yield self.data
        yield self.error

    def unwrap(self) -> T:
        """Retorna os dados ou lança a exceção caso error esteja preenchido."""
        if self.error is not None:
            raise self.error
        if self.data is None:
            raise ValueError("Resposta sem dados disponíveis.")
        return self.data
```

---

## 5. Padrões de Qualidade e Segurança

1. **Sem Segredos em Código**: Resolução de chave prioritária via parâmetro do construtor, com fallback para `COFFEEMAIL_API_KEY`.
2. **User-Agent Identificador**: Header `User-Agent: coffeemail-python/{version}` em todas as requisições.
3. **Resolução de Timeout Padrão**: 10 segundos configuráveis (`timeout=10.0`).
4. **Verificação de Webhook Imune a Timing Attacks**: Validação HMAC através de `hmac.compare_digest`.
5. **Traduções / i18n**: Suporte a mensagens de erro em `pt-BR` (padrão) e `en`.
