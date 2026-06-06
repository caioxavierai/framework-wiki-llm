# 04 — Replicação

> O framework não é uma wiki só — é um **padrão multi-instância**. Aqui estão casos de uso típicos e o guia passo-a-passo pra montar uma wiki nova do zero.

---

## Casos de uso (a mesma anatomia, contextos diferentes)

| Caso | Fontes (raw) | Categorias típicas | Quem lê |
|---|---|---|---|
| **Pessoal / segundo cérebro** | artigos, repos, vídeos, livros que você estuda | ferramentas, conceitos, projetos | você + seus agentes |
| **Por cliente / por projeto** | transcrições de reunião, documentos do cliente | as dimensões do diagnóstico daquele cliente | a equipe que atende o cliente |
| **Time interno** | transcrições, decisões, documentos de projeto | áreas/processos do time | o time, com você no portão da curadoria |

**O que elas têm em comum:** a mesma anatomia (SCHEMA/CLAUDE/index/log + categorias + formato de página + wikilinks), as 3 operações (Ingest/Query/Lint) e a régua de curadoria. **O que muda entre elas:** as fontes brutas, as categorias (dimensões do domínio) e quais alimentadores estão plugados.

> Se você roda várias instâncias, defina a hierarquia: uma wiki pode ser canônica de ecossistema e as outras satélites. Conhecimento de ecossistema vai na canônica; a satélite só linka, não duplica.

---

## Guia de replicação — montar uma wiki nova do zero

### Passo 1 — Infraestrutura (anatomia)
Copie os [`templates/`](../templates/) pra pasta da nova wiki e adapte:
- `SCHEMA.md` — o contrato (ajuste as categorias ao domínio).
- `CLAUDE.md` (ou `AGENTS.md`) — instrução do agente.
- `index.md` — mapa vazio, com as seções de categoria do domínio.
- `log.md` — vazio, com o cabeçalho.
- Subpastas = as **categorias do domínio**.

### Passo 2 — Definir as fontes brutas
Onde vivem os raw sources (artigos, transcrições, docs) — **imutáveis**, a wiki nunca os altera.

### Passo 3 — Plugar os alimentadores (Ingest)
Escolha quais [padrões de alimentador](02-alimentadores.md) fazem sentido e adapte. O que **muda** ao replicar:
- o **arquivo de contexto de domínio** (o aterramento dos insights);
- as **categorias** (dimensões do novo domínio);
- o **dicionário de entidades canônicas** (pra não alucinar nomes).

O que **se mantém:** o esqueleto (ler → sintetizar com template → escrever add-only/bloco gerenciado → atualizar index/log → idempotência por hash/slug → gate onde sensível) e a divisão determinístico (código stdlib) ↔ LLM (julgamento).

### Passo 4 — Conectar o agente (Query)
No `CLAUDE.md`/`AGENTS.md`: "ao iniciar, ler o `index.md`; ao concluir decisão durável, atualizar a página + log". A regra "a página vence o índice" evita confiar num mapa defasado.

### Passo 5 — Ligar a curadoria (Lint)
Plugue a Camada A (saúde mecânica) e, quando o uso crescer, a Camada B (curadoria das sessões) + o lembrete agendado. Ver [03](03-manutencao-e-curadoria.md) e os [scripts de exemplo](../examples/scripts/).

---

## Decisões de arquitetura comprovadas
- **Raw sources nunca são movidos** — a wiki é síntese, não cópia.
- **Tudo aditivo** — adicionar instância/alimentador não quebra o que já roda.
- **Markdown + git** — versionamento, histórico e colaboração de graça.
- **Editor visual é opcional** — um app com graph view (ex.: Obsidian) ajuda a enxergar a forma da wiki, mas não é obrigatório; o fluxo é terminal + agente.
- **Publicação externa em paralelo** (ex.: um Notion/site) — pode ser uma vitrine humana; a wiki é a síntese viva. Não cachear o conteúdo externo na wiki (só ponteiros).

---

## Teste de sucesso
Uma pessoa lê este repositório e consegue **montar uma wiki nova + plugar pelo menos um alimentador** num contexto novo, **sem perguntar nada**. Se conseguir, a documentação cumpriu seu papel.
