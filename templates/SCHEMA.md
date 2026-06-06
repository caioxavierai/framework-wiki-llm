# SCHEMA.md — Como Operar esta Wiki

> Contrato operacional da wiki. Toda IA que tocar este diretório deve ler este arquivo primeiro.
> *(Template do LLM Wiki Framework — adapte as categorias ao seu domínio e apague estas notas.)*

---

## O que é esta Wiki

Uma base de conhecimento viva mantida por LLM. Não é um repositório de documentos brutos — é uma **camada de síntese** que cresce e se interliga com o tempo. Cada nova fonte ingerida fortalece o que já existe; cada consulta pode virar uma página.

---

## Estrutura

```
wiki/
├── SCHEMA.md      ← este arquivo
├── CLAUDE.md      ← instrução para o agente
├── index.md       ← mapa de navegação por categoria
├── log.md         ← histórico append-only
└── <categorias>/  ← uma pasta por dimensão do domínio (ex.: ferramentas, conceitos, projetos, entidades)
```

**Fontes brutas (não pertencem à wiki):** ficam fora, imutáveis. A wiki sintetiza, não copia.

---

## Convenções de arquivo
- Nomes em **kebab-case** minúsculo, sem acentos.
- **Um conceito = um arquivo.** Nada de `notas.md`/`misc.md`. Nomes descritivos.
- **Sem fluff** — cada frase carrega informação.
- **Links internos `[[arquivo]]`** conectam páginas relacionadas (cria o grafo).
- **Não duplicar:** se já existe, linkar.
- **Atualizar, não substituir:** nova fonte sobre tema existente atualiza a página; contradição é marcada com data, o histórico não é apagado.
- **A página vence o índice:** se o `index.md` diverge da página real, a página é a verdade.

---

## Operação: Ingest
1. Identificar o tipo da fonte e a categoria.
2. Verificar se já existe página — se sim, atualizar preservando; se não, criar.
3. Criar links internos pras páginas relacionadas.
4. Atualizar `index.md` se criou página.
5. Registrar em `log.md`.

> Uma fonte pode tocar várias páginas. Privacidade: o que outros leem é neutro, sem dados sensíveis.

## Operação: Query
1. Ler `index.md` pra achar páginas relevantes.
2. Ler as páginas, sintetizar com citações.
3. **Boa resposta que revela insight novo → vira página.** Explorações compõem.

## Operação: Lint
Revisão de saúde da wiki, em duas camadas:

**Mecânica (automática, read-only):** wikilinks quebrados · páginas órfãs · `index.md` dessincronizado · header de data defasado · páginas estagnadas. Roda em silêncio; só alerta em drift. Detecção é automática; **correções de escrita passam por aprovação humana** (o lint aponta, não reescreve sozinho).

**Semântica (sob demanda):** conceitos citados sem página própria · contradições entre páginas.

Registrar o resultado em `log.md`.

---

## index.md e log.md
- **index.md:** organizado por categoria; uma linha por página (`- [[arquivo]] — resumo`). Atualizar a cada página criada.
- **log.md:** append-only, **nunca deletar entradas**. Formato:
  ```
  ## AAAA-MM-DD — [tipo: ingest | query | lint | projeto]
  - Fonte: [nome ou URL]
  - Páginas criadas/atualizadas: [lista]
  - Notas: [opcional]
  ```

## O que NÃO fazer
- Não mover/alterar as fontes brutas.
- Não copiar conteúdo bruto pra wiki — só síntese e contexto.
- Não criar páginas genéricas demais — preferir granularidade.
- Não apagar entradas do `log.md`.
