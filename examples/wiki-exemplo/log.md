# log.md — Histórico da wiki de Exemplo

> Append-only. Nunca deletar entradas. TODO histórico da wiki vive aqui (nunca nos índices).
> Formato: `## AAAA-MM-DD — [tipo: ingest | query | lint | projeto]` + fonte + páginas afetadas.

## 2026-09-19 — [tipo: ingest]

- Fonte: exemplo ilustrativo (nenhuma fonte real)
- Páginas criadas: ferramentas/editor-de-notas, conceitos/indice-em-dois-niveis, conceitos/gate-humano
- Notas: mini-wiki fictícia de demonstração, montada com `scripts/wiki_new.py`.

## 2026-09-19 — [tipo: lint]

- Fonte: `python3 scripts/wiki_lint.py examples/wiki-exemplo --okf`
- Páginas afetadas: nenhuma
- Notas: wiki saudável (0 achados); índices em dia com `scripts/wiki_index.py`.
