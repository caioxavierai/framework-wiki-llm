# Exemplos

Material de referência pra ver o framework funcionando.

## `wiki-exemplo/`
Uma mini-wiki navegável — os 4 arquivos-raiz (`SCHEMA.md`, `CLAUDE.md`, `index.md`, `log.md`) + algumas páginas com wikilinks entre si. Serve pra:
- ver como uma wiki real fica montada;
- rodar os scripts abaixo contra ela.

## `scripts/`
Versões de **referência** dos utilitários de curadoria ([docs/03](../docs/03-manutencao-e-curadoria.md)). Rodam com [Bun](https://bun.sh). São educativos — leia e adapte ao seu caso.

- **`wiki-lint.ts`** — Camada A (saúde mecânica), 100% read-only. Detecta links quebrados, órfãs, drift do índice, header defasado e páginas estagnadas.
  ```bash
  WIKI_ROOT=./examples/wiki-exemplo bun run examples/scripts/wiki-lint.ts
  ```
- **`sessions-digest.ts`** — Estágio 1 da Camada B: varre as sessões novas do seu agente e extrai um digest barato pro agente minerar. **O formato de sessão varia por agente** — adapte o `parseSession()` ao seu (o exemplo assume `.jsonl` por evento).
  ```bash
  SESSIONS_DIRS=~/.seu-agente/sessions bun run examples/scripts/sessions-digest.ts
  ```

> Ambos são read-only sobre o conteúdo; a escrita na wiki é sempre do agente, com aprovação humana (a régua "detecta sozinho, escreve com gate").
