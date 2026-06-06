# Padrão: Documento Longo (chunking)

> Ingerir uma fonte longa (livro, relatório, curso) fatiando-a em unidades semânticas, **sintetizando cada uma isoladamente e gravando no disco antes de avançar** — depois consolidando numa síntese-mãe. O filesystem é a memória, não o contexto do LLM.

## Quando usar
Fontes grandes demais pra caber no contexto: um livro, um relatório extenso, uma transcrição longa de curso. Você quer tanto o detalhe por parte quanto a visão do todo.

## Como funciona
1. **Ler a fonte** (já em texto na pasta de origem — o padrão não baixa/converte).
2. **Extrair metadados** (título, autor, etc.) e gerar slug.
3. **Detectar unidades** (capítulos/seções) por uma cascata de padrões. Registrar a contagem antes de processar.
4. **Processar UMA unidade por vez** (nunca carregar a fonte inteira no contexto). Cada unidade gera Markdown com seções fixas (síntese · conceitos-chave · citações · aplicações no domínio) e **é salva imediatamente antes de avançar**.
5. **Consolidar** depois de todas — a síntese-mãe é gerada **a partir dos arquivos salvos, não relendo a fonte** (tese central · conceitos fundamentais · tabela de estrutura · links pras unidades).
6. **Atualizar `index.md` + `log.md`** e, opcionalmente, publicar a síntese-mãe externamente.

## Saída e efeito na wiki
- **Por unidade:** `<categoria>/<slug>/parte-NN-<slug>.md` (NN com zero à esquerda). Granularidade fina, recuperável individualmente.
- **Síntese-mãe:** `<categoria>/<slug>/index.md` — página-mãe com tabela de estrutura + links pras partes. É a candidata natural a subir pra uma publicação externa (as partes não sobem).
- **`index.md` global:** uma linha pra página-mãe.

## Idempotência
**Estado no filesystem:** cada unidade é gravada quando pronta; a síntese relê esses arquivos → tolera contexto longo e falha no meio (trabalho parcial fica salvo). Se o slug já existe, avisar e **perguntar** antes de reprocessar (não sobrescrever cego). Para fontes sem marcadores de unidade, fatiar por tamanho com overlap entre blocos.

## Gotchas / decisões de design
- **"Uma unidade por vez, salve e avance"** é a decisão central anti-estouro de contexto; a síntese lê os arquivos salvos, não a fonte.
- **Aplicação ao domínio no template** força o aterramento — adapte essas seções + o arquivo de contexto ao replicar.
- Slug é a chave de identidade em todo o sistema (pasta, arquivo, links, índice).

## Essência replicável
**Fatiar um documento longo em unidades semânticas, sintetizar cada uma isoladamente gravando no disco antes de avançar, depois consolidar as partes numa síntese-mãe.** Duplo destino: wiki granular (primária) + síntese consolidada (opcionalmente externa). Pra adaptar a qualquer fonte longa: mantenha o esqueleto fatiar→salvar→consolidar e troque o detector de unidades + o contexto de aterramento.
