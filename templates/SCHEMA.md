# SCHEMA.md — Wiki <NOME-DA-WIKI>

> Contrato operacional desta wiki. Toda IA que tocar este diretório lê este arquivo primeiro.
> Padrão **LLM Wiki** (Karpathy) · **LLM Wiki Framework** · conformante **OKF v0.2**.

## O que é esta Wiki

<Uma frase: domínio coberto, quem escreve (agente X + humano Y), qual a fonte canônica quando houver conflito.>

## Estrutura

```
wiki/
├── SCHEMA.md            ← este contrato
├── CLAUDE.md            ← instrução do agente
├── index.md             ← mapa das ÁREAS (uma linha por pasta) — NÃO lista páginas
├── log.md               ← histórico append-only (o ÚNICO lugar de histórico)
└── <categoria>/
    ├── index.md         ← as páginas daquela área (links relativos à pasta)
    └── <pagina>.md
```

## Convenções

- **Nomes:** kebab-case, sem acentos. 1 conceito = 1 página. Nada de `notas.md`/`misc.md`.
- **Frontmatter obrigatório** em toda página (conformidade OKF): `type` não-vazio. Recomendados: `title`, `description`, `status` (draft|stable|deprecated; ausente ⇒ stable), `stale_after` (só em tipo que envelhece).
- **Links:** markdown relativo (`[titulo](arquivo.md)`) — portável, qualquer consumidor lê.
- **Não duplicar:** se existe, linkar. **Atualizar, não substituir:** contradição vira nota datada.
- **A página vence o índice:** índice defasado é drift, a página é a verdade.

## A trava dura — índice é navegação, histórico é log

**Nunca** escrever `Última atualização:`, `Contexto anterior —` ou narrativa do que mudou em um
índice (raiz ou de pasta). Se responde *"o que aconteceu"* → é entrada de `log.md`. Se responde
*"o que existe e onde"* → é linha de índice. (Motivo: um índice real chegou a 212 KB, 57% changelog,
por imitação de agente — ver docs/01 do framework.)

## Operações

- **Ingest** — fonte nova → páginas atualizadas/criadas → linha no `index.md` DA PASTA → entrada no `log.md`.
- **Query** — ler `index.md` raiz → descer só na área relevante → responder citando páginas. Boa resposta vira página.
- **Lint** — `python3 <caminho-do-framework>/scripts/wiki_lint.py <esta-wiki> --okf` — detecção automática; **escrita só com aprovação humana**.

## log.md — formato de entrada

Append-only, **nunca deletar entradas**. Uma entrada por operação:

```
## AAAA-MM-DD — [tipo: ingest | query | lint | projeto]
- Fonte: [nome ou URL]
- Páginas criadas/atualizadas: [lista]
- Notas: [opcional]
```

## Formato de página

Ver `templates/pagina.md` do framework. Frontmatter + `# Título` + `> tagline` + `## O que é` +
`## Como usamos` + `## Conexões` + `## Fontes`.

## O que NÃO fazer

- Não mover/alterar raw sources (a wiki é síntese, não cópia).
- Não apagar entradas do `log.md`.
- Não pôr histórico em índice (trava acima).
- Não expor PII em página que outros leem.
- Não alterar este SCHEMA sem registrar no `log.md`.
