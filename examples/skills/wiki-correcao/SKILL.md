---
name: wiki-correcao
description: >-
  Rotina de correção da wiki (Camada A — saúde mecânica). Roda um checker
  determinístico READ-ONLY sobre a wiki e detecta: links quebrados (wikilink e
  markdown relativo), páginas órfãs, índice fora de sincronia com o disco, índice de
  pasta faltando, narrativa de histórico infiltrada em índice, páginas
  estagnadas e (opcional) não conformidade OKF. Apenas PROPÕE —
  só aplica correção com a aprovação do dono da wiki, com backup antes. Acionar com
  /wiki-correcao, "corrige a wiki", "saúde da wiki", "lint da wiki", "wiki tá em ordem?".
---

# wiki-correcao — Camada A da curadoria da wiki

Implementa a **Operação Lint (camada mecânica)** do `SCHEMA.md`. Detecção é
automática e read-only; **toda escrita passa pela aprovação do dono da wiki**
(régua de auto-cura: o lint aponta, não reescreve sozinho).

> Ajuste os caminhos: `<framework>` é onde você clonou o framework; `<wiki>` é a
> raiz da wiki a checar.

## Fluxo

1. **Rodar o checker** (read-only, nunca escreve):
   ```bash
   python3 <framework>/scripts/wiki_lint.py <wiki> --okf --active-dirs projetos,conceitos --stale-days 60 --json
   ```
   (sem `--json` ele imprime um relatório legível; a skill usa o JSON. `--okf` só se a
   wiki é conformante; `--active-dirs` são as pastas onde "parada há N dias" faz sentido.)

2. **Apresentar o relatório**, organizado pelos checks, com a contagem de cada e os
   itens. Silêncio = saudável: se tudo zerado, dizer que a wiki está em ordem e parar.

3. **Para cada bloco com achado, PROPOR a correção e ESPERAR o "ok"** (item a item
   ou em bloco — o dono decide). Não aplicar nada sem aprovação explícita.
   - **Fora do índice da pasta** → propor a linha no formato do SCHEMA
     (`- [arquivo](arquivo.md) — resumo numa linha`), puxando o resumo do
     `description` do frontmatter ou do primeiro blockquote `>` da página.
     Inserção **add-only**; para lote, `wiki_index.py` (dry-run primeiro).
   - **Índice de pasta faltando** → propor criar (o `wiki_index.py --write` cria).
   - **Narrativa em índice** (`Última atualização:`, `Contexto anterior —`) → é
     entrada de `log.md`, não de índice: propor mover para o log e limpar o índice.
   - **Links quebrados** → mostrar origem + alvo; propor corrigir o alvo ou remover
     o link. Caso a caso.
   - **Órfãs** → sinalizar; sugerir de onde linkar (ou se é página a aposentar).
   - **Estagnadas** → só listar para revisão humana; não mexer no conteúdo.
   - **OKF** (`--okf`) → página sem frontmatter ou sem `type`; para lote,
     `wiki_frontmatter.py` (dry-run primeiro).

4. **Aplicar só o aprovado**, sempre com **backup `.bak-<timestamp>`** do arquivo
   antes de editar. Usar Edit pontual, nunca reescrever o arquivo inteiro.

5. **Registrar em `<wiki>/log.md`** (append, formato do SCHEMA
   `## AAAA-MM-DD — [tipo: lint]`) **somente se houve correção** — não poluir o log
   quando a wiki está saudável. Usar a data real (`date`), nunca de memória.

## Regras

- **Read-only por padrão.** O `wiki_lint.py` jamais escreve; quem escreve é esta
  skill, e só após o "ok".
- **Respeitar o SCHEMA.md** (formato de `index.md` e `log.md`; não alterar o SCHEMA
  sem registrar no log).
- **Fontes fora da wiki não contam como órfãs** — o checker já trata; não reverter.
- **Privacidade:** ao escrever resumo de página no índice, não expor dados de
  pessoas; manter a separação entre domínios.

## Escopo

Esta é a **Camada A** (mecânica). A **Camada B** — minerar as sessões recentes do
agente para trazer conhecimento novo, atualizar o que mudou e marcar o que parou de
ser usado — é a skill `wiki-curadoria`.
