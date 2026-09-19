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
- **Índice em dois níveis e conformidade com o padrão aberto OKF** (a wiki escala sem inchar o custo de entrada) → ver abaixo e [05](05-conformidade-okf.md)

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
- **`index.md`** — **navegação, em dois níveis** (ver abaixo): a raiz mapeia as áreas, cada pasta lista as suas páginas. O LLM lê primeiro pra se orientar, sem precisar de RAG/embeddings.
- **`log.md`** — **cronológico**: append-only, registro de ingests/queries/lints. Prefixo consistente (`## AAAA-MM-DD — [tipo: ...]`) → parseável com `grep`. Nunca apagar entradas. **É o único lugar de histórico da wiki.**

### O índice em dois níveis (progressive disclosure)

Um índice único que lista todas as páginas **não escala** — e o limite não é o número de páginas, é o peso da linha. Medido em uma wiki interna de **147 páginas**: o `index.md` tinha **212 KB (~53 mil tokens)**, carregados em toda sessão de agente. Outra wiki, de 448 páginas, tinha 77 KB. O que engorda é descrição gorda por entrada e histórico infiltrado, não a quantidade de páginas.

A anatomia canônica é:

```
wiki/
├── index.md              ← mapa das ÁREAS: uma linha por pasta. NÃO lista páginas.
│                            Único índice com frontmatter: okf_version: "0.2"
├── log.md                ← histórico de toda a wiki (append-only)
├── SCHEMA.md · CLAUDE.md
└── <categoria>/
    ├── index.md          ← as PÁGINAS daquela área, links relativos à pasta, sem frontmatter
    └── <pagina>.md
```

- **Raiz** — `- [Área](pasta/index.md) — o que cobre · N páginas`, mais as seções que não são pasta (ponteiros para fora). Deve caber em ~1k tokens e ficar estável conforme a wiki cresce.
- **Pasta** — cabeçalho de 3 linhas (título, o que a área cobre, volta para `../index.md` e `../log.md`) e uma linha por página: `- [arquivo](arquivo.md) — resumo em uma linha`.
- **Efeito medido:** na wiki de 147 páginas, entrar caiu de **53.170 para 879 tokens** (−98,3%); com a área aberta, ~1.170. A leitura passa a ser "mapa → desço só onde interessa" em vez de "carrego tudo".

O índice **pode e deve ser gerado por varredura do disco** ([`scripts/wiki_index.py`](../scripts/wiki_index.py) faz isso, só adicionando e nunca reescrevendo descrição curada). Índice regenerado não sofre drift: o que existe no disco é o que aparece.

### A trava: índice é navegação, histórico é log

**Nunca escrever narrativa de atualização em um índice** — nada de `Última atualização: …`, `Contexto anterior — …` ou resumo do que mudou. Se a informação responde *"o que aconteceu"*, ela é entrada de `log.md`. Se responde *"o que existe e onde"*, é linha de índice.

Não é preciosismo: **56,7% do índice de 212 KB era changelog no cabeçalho** — 39 linhas, uma delas com 9.462 caracteres. E o padrão apareceu **em duas wikis diferentes sem que nenhum documento, skill ou schema jamais tivesse pedido**. Nasceu por imitação: o agente abre o índice, vê o formato no topo e replica. Por isso a trava tem que estar escrita em quatro lugares, e não só num:

1. no **cabeçalho do próprio índice** (é o que o agente lê imediatamente antes de escrever) — a defesa mais forte;
2. no **`SCHEMA.md`** da wiki (a lei que todo agente lê primeiro);
3. na **skill** que alimenta a wiki (seção "o que esta skill NÃO faz");
4. no **`AGENTS.md`/`CLAUDE.md`** do agente que escreve nela.

O `wiki_lint.py` tem um check (`index_narrative`) que pega a regressão.

### Categorias (subpastas)
Uma pasta por tipo de conhecimento = **as dimensões do seu domínio**. Exemplos comuns: `ferramentas/`, `conceitos/`, `projetos/`, `entidades/`. Numa wiki de um cliente/negócio, as categorias são as dimensões daquele negócio. **Cada pasta nasce com o seu `index.md`**, mesmo vazio — criar no dia zero custa minutos; adiar custa uma cirurgia.

### Formato de página
```
---
type: <Tipo>              # OBRIGATÓRIO — a única exigência de conformidade OKF (ver 05)
title: <Título>           # recomendado
description: <uma linha>  # recomendado — é a linha que vai pro índice da pasta
status: draft | stable | deprecated
---

# Título
> Uma linha: o que é e por que importa
## O que é
## Como funciona / Como usamos
## Conexões
- [página-relacionada](pagina.md) — motivo do link
## Fontes
```

### Convenções que sustentam o framework
- **Sem fluff.** Cada frase carrega informação.
- **Granularidade:** 1 conceito = 1 página. Nada de `notas.md`/`misc.md`. Nomes kebab-case sem acento.
- **Links internos conectam as páginas** — é o que cria valor no grafo. Duas formas, e a escolha é consciente:
  - `[[wikilink]]` — grafo nativo no Obsidian e em editores compatíveis, mas **não é portável**: outro consumidor (incluindo um agente que não conhece a convenção) não resolve o link.
  - `[caminho](arquivo.md)` **relativo** — markdown padrão, portável, conformante com OKF, resolve em qualquer editor, no GitHub e para qualquer agente.
  - **Recomendação:** markdown relativo em toda wiki que sai da máquina (cliente, produto, entrega); `[[ ]]` só em wiki pessoal onde o grafo do Obsidian é usado de fato. O `wiki_lint.py` entende as duas formas.
- **Não duplicar:** se já existe, linkar — não copiar.
- **Atualizar, não substituir:** nova fonte sobre tema existente atualiza a página; contradição é marcada com data, o histórico não é apagado.
- **A página vence o índice:** se o `index.md` diverge da página real, a página é a verdade — sinalizar o drift.

---

Quem entende **estas 3 camadas + 3 operações + a anatomia** consegue montar uma wiki nova em qualquer contexto. A conformidade com o padrão aberto **OKF** — o que ela exige e o que o framework adota — está em [05](05-conformidade-okf.md). Os [alimentadores](02-alimentadores.md) são formas automatizadas de **Ingest**; a [curadoria](03-manutencao-e-curadoria.md) é o **Lint** automatizado. Tudo se reduz a este núcleo.
