# 02 — Alimentadores (Ingest automatizado)

> Um **alimentador** é uma rotina/skill que automatiza a operação **Ingest**: pega uma fonte, destila e escreve na wiki sozinha. Este doc define o **padrão comum** a todos; os padrões concretos estão em [patterns/](patterns/).

---

## Os padrões de alimentador

Cada padrão é uma forma de Ingest — instancie os que fizerem sentido pro seu domínio:

| Padrão | Fonte → destino | Doc |
|---|---|---|
| **Ingestão de fontes** | link / PDF / vídeo / repositório → página de wiki (+ publicação externa opcional) | [patterns/ingestao-de-fontes.md](patterns/ingestao-de-fontes.md) |
| **Documento longo (chunking)** | livro / relatório / curso longo → uma página por capítulo + síntese-mãe | [patterns/documento-longo-chunking.md](patterns/documento-longo-chunking.md) |
| **Ingestão em lote (headless)** | muitas fontes de uma vez (ex.: um feed) → fichas estruturadas, sem humano no loop | [patterns/ingestao-em-lote.md](patterns/ingestao-em-lote.md) |
| **Transcrição → wiki** | transcrição de reunião → memória estruturada, com checkpoint humano | [patterns/transcricao-para-wiki.md](patterns/transcricao-para-wiki.md) |

Não por acaso, esses cobrem os casos que o padrão original cita: ler um livro, pesquisa/análise contínua, e wiki de time alimentada por transcrições.

---

## A anatomia de um alimentador (o padrão comum)

Todos seguem o mesmo esqueleto. **Para criar um alimentador novo, replique estes 7 elementos:**

1. **Gatilho + input definidos.** Um comando (`/skill <arg>`) ou uma descrição semântica que aciona a rotina. Input de um tipo claro (um arquivo, um link, um lote).

2. **Ler a fonte por inteiro antes de sintetizar.** Roteia por tipo se necessário (PDF, vídeo, web, repo). Para fontes longas, **fatiar e processar uma parte por vez, gravando no disco antes de avançar** — o filesystem é a memória, não o contexto do LLM.

3. **Sintetizar com template fixo, aterrado em contexto.** Seções fixas (resumo, denso, aplicação) garantem consistência. O conteúdo é **aterrado num arquivo de contexto de domínio** — é o que transforma "li algo" em "o que isso muda no meu contexto". Esse arquivo de contexto é o que mais muda ao adaptar pra outro domínio.

4. **Escrever na wiki sem destruir.** Duas técnicas comprovadas:
   - **Bloco gerenciado** entre marcadores HTML (`<!-- skill:start --> ... <!-- skill:end -->`): a reingestão substitui só esse bloco; o resto da página (escrito por humano) é preservado.
   - **Edit add-only:** só adiciona; informação superada vira nota datada, nunca é apagada; contradição é marcada (`> Atualização DD/MM: antes X, agora Y`).

5. **Atualizar `index.md` e `log.md`.** Inserir o link no índice (idempotente — só se ainda não existe) e registrar no log com a assinatura datada parseável.

6. **Idempotência.** Reprocessar a mesma fonte não pode duplicar nem corromper. Duas âncoras possíveis:
   - **Hash do conteúdo** (ex.: SHA-1) registrado no log → hash visto = modo `replace`; hash novo = modo `append`.
   - **Slug determinístico + marcadores HTML + dedup textual** no índice/log.

7. **Gate humano onde há risco.** Para fontes sensíveis (transcrições com dados de pessoas, decisões), **classificar é autônomo, mas gravar pede aprovação** — um checkpoint que apresenta o entendimento + plano e espera o OK. Para fontes públicas (um repo, um artigo), a ingestão pode ser direta.

---

## Dois princípios transversais

- **Separação raw ↔ síntese.** As fontes brutas **nunca são movidas nem alteradas**. A wiki é síntese, não cópia. O alimentador lê do raw e escreve na wiki.
- **Separação público ↔ privado.** O que outros leem (resumo, página compartilhada) é **neutro e sem dados sensíveis**; o acionável/privado fica em camada protegida ou é omitido. Vale forçar isso com um **validador determinístico** (um script que reprova um resumo "público" que cite dados privados).

---

## Divisão de trabalho determinístico ↔ LLM

O padrão mais robusto: **código determinístico faz o reproduzível** (parse, chunking, validação de schema, render, escrita no índice/log), e o **LLM faz só o julgamento** (sintetizar, decidir o que importa, rotear). Isso mantém a parte cara (LLM) focada e a parte mecânica barata, testável e idempotente. Prefira **stdlib pura** nos scripts (sem dependências externas) pra rodar em qualquer máquina.

---

## Como criar um alimentador novo (checklist)

1. Defina a **fonte** (o que entra) e o **destino** (quais páginas/categorias).
2. Escreva o **arquivo de contexto de domínio** (o aterramento dos insights).
3. Defina o **template de síntese** (seções fixas).
4. Escolha a **técnica de escrita** (bloco gerenciado vs. Edit add-only) e a **âncora de idempotência** (hash vs. slug+marcadores).
5. Decida se precisa de **gate humano** (fonte sensível → sim).
6. Implemente o **determinístico em código stdlib**, deixe o **julgamento pro LLM**.
7. Faça o alimentador **atualizar index/log** sempre.

→ Ver os [patterns/](patterns/) pra exemplos completos e replicáveis de cada padrão.
