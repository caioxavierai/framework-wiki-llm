# Padrão: Ingestão em Lote (headless)

> A variante **industrial** da ingestão de fontes: um runner em lote dirige um worker LLM que só produz **JSON com schema fixo**; scripts determinísticos renderizam, validam e distribuem o resultado para os destinos. É o padrão de ingestão em escala, sem humano no loop.

## Quando usar
Processar muitas fontes de uma vez, de forma agendada/automática (ex.: um feed de novidades, uma lista de itens). O volume inviabiliza revisar item a item — a robustez tem de vir do desenho, não da supervisão.

## Como funciona
1. O **runner** é dono do lote; para cada item, passa o conteúdo + um **arquivo de contexto** (os eixos do seu domínio).
2. O **worker LLM** produz um **JSON estrito** (schema fixo).
3. Um script determinístico **renderiza** o JSON → Markdown canônico.
4. Outro script **valida** o Markdown (gate; falha com código de erro se reprovar).
5. Salva o arquivo denso, distribui pros destinos (wiki, publicação externa).
6. **Sem notificação por item** — só um resumo final do lote.

## Saída e efeito na wiki
- **Contrato JSON** com campos fixos (título, slug, categoria, resumo público, resumo denso, aplicação, insights, confiança). Regras embutidas: campos obrigatórios, mínimo de itens por lista, resumo público sem dados privados.
- **Markdown** renderizado nas seções canônicas.
- **Wiki:** mesmo ingester do padrão de ingestão de fontes (upsert de bloco gerenciado + índice da pasta/log idempotentes).

## Idempotência e robustez
- **Falha isolada** por item não derruba o lote.
- **Retry segmentado por estágio** (a peça-chave): se a publicação externa falhou depois do Markdown, retoma só dela; se a wiki falhou, retoma só da ingestão — sem refazer os estágios anteriores.
- Idempotência nos destinos: Markdown regerado do JSON; wiki só atualiza o bloco gerenciado; índice só insere link inédito.

## Gotchas / decisões de design
- **JSON estrito** porque o output é consumido por máquina (render + validate), não por humano — elimina parsing frágil de Markdown livre e habilita o retry segmentado.
- **Validação em camadas:** valida o payload na geração (campos, contagens) e o produto final (seções, marcadores proibidos). Defesa em profundidade contra LLM desobediente.
- **Eixos de contexto** (os ângulos pelos quais cada item é analisado) são estruturais — é o que transforma "processei N itens" em "o que cada um muda no meu contexto".
- **Sem dependências externas no caminho crítico** — CLI/HTTP direto dá robustez ao batch.

## Essência replicável
**Um runner em lote dirige um worker LLM que só produz JSON de schema fixo; scripts determinísticos (stdlib) renderizam, validam e distribuem para N destinos.** Robustez por **retry segmentado por estágio**, **idempotência por bloco-gerenciado/dedup** e **gates de validação em camadas**. Pra adaptar a outro domínio/escala: troque o arquivo de contexto (eixos) e o schema JSON — o motor render/validate/distribui é agnóstico. É a ingestão de fontes "sem humano", trocando síntese livre por contrato JSON validável.
