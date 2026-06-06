# 01 — Metodologia & Anatomia de uma Wiki LLM

> A fundação. O que é o padrão, e como é a anatomia canônica de **uma** wiki no framework.

---

## A ideia central

O uso comum de LLM com documentos é **RAG**: você sobe arquivos, o LLM recupera trechos na hora da pergunta e responde. Funciona, mas **redescobre o conhecimento do zero a cada pergunta** — nada se acumula.

A Wiki LLM é o oposto: o LLM **constrói e mantém uma wiki persistente** — uma coleção de Markdown interligado entre você e as fontes brutas. Cada nova fonte não é só indexada: é **lida, destilada e integrada** ao que já existe (atualiza páginas, revisa sínteses, sinaliza contradições). O conhecimento é compilado uma vez e **mantido vivo**, não re-derivado a cada consulta.

A diferença-chave: **a wiki é um artefato que compõe (compounding).** As referências cruzadas já estão lá. As contradições já foram sinalizadas. A síntese já reflete tudo que você leu. Ela fica mais rica a cada fonte.

**Divisão de trabalho:** você cuida de **fontes, exploração e boas perguntas**. O LLM faz **todo o resto** — resumir, cruzar, arquivar, manter consistência. Você nunca (ou raramente) escreve a wiki à mão.

> Analogia do Karpathy: *o editor de Markdown (ex.: Obsidian) é a IDE, o LLM é o programador, a wiki é o codebase.*

### Por que funciona
O caro de manter uma base de conhecimento não é ler nem pensar — é o **trabalho de manutenção** (atualizar referências, manter sínteses em dia, sinalizar contradições em dezenas de páginas). Humanos abandonam wikis porque a manutenção cresce mais rápido que o valor. **O LLM não cansa, não esquece de atualizar um link, toca 15 arquivos numa passada.** A wiki se mantém porque o custo de manutenção é quase zero.

---

## Padrão abstrato → instanciação madura

O gist original ([Karpathy](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)) é **deliberadamente abstrato** — descreve a ideia, não uma implementação, e sugere: *"compartilhe com seu agente LLM e construam juntos uma versão que sirva às suas necessidades."*

**Este framework é uma dessas versões**, instanciada de forma madura e comprovada em uso diário, com:
- **Alimentadores automatizados** (skills/rotinas que fazem o Ingest sozinhas) → ver [02](02-alimentadores.md)
- **Curadoria automatizada** (o Lint virou rotina com gate humano) → ver [03](03-manutencao-e-curadoria.md)
- **Multi-instância** (a mesma anatomia serve a vários contextos) → ver [04](04-replicacao.md)

---

## As 3 camadas (arquitetura)

| Camada | O que é | Quem escreve |
|---|---|---|
| **Fontes brutas** | A coleção curada de origem (artigos, PDFs, transcrições, docs). **Imutável** — o LLM lê, nunca altera. | Você (curadoria) |
| **A wiki** | Markdown gerado pelo LLM: páginas de entidade/conceito, sínteses, índice. | **O LLM (sempre)** |
| **O schema** | O `SCHEMA.md` (+ `CLAUDE.md`/`AGENTS.md`): diz como a wiki é estruturada, as convenções e os fluxos. É o que faz o LLM um **mantenedor disciplinado**, não um chatbot genérico. | Você + LLM co-evoluem |

---

## As 3 operações

- **Ingest** — uma fonte entra → o LLM lê, destila, escreve/atualiza páginas, atualiza `index.md`, registra em `log.md`. Uma fonte pode tocar 10-15 páginas. → automatizado nos **[alimentadores](02-alimentadores.md)**.
- **Query** — você pergunta → o LLM lê o `index.md`, abre as páginas relevantes, responde com citações. **Boas respostas viram página** (não somem no chat). É o que faz a exploração também compor.
- **Lint** — revisão de saúde: contradições, páginas órfãs, claims obsoletos, conceitos sem página, links quebrados, índice dessincronizado. → automatizado na **[curadoria](03-manutencao-e-curadoria.md)**.

---

## Anatomia canônica de uma wiki

Toda wiki do framework — seja pessoal, de um cliente ou de um time — tem a mesma espinha. Os templates prontos estão em [`templates/`](../templates/).

### Os 4 arquivos-raiz
- **`SCHEMA.md`** — o contrato operacional. Toda IA que tocar a wiki lê isto primeiro. Define estrutura, convenções, as operações e "o que NÃO fazer".
- **`CLAUDE.md`** (ou `AGENTS.md`) — a instrução pro agente: o que ler ao iniciar, hierarquia de fontes, quando atualizar.
- **`index.md`** — **orientado a conteúdo**: catálogo de tudo, por categoria, uma linha por página (`- [[arquivo]] — resumo`). O LLM lê primeiro pra navegar. Funciona bem até ~centenas de páginas, sem precisar de RAG/embeddings.
- **`log.md`** — **cronológico**: append-only, registro de ingests/queries/lints. Prefixo consistente (`## AAAA-MM-DD — [tipo: ...]`) → parseável com `grep`. Nunca apagar entradas.

### Categorias (subpastas)
Uma pasta por tipo de conhecimento = **as dimensões do seu domínio**. Exemplos comuns: `ferramentas/`, `conceitos/`, `projetos/`, `entidades/`. Numa wiki de um cliente/negócio, as categorias são as dimensões daquele negócio.

### Formato de página
```
# Título
> Uma linha: o que é e por que importa
## O que é
## Como funciona / Como usamos
## Conexões
- [[página-relacionada]] — motivo do link
## Fontes
## Log de atualizações
```

### Convenções que sustentam o framework
- **Sem fluff.** Cada frase carrega informação.
- **Granularidade:** 1 conceito = 1 página. Nada de `notas.md`/`misc.md`. Nomes kebab-case sem acento.
- **Links internos `[[...]]`** conectam as páginas — é o que cria valor no grafo.
- **Não duplicar:** se já existe, linkar — não copiar.
- **Atualizar, não substituir:** nova fonte sobre tema existente atualiza a página; contradição é marcada com data, o histórico não é apagado.
- **A página vence o índice:** se o `index.md` diverge da página real, a página é a verdade — sinalizar o drift.

---

Quem entende **estas 3 camadas + 3 operações + a anatomia** consegue montar uma wiki nova em qualquer contexto. Os [alimentadores](02-alimentadores.md) são formas automatizadas de **Ingest**; a [curadoria](03-manutencao-e-curadoria.md) é o **Lint** automatizado. Tudo se reduz a este núcleo.
