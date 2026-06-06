# CLAUDE.md — Instrução do Agente para esta Wiki

> Instrução para o agente (Claude Code, Codex, etc.) ao trabalhar nesta wiki.
> *(Template — adapte ao seu contexto. Se usar Codex/outro, renomeie para `AGENTS.md`.)*

---

## Ao iniciar uma sessão
1. Ler `index.md` pra ter o contexto acumulado.
2. Se houver página relacionada ao tema da sessão, ler também.
3. **Se a página real divergir do index, a página vence** — sinalizar o drift.

## Durante a sessão
- Ao encontrar algo já documentado, consultar a página antes de recomendar.
- Ao tomar uma decisão, verificar se contradiz algo na wiki.
- Ao descobrir algo útil que não está na wiki, anotar pra atualizar ao final.

## Ao concluir algo relevante
Atualizar a página correspondente (criar se não existir) e **registrar em `log.md`**. Boa resposta de chat que vira conhecimento durável → virar página antes de se perder.

## Regras
- A wiki é **síntese**, não cópia das fontes brutas (que são imutáveis).
- Escrita é **add-only**: não apagar; informação superada vira nota datada.
- Privacidade: não expor dados sensíveis em páginas que outros leem.
- Seguir as convenções do `SCHEMA.md`.
