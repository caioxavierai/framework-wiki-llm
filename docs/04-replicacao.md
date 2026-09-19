# 04 — Replicação

> O framework não é uma wiki só — é um **padrão multi-instância**. Aqui estão os casos de uso típicos, o que aprendemos rodando várias instâncias em paralelo e o guia passo-a-passo pra montar uma wiki nova do zero.

---

## Casos de uso (a mesma anatomia, contextos diferentes)

| Caso | Fontes (raw) | Categorias típicas | Quem lê |
|---|---|---|---|
| **Pessoal / ecossistema** | artigos, repos, vídeos, livros que você estuda | ferramentas, conceitos, projetos, decisões | você + seus agentes |
| **Por cliente / por projeto** | transcrições de reunião, documentos do cliente | as dimensões do diagnóstico daquele cliente | a equipe que atende o cliente |
| **Empresa própria (interna)** | transcrições de reunião, decisões, documentos de projeto | áreas/processos da empresa | o time, com você no portão da curadoria |
| **Empresa própria + ponte** | idem, com o sistema de gestão (roadmap, decisões, ritos) | idem + áreas de gestão | diretoria e time; o alimentador propõe edições fora da wiki — ver [ponte com o sistema de gestão](patterns/ponte-com-sistema-de-gestao.md) |
| **De uma cadeira/área** | transcrições e materiais da área | plano, calendário, aprendizados | quem assume a cadeira |

**O que elas têm em comum:** a mesma anatomia (SCHEMA/CLAUDE/index/log + categorias + formato de página + índice em dois níveis), as 3 operações (Ingest/Query/Lint) e a régua de curadoria. **O que muda entre elas:** as fontes brutas, as categorias (dimensões do domínio) e quais alimentadores estão plugados.

> Se você roda várias instâncias, defina a hierarquia: uma wiki pode ser canônica de ecossistema e as outras satélites. Conhecimento de ecossistema vai na canônica; a satélite só linka, não duplica.

### O que aprendemos com várias instâncias

- **Nascer certa é barato; corrigir depois é cirurgia.** Uma instância criada já com índice em dois níveis, `type` em toda página, links markdown relativos e a trava do índice escrita no `SCHEMA.md` custou minutos. A migração equivalente numa wiki interna com 147 páginas já formadas exigiu reestruturar um índice de 212 KB. É a prova prática do Passo 1 do guia abaixo.
- **A wiki nasce com a cadeira.** Quando uma área ganha repositório próprio, a wiki e o alimentador entram no dia 1 — e o cérebro da área acumula desde a primeira sessão, em vez de esperar "sobrar tempo".
- **Alimentador pode ser local ao repositório ou global.** A regra é quem aciona: skill chamada por um despachante de outra máquina precisa ser global; skill chamada por quem está trabalhando no repo mora no repo (`.claude/skills/`).
- **A política de privacidade é atributo da instância, não do framework.** Uma wiki de ecossistema pode abstrair nomes de pessoas; uma base interna que precisa responder sobre gente de verdade pode registrar nominalmente, por decisão explícita do dono; uma de cliente segue a régua do cliente, e o material client-facing usa só cargos. Quem escreve precisa saber em qual instância está — e o `SCHEMA.md` de cada uma tem que dizer isso.

---

## Guia de replicação — montar uma wiki nova do zero

### Passo 1 — Infraestrutura (anatomia)
**Atalho:** `python3 scripts/wiki_new.py <destino> --nome "Pessoal" --categorias "slug:descrição;slug2:descrição2"` — instancia os [`templates/`](../templates/) já conformantes e no formato de dois níveis. Depois valide: `python3 scripts/wiki_lint.py <destino> --okf`. Ou manualmente:
- `SCHEMA.md` — o contrato (ajuste as categorias ao domínio).
- `CLAUDE.md` (ou `AGENTS.md`) — instrução do agente.
- `index.md` — **mapa das ÁREAS**: uma linha por categoria apontando para o índice dela (`- [Área](pasta/index.md) — o que cobre`). Frontmatter com `okf_version: "0.2"`. **Não lista páginas.**
- `log.md` — vazio, com o cabeçalho. É o **único** lugar de histórico da wiki.
- Subpastas = as **categorias do domínio** — **cada uma com seu `index.md`** desde o dia zero, mesmo vazio.
- No `SCHEMA.md`, registre a trava: **índice é navegação, histórico é `log.md`** (ver [01](01-metodologia-e-anatomia.md)).

> Criar os índices de pasta no dia zero custa minutos. Adiar custa uma cirurgia.

### Passo 2 — Definir as fontes brutas
Onde vivem os raw sources (artigos, transcrições, docs) — **imutáveis**, a wiki nunca os altera.

### Passo 3 — Plugar os alimentadores (Ingest)
Escolha quais [padrões de alimentador](02-alimentadores.md) fazem sentido e adapte. O que **muda** ao replicar:
- o **arquivo de contexto de domínio** (o aterramento dos insights);
- as **categorias** (dimensões do novo domínio);
- o **dicionário de entidades canônicas** (pra não alucinar nomes).

O que **se mantém:** o esqueleto (ler → sintetizar com template → escrever add-only/bloco gerenciado → atualizar índice da pasta/log → idempotência por hash/slug → gate onde sensível) e a divisão determinístico (código stdlib) ↔ LLM (julgamento).

### Passo 4 — Conectar o agente (Query)
No `CLAUDE.md`/`AGENTS.md`: "ao iniciar, ler o `index.md` da raiz e descer só na área relevante; ao concluir decisão durável, atualizar a página + log". A regra "a página vence o índice" evita confiar num mapa defasado.

### Passo 5 — Ligar a curadoria (Lint)
Plugue a Camada A (saúde mecânica) e, quando o uso crescer, a Camada B (curadoria das sessões) + o despachante semanal. Ver [03](03-manutencao-e-curadoria.md), os [`scripts/`](../scripts/) e as [skills de exemplo](../examples/skills/).

### Migrar uma wiki que já existe
Ver a ordem que funcionou em [05 — Migrar uma wiki existente](05-conformidade-okf.md#migrar-uma-wiki-existente). Os scripts `wiki_frontmatter.py` (injeta `type` em lote a partir de um mapa pasta → tipo) e `wiki_index.py` (cria e sincroniza os índices) fazem o trabalho mecânico, em dry-run por padrão.

---

## Decisões de arquitetura comprovadas
- **Raw sources nunca são movidos** — a wiki é síntese, não cópia.
- **Tudo aditivo** — adicionar instância/alimentador não quebra o que já roda.
- **Markdown + git** — versionamento, histórico e colaboração de graça.
- **Editor visual é opcional** — um app com graph view (ex.: Obsidian) ajuda a enxergar a forma da wiki, mas não é obrigatório; o fluxo é terminal + agente.
- **Publicação externa em paralelo** (ex.: um Notion/site) — pode ser uma vitrine humana; a wiki é a síntese viva. Não cachear o conteúdo externo na wiki (só ponteiros).
- **Índice em dois níveis** — a raiz mapeia áreas, a pasta lista páginas. O índice único não escala, e o limite não é o número de páginas: é descrição gorda e histórico infiltrado (53.170 → 879 tokens de entrada na instância medida).
- **Índice é navegação; histórico é `log.md`** — trava escrita em quatro lugares (cabeçalho do índice, `SCHEMA.md`, skill de ingest, `AGENTS.md` do agente). O vício nasce por imitação, não por instrução, então uma camada só não segura.
- **Conformidade OKF por padrão** — toda wiki nova nasce conformante (custo: um campo `type` por página). Ver [05](05-conformidade-okf.md).
- **Wiki da própria casa pode ter "ponte"** — quando a instância cobre a empresa que a mantém, o alimentador pode propor edições nos **documentos de gestão fora da wiki**, fechando o ciclo conhecimento → execução, com três travas. Ver o [padrão](patterns/ponte-com-sistema-de-gestao.md).

---

## Teste de sucesso
Uma pessoa lê este repositório e consegue **montar uma wiki nova + plugar pelo menos um alimentador** num contexto novo, **sem perguntar nada**. Se conseguir, a documentação cumpriu seu papel.
