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
| **Ponte com o sistema de gestão** | reunião da própria empresa → wiki **e** edições propostas em roadmap/decisões/ritos | [patterns/ponte-com-sistema-de-gestao.md](patterns/ponte-com-sistema-de-gestao.md) |

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

5. **Atualizar o índice DA PASTA e o `log.md`.** O índice é em dois níveis (ver [01](01-metodologia-e-anatomia.md)): a linha entra no `<categoria>/index.md` da área afetada, com link relativo à pasta; o `index.md` da raiz só muda se nascer uma **área** nova. Registrar no log com a assinatura datada parseável.
   - **Trava dura:** o alimentador **nunca** escreve narrativa de atualização em índice nenhum. Índice responde *"o que existe e onde"*; `log.md` responde *"o que aconteceu"*. Essa regra pertence à seção "o que esta skill NÃO faz" de toda skill de ingest — foi a ausência dela que deixou um índice chegar a 212 KB, com 57% de changelog, em duas wikis diferentes e sem que nada tivesse pedido.
   - **Preferir regenerar o índice a editá-lo.** Um índice varrido do disco por helper determinístico (o [`wiki_index.py`](../scripts/wiki_index.py)) não sofre drift: o que está no disco é o que aparece. Edit pontual no índice é o plano B, quando regenerar não compensa.
   - **Indexar o artefato principal é passo explícito, não subentendido.** Se a skill cria uma síntese, ela indexa a síntese — instrução escrita, com nome de arquivo. Deixar isso implícito funciona por analogia até o dia em que não funciona.

6. **Idempotência.** Reprocessar a mesma fonte não pode duplicar nem corromper. Duas âncoras possíveis:
   - **Hash do conteúdo** (ex.: SHA-1) registrado no log → hash visto = modo `replace`; hash novo = modo `append`.
   - **Slug determinístico + marcadores HTML + dedup textual** no índice/log.

6b. **Glossário de entidades canônicas, quando a fonte é fala transcrita.** Não é enfeite: num backfill real de 8 reuniões, o reconhecimento de voz transformou **"handoff" em "Randolph"** dezenas de vezes — sem a etapa explícita de decodificação, a base teria inventado uma pessoa. A regra que funciona: **nome que não bate com o glossário não é inferido** — vira item do checkpoint, e a confirmação humana volta para o glossário com data.

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
7. Faça o alimentador **atualizar o índice da pasta + o `log.md`** sempre — e escreva explicitamente que ele **não** põe histórico no índice (ver elemento 5).
7b. **Se a wiki é da própria casa, decida se o alimentador tem "ponte"** — isto é, se ele propõe edições em documentos de gestão que vivem **fora** da wiki (roadmap, log de decisões, registro de ritos). Vale a pena quando a reunião move a execução, e não só o conhecimento. Três travas obrigatórias, em [patterns/ponte-com-sistema-de-gestao.md](patterns/ponte-com-sistema-de-gestao.md).
8. Se a wiki de destino é conformante OKF, o alimentador escreve `type` no frontmatter de toda página que criar (ver [05](05-conformidade-okf.md)).
9. **Decida onde a skill mora: global ou local ao repositório.** A regra é **quem aciona**. Skill chamada por um despachante que roda em outra máquina (ou fora do repo) precisa ser **global** e usar caminhos absolutos. Skill chamada por quem está trabalhando dentro do repo mora no repo (`.claude/skills/` dele) e viaja junto com ele.

→ Ver os [patterns/](patterns/) pra exemplos completos e replicáveis de cada padrão.
