# Planejamento de Implementação SDD: CoffeeMail Python SDK

Este documento estabelece o cronograma de entrega baseado em **Spec-Driven Development (SDD)**, com critérios de aceite, etapas de validação e integração ao **CoffeeMail SDK Workbench**.

---

## 🎯 Metodologia de Trabalho

Cada fase segue o ciclo rigoroso de SDD:
1. **Especificação do Contrato**: Validação de parâmetros, tipos Pydantic e assinaturas públicas.
2. **Testes Unitários / Mock First**: Escrita dos testes com `pytest` e `respx` simulando respostas da API antes da implementação final.
3. **Implementação da Lógica**: Desenvolvimento com Clean Code e SOLID, sem complexidade acidental.
4. **Verificação Estrita**: Execução do linter `ruff` e do type checker `mypy --strict`.
5. **Homologação no Workbench**: Conexão com o `runner-python` na porta 4002 para auditoria na interface visual.

---

## 📋 Fases do Roadmap

### **Fase 1: Fundação do Core, Tipos e Clientes Base**
* **Objetivo**: Estruturar transporte HTTP resiliente (síncrono e assíncrono), envelope de resposta e autenticação.
* **Tarefas**:
  - Implementar hierarquia de exceções em `coffeemail.core.errors`.
  - Implementar envelope `CoffeeMailResponse[T]` com suporte a desempacotamento de tupla e `.unwrap()`.
  - Implementar camada HTTP com `httpx.Client` e `httpx.AsyncClient` em `coffeemail.core.http`.
  - Implementar cliente principal `CoffeeMail` e `AsyncCoffeeMail`.
  - Implementar introspecção de chave `client.introspect()`.
* **Critérios de Aceite**:
  - Testes passando com 100% de cobertura para validação de chave nula/inválida.
  - Headers corretos (`User-Agent: coffeemail-python/0.1.0`, `Authorization`, `Accept-Language`).

---

### **Fase 2: Módulo de E-mails Transacionais (`emails`)**
* **Objetivo**: Implementar o principal recurso do SDK, cobrindo envios simples, em lote, consultas e eventos.
* **Tarefas**:
  - Modelar DTOs Pydantic v2: `SendEmailPayload`, `SendEmailResponse`, `EmailDetail`, `BatchSendEmailResult`, etc.
  - Implementar normalização de destinatários: aceitar string (`"user@dominio.com"`), dicionário (`{"name": "...", "email": "..."}`) ou listas de ambos.
  - Implementar suporte a anexos: aceitar string base64, bytes brutos ou caminho de arquivo local (`pathlib.Path` / `str`).
  - Implementar métodos: `send`, `send_batch`, `get`, `list`, `cancel`, `get_events`, `list_tags`.
* **Critérios de Aceite**:
  - Mapeamento correto de `snake_case` para o payload `camelCase` esperado pela API CoffeeMail.
  - Testes unitários com `respx` simulando requisições com múltiplos anexos e parâmetros de agendamento.

---

### **Fase 3: Módulos de Domínios (`domains`) e Webhooks (`webhooks`)**
* **Objetivo**: Configuração de remetentes autorizados e recebimento seguro de eventos.
* **Tarefas**:
  - Implementar métodos de domínios: `list`, `get`, `create`, `verify`, `get_health`, `delete`.
  - Implementar verificação de registros DNS (SPF, DKIM, DMARC, MX).
  - Implementar gestão de endpoints de Webhook: `list`, `get`, `create`, `update`, `toggle`, `rotate_secret`, `test`, `list_deliveries`.
  - Implementar utilitário criptográfico `webhooks.verify_signature` com verificação de timestamp e tolerância a drift de relógio.
* **Critérios de Aceite**:
  - Testes unitários comprovando rejeição de assinaturas HMAC inválidas ou com timestamp expirado.

---

### **Fase 4: Modelos (`templates`) e Pré-visualização**
* **Objetivo**: Gestão de templates HTML e renderização de prévias.
* **Tarefas**:
  - Implementar métodos: `list`, `get`, `create`, `update`, `delete`.
  - Implementar `preview` suportando tanto ID de modelo existente quanto código HTML bruto com variáveis de substituição.
  - Implementar `test_send` para envio de prova.
* **Critérios de Aceite**:
  - Retorno consistente com envelopamento `{ templates: [...] }`.

---

### **Fase 5: Audiências (`audiences`), Contatos (`contacts`) e Campanhas (`broadcasts`)**
* **Objetivo**: Gerenciamento de listas de e-mail e envios em massa.
* **Tarefas**:
  - Implementar gestão de audiências e contatos aninhados (`audiences.contacts`).
  - Adicionar atalhos ergonômicos no topo de `audiences` (`list_contacts`, `create_contact`, `bulk_add_contacts`).
  - Implementar módulo de campanhas `broadcasts` (`list`, `get`, `create`, `send`, `cancel`, `delete`).
* **Critérios de Aceite**:
  - Tipagem completa de atributos personalizados de contatos (`attributes: dict[str, Any]`).

---

### **Fase 6: Supressões (`suppressions`) e Estatísticas (`stats`)**
* **Objetivo**: Controle de reputação de remetente e visualização analítica.
* **Tarefas**:
  - Implementar `suppressions` para consulta e exclusão de bounces/unsubscribes.
  - Implementar `stats` para recuperação de taxas de abertura, entrega e rejeição por período.
* **Critérios de Aceite**:
  - Validação de formatação de datas ISO 8601 nos filtros de estatísticas.

---

### **Fase 7: Integração com o Workbench e Runner Python**
* **Objetivo**: Criar o backend `coffee-mail-sdk-workbench/backends/runner-python` consumindo o pacote local.
* **Tarefas**:
  - Criar mini-backend em FastAPI ou Flask na porta 4002 implementando a Runner Specification API.
  - Habilitar o seletor "Python Runner" no front-end web do Workbench.
  - Executar bateria completa de testes de ponta a ponta na interface visual.
* **Critérios de Aceite**:
  - 100% dos botões e formulários do Workbench funcionando igualmente no Runner Node e no Runner Python.
