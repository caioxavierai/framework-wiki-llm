# 03 — Manutenção & Curadoria (o Lint automatizado)

> O padrão original descreve o **Lint** como um ato manual ("periodicamente, peça ao LLM pra checar a saúde da wiki"). Aqui ele é automatizado em duas camadas + um lembrete agendado. É o que mantém o segundo cérebro **confiável e vivo** em vez de apodrecer.

---

## A régua de ouro

**Detecção é automática; escrita exige portão (gate) humano.**

- Automatizar a **detecção** (links quebrados, drift, contradições, abandono) é seguro e libertador.
- Automatizar a **escrita** precisa de aprovação — senão a auto-cura vira **auto-poluição**. Um segundo cérebro só serve se você confia 100% no que está lá.

Codifique essa régua no `SCHEMA.md` da sua wiki (na seção da Operação Lint).

---

## Duas camadas

### Camada A — Saúde mecânica
Determinística, barata, **read-only**. Um checker varre os docs-raiz e detecta:
- wikilinks `[[...]]` quebrados (resolvendo as variações: nome puro, subdir, alias);
- páginas órfãs (sem link de entrada);
- `index.md` dessincronizado das páginas reais;
- header de data do índice defasado vs. a edição mais recente;
- páginas estagnadas (ex.: >60 dias em categorias ativas).

Roda em silêncio; **só alerta quando há drift** (silêncio = saudável). **Nunca escreve** — propõe a correção e só aplica com o OK, com backup antes. Há um exemplo funcional em [`examples/scripts/wiki-lint.ts`](../examples/scripts/wiki-lint.ts).

> Cuidado com falsos positivos comuns: wikilinks dentro de blocos de código, paths relativos e referências a fontes fora da wiki. O checker de exemplo já trata esses casos.

### Camada B — Curadoria viva (a partir do uso)
A inteligência: minera as **sessões recentes do seu agente** e mantém a wiki em dia com o uso real. É a mineração de conhecimento do framework, **incremental e periódica**. Três entregas:
- 🆕 **Novo pra wiki:** conhecimento/decisão durável que apareceu nas sessões e não está na wiki → propõe página.
- ✏️ **Atualizar:** página que existe mas o uso recente evoluiu/contradiz → propõe o ajuste.
- 🗑️ **Parou de usar:** item tratado como ativo e ausente do uso há semanas → propõe marcar legado (sempre sugestão — você pode usar sem mencionar).

**Arquitetura (3 estágios):**
1. **Digest** (script read-only, barato) — varre só as sessões novas desde a última run, filtra ruído (subagentes, sessões triviais) e extrai intenções + ferramentas usadas + domínio. Corta MBs de log cru em KB de sinal. Exemplo em [`examples/scripts/sessions-digest.ts`](../examples/scripts/sessions-digest.ts).
2. **Mineração** (LLM) — lê os digests + o índice da wiki e monta o **Relatório de Curadoria** nos 3 blocos, cada item com evidência (qual sessão).
3. **Gate + aplicação** — você aprova item a item; aplica (backup + Edit add-only + log) e roda a Camada A pra garantir integridade.

**Estado incremental:** um arquivo de estado guarda a última run (janela "desde então"); um mapa de uso acumula "item → última vez visto" — base da detecção de abandono (melhora a cada ciclo).

### O lembrete agendado
Um job leve (cron/launchd/etc.) **só conta** sessões novas e te avisa ("N sessões novas, hora da curadoria"). A mineração (cara) **só roda quando você dispara** — nunca acorda o LLM à toa.

---

## O ciclo completo (periódico)
1. O lembrete te avisa.
2. Você dispara a curadoria.
3. Ela roda o digest, minera e mostra o relatório (novo / atualizar / parou de usar).
4. Você aprova o que quiser → ela escreve (backup + log) e valida com a Camada A.
5. Fecha a janela (marca a run como processada). Segundo cérebro atualizado com o uso do período.

---

## Como replicar a curadoria
1. **Camada A primeiro** (o checker mecânico) — base read-only, fecha a integridade.
2. **Camada B depois** — o digest determinístico (filtrar ruído é essencial) + o passe LLM com gate.
3. **A régua sempre:** detecta sozinho, escreve com aprovação.
4. **O lembrete** pra não depender de você lembrar — sem acordar LLM caro automaticamente.

> Lição da experiência: uma wiki (e até o repositório que a documenta) **congela** quando não tem gatilho de manutenção. A curadoria existe pra que nada apodreça — e vale incluir, no checklist da curadoria, "atualizar a própria documentação do framework quando algo novo surgir".
