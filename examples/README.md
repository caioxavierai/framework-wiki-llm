# Exemplos

Material de referência pra ver o framework funcionando.

## `wiki-exemplo/`
Uma mini-wiki fictícia, navegável, **no formato atual**: índice em dois níveis (a raiz mapeia as áreas, cada pasta lista as suas páginas), frontmatter OKF em toda página, links em markdown relativo e `log.md` como único lugar de histórico. Foi montada com [`scripts/wiki_new.py`](../scripts/wiki_new.py) e serve pra:
- ver como uma wiki real fica montada;
- rodar as ferramentas contra ela:
  ```bash
  python3 scripts/wiki_lint.py examples/wiki-exemplo --okf   # saúde: 0 achados
  python3 scripts/wiki_index.py examples/wiki-exemplo        # índices em dia
  ```

## `skills/`
As duas skills de curadoria, em versão genérica — o **Lint automatizado** descrito em [docs/03](../docs/03-manutencao-e-curadoria.md):

- **`wiki-correcao`** — Camada A: roda o checker de saúde e propõe as correções, com gate humano.
- **`wiki-curadoria`** — Camada A + B: minera as sessões recentes do seu agente e propõe o que é novo, o que mudou e o que parou de ser usado.

Para usar, copie a pasta da skill para as skills do seu agente (no Claude Code, `~/.claude/skills/`) e ajuste os caminhos `<framework>` e `<wiki>` dentro dela.

> As ferramentas que essas skills chamam estão em [`scripts/`](../scripts/), na raiz do repositório (Python, só biblioteca padrão). A régua é sempre a mesma: **detecta sozinho, escreve com gate.**
