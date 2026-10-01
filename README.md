# CoffeeMail Python SDK (`coffeemail`)

SDK oficial da **CoffeeMail** para Python, com suporte nativo a operações **Síncronas** e **Assíncronas**, tipagem estrita via **Pydantic v2**, compatibilidade total com PEP 561 (`py.typed`) e padrão de retorno seguro `{ data, error }`.

---

## 📦 Instalação

```bash
pip install coffeemail
# ou utilizando uv:
uv add coffeemail
# ou utilizando poetry:
poetry add coffeemail
```

---

## ⚡ Início Rápido

### 1. Envio Transacional Síncrono (Django, Flask, Scripts)

```python
from coffeemail import CoffeeMail

# Lê automaticamente a variável de ambiente COFFEEMAIL_API_KEY se omitida:
client = CoffeeMail()

data, error = client.emails.send(
    {
        "from": "contato@seudominio.com.br",
        "to": "cliente@empresa.com",
        "subject": "Boas-vindas ao CoffeeMail!",
        "html": "<h1>Olá, seja bem-vindo!</h1>",
    }
)

if error:
    print(f"Erro ao disparar e-mail: {error.message}")
else:
    print(f"E-mail enfileirado com sucesso! ID: {data.id}")
```

### 2. Envio Assíncrono de Alta Performance (FastAPI, Celery, Temporal)

```python
import asyncio
from coffeemail import AsyncCoffeeMail


async def main():
    client = AsyncCoffeeMail()

    response = await client.emails.send(
        {
            "from": {"email": "notificacoes@seudominio.com.br", "name": "Notificações"},
            "to": "destinatario@gmail.com",
            "subject": "Sua fatura foi gerada",
            "html": "<p>Acesse o painel para visualizar o boleto.</p>",
        }
    )

    if response.error:
        print(f"Falha: {response.error}")
        return

    print(f"Status do disparo: {response.data.status}")


asyncio.run(main())
```

---

## 🛡️ Padrão de Resposta Seguro e Ergonomia

Todas as chamadas do SDK retornam uma instância de `CoffeeMailResponse[T]`. Você pode optar pelo estilo que melhor se adapta à sua equipe:

### Desempacotamento de Tupla (Recomendado)
```python
data, error = client.emails.get("msg_123")
if error:
    print(f"Falha: {error}")
else:
    print(f"Status: {data.status}")
```

### Método `.unwrap()` (Lança Exceção em Caso de Erro)
```python
try:
    email = client.emails.get("msg_123").unwrap()
    print(f"Entregue em: {email.delivered_at}")
except CoffeeMailError as err:
    print(f"Exceção capturada: {err}")
```

---

## 🧩 Recursos Disponíveis

* **`emails`**: Disparo individual, em lote (`send_batch`), consulta de status, cancelamento de agendamentos e listagem de eventos.
* **`domains`**: Criação de domínios e verificação de registros DNS (SPF, DKIM, DMARC, MX).
* **`templates`**: Cadastro de modelos HTML, renderização de pré-visualização (`preview`) e envio de testes.
* **`audiences`**: Listas de contatos, inclusão em lote (`bulk_add`) e gestão de inscritos.
* **`broadcasts`**: Campanhas e envios em massa com agendamento.
* **`suppressions`**: Consulta e gerenciamento de lista de supressão (bounces e unsubscribes).
* **`webhooks`**: Gerenciamento de endpoints e validação criptográfica de assinaturas HMAC SHA-256.
* **`stats`**: Consulta de taxas de entrega, abertura e rejeição por período.

---

## 🔒 Validação Criptográfica de Webhooks

Proteja suas rotas contra requisições forjadas validando a assinatura enviada no header `x-coffeemail-signature`:

```python
from coffeemail import Webhooks

is_valid = Webhooks.verify_signature(
    payload=request_body_raw,
    signature=headers.get("x-coffeemail-signature"),
    secret="whsec_seu_segredo_cadastrado",
)

if not is_valid:
    return {"error": "Assinatura inválida"}, 401
```

---

## 🛠️ Desenvolvimento e Testes

Para contribuir ou rodar os testes localmente:

```bash
# Instalar dependências de desenvolvimento com uv:
uv sync --extra dev

# Executar suíte de testes unitários:
uv run pytest

# Executar checagem estrita de tipos com mypy:
uv run mypy src

# Executar linter e formatação com ruff:
uv run ruff check .
```
