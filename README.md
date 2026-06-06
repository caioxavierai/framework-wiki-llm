# LLM Wiki Framework

> Um framework para construir um **segundo cérebro vivo** com agentes de IA: uma base de conhecimento em Markdown que **se acumula, se mantém e se cura sozinha** — em vez de redescobrir tudo a cada conversa.
>
> *Fork e instanciação madura do padrão [LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) de Andrej Karpathy — by **@caioxavier.ai**. Ver [ATTRIBUTION.md](ATTRIBUTION.md).*

---

## O problema

O uso comum de LLM com documentos é **RAG**: você sobe arquivos, o modelo recupera trechos na hora da pergunta e responde. Funciona, mas **redescobre tudo do zero a cada pergunta** — nada se acumula. Pergunte algo que exige cruzar cinco fontes e o modelo refaz o trabalho toda vez.

## A ideia

Em vez de só recuperar trechos brutos, o LLM **constrói e mantém uma wiki persistente** — Markdown interligado que fica entre você e as fontes. Cada nova fonte é lida, destilada e **integrada** ao que já existe. O conhecimento é compilado uma vez e **mantido vivo**.

```
FONTES BRUTAS  →  [Ingest]  →  WIKI (síntese viva)  →  [Query]  →  o agente opera com contexto acumulado
   (imutáveis)                      ↑  [Lint / Curadoria]  ↓
                                 mantida saudável e atualizada (com você no portão)
```

**Divisão de trabalho:** você cuida de **fontes, exploração e boas perguntas**; o LLM faz **todo o resto** — resumir, cruzar, arquivar, manter consistência. Você quase nunca escreve a wiki à mão.

## Por que este framework (e não só o gist)

O gist do Karpathy é **deliberadamente abstrato** — descreve a ideia e sugere que cada um construa sua versão. Este repositório **é uma versão madura, comprovada em uso diário**, que vai além em dois pontos:

- **Ingest automatizado** — em vez de pedir ao LLM "ingira esta fonte" toda vez, você tem **alimentadores** (skills/rotinas) que fazem isso sozinhos. → [docs/02](docs/02-alimentadores.md) + [patterns](docs/patterns/)
- **Lint automatizado** — a checagem de saúde vira **rotina de curadoria** com a régua "detecta sozinho, escreve com gate humano". → [docs/03](docs/03-manutencao-e-curadoria.md)

## Quick start — montar sua wiki em 5 passos

1. **Copie os [templates/](templates/)** pra uma pasta nova: `SCHEMA.md`, `CLAUDE.md`, `index.md`, `log.md`.
2. **Defina suas categorias** (subpastas) = as dimensões do seu domínio.
3. **Aponte seu agente** pra ler o `index.md` ao iniciar e atualizar ao concluir (já está no `CLAUDE.md` template).
4. **Comece a ingerir** — manualmente, ou montando um [alimentador](docs/02-alimentadores.md).
5. **Ligue a curadoria** quando crescer ([docs/03](docs/03-manutencao-e-curadoria.md)) — há scripts de exemplo em [examples/scripts/](examples/scripts/).

Guia completo em **[docs/04 — Replicação](docs/04-replicacao.md)**.

## Índice

| Doc | O que cobre |
|---|---|
| **[01 — Metodologia & Anatomia](docs/01-metodologia-e-anatomia.md)** | A fundação, as 3 camadas, as 3 operações, e a anatomia canônica de uma wiki. **Comece aqui.** |
| **[02 — Alimentadores](docs/02-alimentadores.md)** | O Ingest automatizado: a "anatomia de um alimentador" + os padrões em [patterns/](docs/patterns/). |
| **[03 — Manutenção & Curadoria](docs/03-manutencao-e-curadoria.md)** | O Lint automatizado: a régua "detecta sozinho, escreve com gate" + curadoria das sessões. |
| **[04 — Replicação](docs/04-replicacao.md)** | Casos de uso + guia passo-a-passo pra montar uma wiki nova. |
| [templates/](templates/) | Starter-kit: os 4 arquivos-raiz prontos pra copiar + modelo de página. |
| [examples/](examples/) | Mini-wiki de exemplo + scripts educativos (lint e digest de sessões). |

## Estrutura do repositório

```
docs/        — a metodologia e os padrões
templates/   — starter-kit (copie e comece)
examples/    — exemplo navegável + scripts de referência
```

## Créditos e uso

Baseado no padrão **LLM Wiki** de **Andrej Karpathy** ([gist original](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)). Esta é uma instanciação/fork **by @caioxavier.ai**. Compartilhado livremente — **use à vontade, adapte ao seu contexto, crédito é apreciado.** Detalhes em [ATTRIBUTION.md](ATTRIBUTION.md).
