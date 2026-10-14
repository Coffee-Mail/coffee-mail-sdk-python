# Contribuindo com o CoffeeMail Python SDK

Obrigado pelo interesse! Este guia resume como propor mudanças.

## Antes de começar

- Bugs e sugestões: abra uma issue descrevendo o problema e como reproduzi-lo (sem chaves de API).
- Vulnerabilidades: **não** abra issue pública; siga o [SECURITY.md](SECURITY.md).
- Mudanças que alterem a API pública: abra uma issue para discussão antes do PR.

## Ambiente

Requer Python 3.10+ e uv.

```bash
uv sync --extra dev
uv run ruff format --check . && uv run ruff check . && uv run mypy src tests && uv run pytest
```

Todos os comandos acima precisam passar antes de qualquer PR.

## Regras de código

O SDK segue as regras de código da CoffeeMail:

- Código em inglês; documentação, issues, commits e PRs em português do Brasil.
- Sem comentários fora da documentação da API pública.
- Sem `else`/`elseif`/`switch`: use retorno antecipado ou tabelas de lookup.
- Sem textos e números mágicos: use constantes nomeadas.
- Cada comportamento novo vem com testes: caminho feliz e ao menos dois caminhos de erro.

## Compatibilidade

O SDK é usado em produção. Mudanças na API pública devem **adicionar e depreciar**, nunca renomear ou remover. Os SDKs oficiais (Node.js, Python, PHP e Java) mantêm o mesmo contrato: uma funcionalidade nova deve existir em todos.

## Commits e PRs

- Mensagens em português, no formato `tipo(escopo): descrição` (ex.: `feat(emails): expõe metadata no envio`).
- Descreva no PR o que muda, por que e como foi testado.
