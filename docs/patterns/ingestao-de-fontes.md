# Padrão: Ingestão de Fontes

> Pegar uma fonte externa (link, PDF, vídeo, repositório) e transformá-la em conhecimento estruturado, persistido em **destinos com papéis distintos**: um arquivo denso (fonte de verdade), uma página de wiki (síntese viva) e, opcionalmente, uma publicação externa (vitrine humana). É o ETL de conhecimento básico do framework.

## Quando usar
Ingestão contínua de material de estudo/pesquisa: artigos, documentação, vídeos, repositórios. Uma fonte por vez, com você no controle.

## Como funciona
1. **Ingerir** a fonte com a ferramenta do tipo (extrator de PDF, de vídeo, fetch web, leitor de repo). Processar a fonte por completo antes de analisar.
2. **Inferir** título, categoria (de uma lista fixa do domínio) e slug (lowercase, sem acento, hífens).
3. **Sintetizar** num template fixo, lendo um **arquivo de contexto de domínio** para aterrar os insights em fatos reais do seu contexto (a aplicação tem de ser específica da fonte, nunca genérica).
4. **Salvar o arquivo denso** local (datado), e **validar** com um checker determinístico antes de qualquer publicação. Se reprovar, reescrever e revalidar.
5. **Ingerir na wiki** — só se for conceito/ferramenta reaproveitável (pular o que for pontual demais, pra não poluir).
6. **(Opcional) Publicar externamente** (ex.: um Notion/site) como vitrine humana.

## Saída e efeito na wiki
- **Arquivo denso** (a fonte de verdade): template fixo com resumo executivo **neutro/público**, resumo denso técnico, e aplicação/insights aterrados no domínio.
- **Página de wiki:** uma versão **destilada** em `ferramentas/<slug>.md` ou `conceitos/<slug>.md` (categoria auto-detectada). Em página existente, faz **upsert só de um bloco gerenciado** entre marcadores HTML, preservando o resto (que pode ter sido editado por humano).
- **`index.md` + `log.md`** atualizados (idempotentes).

## Idempotência
Âncora = **marcadores HTML + slug determinístico** (não hash). Reingestão substitui só o bloco gerenciado via regex; página nova vs. update decidido por existência do arquivo. `index.md` dedup pela presença do link; `log.md` dedup por assinatura.

## Gotchas / decisões de design
- **Separação público/privado é o coração:** o validador reprova o resumo executivo se citar dados privados (nomes, ferramentas internas) ou se começar técnico demais — força um resumo compartilhável.
- **Bloco gerenciado por marcadores HTML** permite a página ser co-editada por humano e re-ingerida por máquina sem conflito. Remover os marcadores faz a reingestão **anexar** (duplicação silenciosa) — não remova.
- **Defesa contra saída malformada do LLM:** se a síntese vier como objeto/JSON em vez de bullets, normalize antes de gravar.

## Essência replicável
**ETL de uma fonte para N destinos de papéis distintos** (arquivo denso imutável · wiki viva · vitrine externa), com **dupla separação**: público/neutro vs. privado/acionável (forçada por validador determinístico) e raw vs. síntese. Idempotência por **âncoras** (marcadores + slug + dedup), não por hash — permite reingestão segura e coexistência com edição humana. Para adaptar: troque o template de seções, o arquivo de contexto de domínio e os destinos.
