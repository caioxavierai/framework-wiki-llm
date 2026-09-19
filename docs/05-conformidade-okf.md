# 05 — Conformidade OKF (o padrão aberto)

> O framework é anterior ao OKF e não depende dele. Este doc registra **como uma wiki do framework nasce conformante** com o Open Knowledge Format — a especificação aberta, publicada pelo Google Cloud, para bases de conhecimento legíveis por humanos e por agentes.
> Fonte: <https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md> (v0.2 — confira a versão vigente antes de tratar este doc como verdade).

---

## Por que isso importa

O framework nasceu do padrão LLM Wiki do Karpathy: markdown interligado, índice, histórico. O OKF formaliza a mesma ideia como **especificação aberta** — mesma anatomia (`index.md`, `log.md`, páginas com frontmatter), com um vocabulário mínimo padronizado.

Duas consequências práticas:

- **Interoperabilidade.** Uma wiki conformante é lida por qualquer agente que conheça o padrão, sem precisar aprender as manias dela. A motivação da spec (§1) é exatamente essa: conhecimento em formatos comuns e estabelecidos — **legível** por humanos sem ferramenta, **interpretável** por agentes sem SDK próprio, **comparável** em controle de versão e **portável** entre ferramentas, organizações e tempo.
- **Entrega.** Uma wiki entregue a um cliente deixa de ser "o formato da casa" e passa a ser um padrão aberto com nome e documentação pública. Muda o que se pode prometer sobre portabilidade.

O custo é baixo o suficiente para ser o default: **conformidade plena exige um campo por arquivo.**

---

## A régua de conformidade (§11 da spec)

Uma wiki é conformante com OKF v0.2 se, e só se:

1. Todo `.md` não reservado tem um bloco de frontmatter YAML parseável.
2. Esse frontmatter tem um campo **`type`** não vazio.
3. Os arquivos reservados `index.md` e `log.md`, quando existem, seguem a estrutura definida.

É tudo. Um documento que carrega só `type` é **plenamente conformante**. O `wiki_lint.py --okf` checa os itens 1 e 2.

---

## O que o framework adota

| Elemento OKF | Como entra no framework |
|---|---|
| `type` (obrigatório) | O tipo da página. Na prática, deriva da categoria: `Ferramenta`, `Conceito`, `Sistema`, `Processo`, `Transcrição`, `Decisão`, `Produto`. Vocabulário **aberto** — nomes descritivos, sem registro central. |
| `title`, `description` | Recomendados. `description` é a mesma linha que vai para o índice da pasta — escreve-se uma vez. |
| `index.md` reservado | O índice em dois níveis do [01](01-metodologia-e-anatomia.md). Sem frontmatter, exceto `okf_version: "0.2"` no índice da raiz — o único lugar onde a spec permite. |
| `log.md` reservado | O log append-only do framework. Datas em heading ISO (`## AAAA-MM-DD`). *Nota:* a spec exemplifica o log com as entradas mais novas primeiro; o framework escreve no fim (cronológico). Divergência de ordem consciente — a data ISO no heading é o que importa para o parse. |
| Links markdown padrão | A recomendação do [01](01-metodologia-e-anatomia.md) para toda wiki que sai da máquina. |
| `status` | `draft` / `stable` / `deprecated`. Ausente ⇒ `stable`. |
| `generated` / `verified` | **Quem escreveu × quem conferiu.** `generated: { by: <agente>, at: <ISO> }` e `verified: [{ by: human:<id>, at: <ISO> }]`. O prefixo `human:` é o que distingue "um agente escreveu" de "uma pessoa conferiu" — a spec deriva daí um *trust tier*. Vale a pena em toda wiki onde um agente escreve direto. |
| `stale_after` | Data absoluta a partir da qual a página é considerada vencida. Substitui a heurística de "página parada há N dias" — e, principalmente, **permite não aplicar frescor onde ele não faz sentido** (uma transcrição de reunião é histórico congelado; um processo operacional envelhece). |
| `sources` | Procedência: de onde a página derivou. Encaixa direto na seção `## Fontes` que o framework já usa. |

## O que o framework NÃO adota (e por quê)

- **Attested Computation** (§10 da spec) — um tipo de documento que declara a computação sancionada de um número, com executor e verificador determinístico. É poderoso para **número financeiro auditável**, não para wiki de conceito. Fica registrado como oportunidade, não como padrão.
- **Abandonar `[[wikilinks]]` onde eles já são o tecido de navegação.** A regra de portabilidade é opcional na spec. Numa wiki pessoal com milhares de wikilinks e grafo em uso, converter custa mais do que a portabilidade vale. Registrar a escolha vale mais do que fingir conformidade total.
- **Ferramenta.** O OKF é uma especificação — não exige editor, SDK nem runtime. Existem ferramentas que o implementam, mas **adotar o formato não implica adotar nenhuma delas**. O formato é o ativo; a ferramenta é conveniência.

---

## Checklist — wiki nova nasce conformante

1. `index.md` da raiz com `okf_version: "0.2"` no frontmatter; um `index.md` por categoria, sem frontmatter.
2. `log.md` com datas em heading ISO.
3. Template de página com `type` no frontmatter (ver formato de página no [01](01-metodologia-e-anatomia.md)).
4. Alimentadores escrevem `type` sempre; `generated.by` quando quem escreve é agente.
5. Links internos em markdown relativo, se a wiki sai da máquina.
6. `SCHEMA.md` da wiki registra a trava "índice é navegação, histórico é log".

Cumprido isso, a wiki é conformante desde o primeiro arquivo — e continua sendo, porque a trava está onde o agente lê antes de escrever. O `python3 scripts/wiki_new.py` já gera tudo isso.

---

## Migrar uma wiki existente

A ordem que funcionou (uma wiki interna de 147 páginas):

1. **Índice primeiro.** Separar navegação de histórico e quebrar o índice único em raiz + pastas (`wiki_index.py`). É onde está a maior parte do ganho e não depende de OKF nenhum.
2. **`type` depois.** Derivado da pasta, em lote (`wiki_frontmatter.py --map "pasta=Tipo,..."`). `title`/`description` reaproveitam o H1 e o blockquote que a página já tem.
3. **Skills e schema na mesma janela.** Migrar a wiki sem atualizar quem escreve nela é migrar por uma semana: o próximo ingest volta ao formato antigo.
4. **Frescor por último**, e só nos tipos que envelhecem — senão o lint acusa dezenas de páginas corretas e alguém desliga o lint.
