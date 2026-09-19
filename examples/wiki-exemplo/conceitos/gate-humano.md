---
type: Conceito
title: Gate humano
description: Detecção é automática; escrita passa por aprovação. Vale para lint e para curadoria.
status: stable
stale_after: 2027-09-19T00:00:00Z
---

# Gate humano

> A régua que impede a auto-cura de virar auto-poluição: o agente detecta sozinho, mas só grava com o seu OK.

## O que é

Automatizar a **detecção** (link quebrado, página órfã, conhecimento novo nas sessões) é seguro. Automatizar a **escrita** exige um portão: o agente propõe, uma pessoa aprova, e só então o aprovado é gravado (com backup e entrada no log).

## Como usamos

- O lint só aponta; quem corrige é o agente, item a item, depois do "ok".
- Fonte sensível (transcrição, decisão de pessoas): classificar é autônomo; gravar pede aprovação.
- Omissão deliberada não some em silêncio: vai para as notas do `log.md`.

## Conexões

- [Índice em dois níveis](indice-em-dois-niveis.md) — outra trava contra a degradação da wiki
- [Editor de notas](../ferramentas/editor-de-notas.md) — onde a pessoa lê o que o agente propôs

## Fontes

- Página de exemplo — sem fonte real.
