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

O gist do Karpathy é **deliberadamente abstrato** — descreve a ideia e sugere que cada um construa sua versão. Este repositório **é uma versão madura, comprovada em uso diário**, que vai além do gist em quatro pontos:

- **Ingest automatizado** — em vez de pedir ao LLM "ingira esta fonte" toda vez, você tem **alimentadores** (skills/rotinas) que fazem isso sozinhos. → [docs/02](docs/02-alimentadores.md) + [patterns](docs/patterns/)
- **Lint automatizado** — a checagem de saúde vira **rotina de curadoria** com a régua "detecta sozinho, escreve com gate humano". → [docs/03](docs/03-manutencao-e-curadoria.md)
- **Escala sem inchar** — **índice em dois níveis** (a raiz mapeia áreas, cada pasta lista suas páginas): numa wiki real de 147 páginas, o custo de entrada caiu de ~53 mil para menos de 1 mil tokens. → [docs/01](docs/01-metodologia-e-anatomia.md)
- **Padrão aberto** — a wiki nasce conformante com o [OKF](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md) (custo: um campo `type` por página). → [docs/05](docs/05-conformidade-okf.md)

## Quick start — montar sua wiki em 5 passos

1. **Gere a estrutura** (Python 3, sem instalar nada): `python3 scripts/wiki_new.py ~/minha-wiki --nome "Pessoal" --categorias "conceitos:ideias e conceitos;ferramentas:o que uso"` — instancia os [templates/](templates/) (`SCHEMA.md`, `CLAUDE.md`, `index.md`, `log.md` + um índice por categoria), já conformante com OKF.
2. **Ajuste as categorias** (subpastas) = as dimensões do seu domínio, e complete os `<placeholders>` do `SCHEMA.md`/`CLAUDE.md`.
3. **Aponte seu agente** pra ler o `index.md` ao iniciar e atualizar ao concluir (já está no `CLAUDE.md`/`AGENTS.md` template).
4. **Comece a ingerir** — manualmente, ou montando um [alimentador](docs/02-alimentadores.md).
5. **Ligue a curadoria** quando crescer ([docs/03](docs/03-manutencao-e-curadoria.md)) — checagem de saúde em [scripts/](scripts/) e skills prontas em [examples/skills/](examples/skills/).

Guia completo em **[docs/04 — Replicação](docs/04-replicacao.md)**.

## Índice

| Doc | O que cobre |
|---|---|
| **[01 — Metodologia & Anatomia](docs/01-metodologia-e-anatomia.md)** | A fundação, as 3 camadas, as 3 operações, e a anatomia canônica de uma wiki. **Comece aqui.** |
| **[02 — Alimentadores](docs/02-alimentadores.md)** | O Ingest automatizado: a "anatomia de um alimentador" + os padrões em [patterns/](docs/patterns/). |
| **[03 — Manutenção & Curadoria](docs/03-manutencao-e-curadoria.md)** | O Lint automatizado: a régua "detecta sozinho, escreve com gate" + curadoria das sessões. |
| **[04 — Replicação](docs/04-replicacao.md)** | Casos de uso, lições de multi-instância + guia passo-a-passo pra montar uma wiki nova. |
| **[05 — Conformidade OKF](docs/05-conformidade-okf.md)** | O padrão aberto: a régua de conformidade, o que o framework adota e o que não adota, e como migrar uma wiki existente. |
| [templates/](templates/) | Starter-kit: os arquivos-raiz prontos + índices de raiz/pasta + modelo de página. |
| [scripts/](scripts/) | Ferramentas em Python (só biblioteca padrão): criar wiki, checar saúde, sincronizar índices, injetar frontmatter, digest de sessões. |
| [examples/](examples/) | Mini-wiki de exemplo no formato atual + skills de curadoria (`wiki-correcao`, `wiki-curadoria`). |

## Estrutura do repositório

```
docs/        — a metodologia e os padrões
templates/   — starter-kit (copie e comece)
scripts/     — ferramentas (criar, checar, indexar, minerar sessões) + testes
examples/    — wiki de exemplo navegável + skills de curadoria
```

## Créditos e uso

Baseado no padrão **LLM Wiki** de **Andrej Karpathy** ([gist original](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)). Esta é uma instanciação/fork **by @caioxavier.ai**. Compartilhado livremente — **use à vontade, adapte ao seu contexto, crédito é apreciado.** Detalhes em [ATTRIBUTION.md](ATTRIBUTION.md).
