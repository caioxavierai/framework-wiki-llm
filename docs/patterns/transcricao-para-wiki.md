# Padrão: Transcrição → Wiki

> Transformar a transcrição bruta de uma reunião em memória estruturada na wiki, propagando as decisões para as páginas afetadas — com **checkpoint humano antes de gravar** e **idempotência por hash do conteúdo**. É o caso "wiki de time alimentada por transcrições, com humanos no loop" do padrão original.

## Quando usar
Reuniões recorrentes cujo conteúdo precisa virar memória durável: 1:1s, reuniões de projeto, calls de cliente. A fonte é **ruidosa e sensível** (nomes corrompidos pela transcrição automática, dados de pessoas) — por isso o gate humano é central.

## Duas abordagens (escolha pela natureza da fonte)

**A) Determinística-pesada** (quando você quer citações programáticas e roteamento por categoria):
1. **Parse + chunking** (script): normaliza turnos (timestamp, speaker, texto), calcula **hash só do conteúdo** (ignora formatação) e agrupa em **chunks de ~500 tokens, sem cortar fala no meio, com overlap** — cada chunk citável.
2. **Pré-classificação determinística** (script): tags multi-label por categoria do domínio, usando keywords/heurísticas + um dicionário de **entidades canônicas** (pra não alucinar nomes). Produz pistas, não verdade.
3. **Curadoria pelo LLM:** o agente lê os chunks (com as tags como pista) e escreve o índice da sessão + o roteamento final por categoria, confirmando/corrigindo o classificador.
4. **Dupla persistência:** um **snapshot imutável por sessão** (o que aquela reunião trouxe daquela categoria, nunca mistura sessões) + um **curado Edit-progressivo** (a verdade atual; contradição é marcada com data, nunca apagada).

**B) Julgamento-puro** (quando basta prosa curada, sem código):
1. O agente lê a transcrição + o contexto canônico da wiki (índice, schema, log recente).
2. **Classifica** tema, entidades, decisões e as páginas-alvo.
3. **Checkpoint humano (obrigatório):** apresenta o entendimento curado + a decodificação de ruído (o que decifrou e o que **não** conseguiu — nunca afirmar palpite como fato) + o plano de destinos, e **espera o OK**. Perguntas só pros gatilhos reais (cauda operacional, conteúdo sensível, página nova, ambiguidade).
4. **Grava** a síntese + propaga pras páginas via **Edit add-only**; omissões deliberadas vão pro log (auditáveis — "sem corte silencioso").

## Saída e efeito na wiki
- **Síntese da reunião** numa página datada.
- **N páginas-tópico** atualizadas via **Edit add-only** (nunca apaga; contradição vira nota datada).
- **`index.md`** (quando cria página) e **`log.md`** (com o hash, e as omissões nas Notas).

## Idempotência
**Hash do conteúdo (ex.: SHA-1) + o log como registro:** hash ausente → `append`; hash visto → `replace` (sobrescreve a síntese, substitui a entrada in-place, marca "reprocessada"). Rodar duas vezes não duplica. Hash só do conteúdo (não da formatação) desacopla a idempotência de mudanças cosméticas.

## Gotchas / decisões de design
- **Checkpoint humano é o que separa "wiki que envenena" de "segundo cérebro confiável":** classificar é autônomo, **gravar nunca é**.
- **Dicionário de entidades canônicas anti-alucinação:** nunca inferir nome próprio de transcrição ruidosa; tratar como dúvida e confirmar.
- **Snapshot imutável vs. curado Edit-progressivo:** o snapshot preserva fidelidade histórica por sessão; o curado mantém a verdade atual; a tensão se resolve **marcando** contradições, nunca apagando.
- **Privacidade:** mascarar dados de pessoas na síntese (preservar no raw); a wiki pode ser lida por outros.
- **Determinístico + LLM:** o código dá recall barato e reproduzível (parse, chunk, classificação); o LLM entra só pra precision e julgamento.

## Essência replicável
Ingestão de transcrição vira **memória multi-destino** quando, além da síntese, propaga decisões pras páginas-tópico via **Edit add-only**, com **idempotência por hash + log**. O diferencial é o **gate humano antes de gravar** + dicionário canônico contra alucinação + "sem corte silencioso". Replica pra qualquer domínio trocando a **taxonomia de categorias** e o **dicionário de entidades**; escolha a abordagem A (com código, citações programáticas) ou B (só prosa + checkpoint) conforme a necessidade.
