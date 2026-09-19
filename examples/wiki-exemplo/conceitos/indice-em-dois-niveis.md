---
type: Conceito
title: Índice em dois níveis
description: A raiz mapeia áreas; cada pasta lista as suas páginas. Índice é navegação, histórico é log.
status: stable
---

# Índice em dois níveis

> Um índice único que lista todas as páginas não escala; o mapa de áreas na raiz mais um índice por pasta, sim.

## O que é

O `index.md` da raiz tem **uma linha por área** (pasta) e não lista páginas. Cada pasta tem o seu `index.md`, com uma linha por página. O agente abre a raiz, escolhe a área e desce só até ali.

## Como usamos

- Página nova → linha no `index.md` **da pasta**; a raiz só muda se nascer uma área.
- Nunca escrever "Última atualização" ou resumo do que mudou em índice: isso é entrada de `log.md`.
- O índice pode ser sincronizado por varredura do disco (`scripts/wiki_index.py`), o que evita drift.

## Conexões

- [Gate humano](gate-humano.md) — a mesma disciplina, aplicada à escrita
- [Editor de notas](../ferramentas/editor-de-notas.md) — onde o mapa de áreas é navegado

## Fontes

- Página de exemplo — sem fonte real.
