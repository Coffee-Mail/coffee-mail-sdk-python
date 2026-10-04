<div align="center">

# coffeemail (Python SDK)

**SDK oficial da CoffeeMail para Python — Síncrono e Assíncrono com tipagem estrita**

[![PyPI version](https://img.shields.io/pypi/v/coffeemail?style=flat-square&color=3178C6)](https://pypi.org/project/coffeemail/)
[![Python versions](https://img.shields.io/pypi/pyversions/coffeemail?style=flat-square&color=3776AB)](https://pypi.org/project/coffeemail/)
[![Type Checked](https://img.shields.io/badge/mypy-strict-blue?style=flat-square)](https://mypy-lang.org/)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2-E92063?style=flat-square&logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](./LICENSE)

[Instalação](#-instalação) · [Início Rápido](#-início-rápido) · [Modo Assíncrono](#-envio-assíncrono-fastapi--celery) · [Recursos Suportados](#-recursos-disponíveis) · [Validação de Webhooks](#-validação-criptográfica-de-webhooks)

</div>

---

## ✨ Visão Geral

O pacote `coffeemail` é a biblioteca cliente oficial da **CoffeeMail** para desenvolvedores Python. Oferece suporte completo e fortemente tipado a todas as operações da API de Produto:

- **Dualidade Síncrona e Assíncrona**: Classes dedicadas `CoffeeMail` (síncrona) e `AsyncCoffeeMail` (assíncrona) baseadas em HTTPX.
- **Validação com Pydantic v2**: Modelos estritos de entrada e saída, compatíveis com PEP 561 (`py.typed`).
- **Retorno Seguro `{ data, error }`**: Suporte nativo a desempacotamento de tuplas e ao método `.unwrap()`.
- **Introspecção Automática**: Verificação de validade de API Key, ambiente e escopos com cache em memória.
- **Localização em Português**: Mensagens de erro locais e cabeçalho `Accept-Language: pt-BR` por padrão.

---

## 📦 Instalação

```bash
# via uv (recomendado)
uv add coffeemail

# via pip
pip install coffeemail

# via poetry
poetry add coffeemail
```

---

## 🚀 Início Rápido

### Envio Transacional Síncrono (Django, Flask, Scripts)

```python
from coffeemail import CoffeeMail

# Instancie o cliente (lê automaticamente COFFEEMAIL_API_KEY do ambiente se omitida)
client = CoffeeMail("cm_live_sua_chave_aqui")

# Desempacotamento de tupla (data, error)
data, error = client.emails.send(
    {
        "from": "contato@seudominio.com.br",
        "to": "cliente@exemplo.com.br",
        "subject": "Boas-vindas à nossa plataforma!",
        "html": "<h1>Olá!</h1><p>Seu cadastro foi realizado com sucesso.</p>",
    }
)

if error:
    print(f"Falha no envio [{error.code}]: {error.message}")
else:
    print(f"E-mail enfileirado com sucesso! ID: {data.id}")
```

---

## ⚡ Envio Assíncrono (FastAPI, Celery, Temporal)

```python
import asyncio
from coffeemail import AsyncCoffeeMail


async def main() -> None:
    client = AsyncCoffeeMail()

    response = await client.emails.send(
        {
            "from": {"email": "financeiro@seudominio.com.br", "name": "Financeiro"},
            "to": "destinatario@exemplo.com.br",
            "subject": "Sua fatura foi gerada",
            "html": "<p>Acesse o painel para visualizar o comprovante.</p>",
        }
    )

    if response.error:
        print(f"Erro: {response.error.message}")
        return

    print(f"Status do disparo: {response.data.status}")


asyncio.run(main())
```

---

## 🛡️ Ergonomia e Tratamento de Erros

Todas as chamadas retornam uma instância de `CoffeeMailResponse[T]`. Você pode escolher a abordagem ideal para seu estilo de código:

### 1. Desempacotamento de Tupla (Recomendado)

```python
data, error = client.emails.get("eml_123456")

if error:
    print(f"Erro {error.status_code} [{error.code}]: {error.message}")
else:
    print(f"Status atual: {data.status}")
```

### 2. Método `.unwrap()` (Lança Exceção em Falhas)

```python
from coffeemail import CoffeeMailError

try:
    email = client.emails.get("eml_123456").unwrap()
    print(f"Entregue em: {email.delivered_at}")
except CoffeeMailError as err:
    print(f"Exceção capturada: {err}")
```

---

## 📚 Recursos Disponíveis

Tanto `CoffeeMail` quanto `AsyncCoffeeMail` expõem os mesmos módulos:

| Módulo | Ações Principais |
| :--- | :--- |
| **`client.emails`** | `send()`, `send_batch()`, `get()`, `list()`, `get_events()`, `cancel()`, `resend()`, `tags()` |
| **`client.domains`** | `create()`, `list()`, `get()`, `verify()`, `get_health()`, `get_warmup()`, `update_warmup()`, `delete()` |
| **`client.templates`** | `create()`, `list()`, `get()`, `update()`, `preview()`, `format()`, `test_render()`, `test_send()`, `delete()` |
| **`client.audiences`** | `create()`, `list()`, `get()`, `update()`, `delete()`, `list_contacts()`, `create_contact()`, `bulk_add_contacts()`, `delete_contact()` |
| **`client.broadcasts`**| `create()`, `list()`, `get()`, `update()`, `delete()`, `send()`, `test_send()`, `cancel()` |
| **`client.suppressions`**| `create()`, `bulk_add()`, `list()`, `get()`, `delete()`, `reactivate()` |
| **`client.webhooks`** | `create()`, `list()`, `get()`, `update()`, `delete()`, `toggle()`, `rotate_secret()`, `test()`, `list_deliveries()` |
| **`client.stats`** | `get()` (totais de entregas, bounces, aberturas e séries temporais) |
| **Introspecção** | `client.introspect(force_refresh=False)` e `client.invalidate_introspection_cache()` |

---

## 🔒 Validação Criptográfica de Webhooks

Proteja suas rotas contra requisições forjadas validando a assinatura enviada no cabeçalho `x-coffeemail-signature`:

```python
from coffeemail import Webhooks

# Exemplo em FastAPI:
from fastapi import FastAPI, Header, HTTPException, Request

app = FastAPI()


@app.post("/webhooks/coffeemail")
async def webhook_endpoint(
    request: Request,
    x_coffeemail_signature: str = Header(...),
) -> dict[str, str]:
    raw_body = await request.body()

    is_valid = Webhooks.verify_signature(
        payload=raw_body,
        signature=x_coffeemail_signature,
        secret="whsec_seu_segredo_cadastrado",
    )

    if not is_valid:
        raise HTTPException(status_code=401, detail="Assinatura inválida")

    return {"status": "ok"}
```

---

## 🛠️ Desenvolvimento Local

```bash
# Sincronizar dependências com uv
uv sync --extra dev

# Executar suíte de testes com pytest
uv run pytest

# Executar checagem estrita de tipos com mypy
uv run mypy src tests

# Executar linter e formatação com ruff
uv run ruff check .
```

---

## 📄 Licença

Distribuído sob a licença **MIT**. Veja [LICENSE](./LICENSE) para mais informações.
