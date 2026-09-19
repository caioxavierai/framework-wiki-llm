# Padrão: Ponte com o Sistema de Gestão

> Quando a wiki é **da própria empresa**, guardar conhecimento não basta: o valor aparece quando o Ingest **conversa com o sistema de gestão**. Além de sintetizar a reunião e propagar nas páginas de área (como no padrão [Transcrição → Wiki](transcricao-para-wiki.md)), o alimentador **propõe edições em documentos que vivem fora da wiki** — roadmap de execução, log de decisões, registro de ritos. É o Ingest fechando o ciclo *conhecimento → execução*.

## Quando usar
A reunião **move a execução**, não só o conhecimento: diretoria, planejamento, rituais de gestão, comitês. Se a wiki é de um cliente ou de um domínio pessoal, **não use** — não há sistema de gestão da casa para alimentar.

## O fluxo

1. **Passo 0 — helper determinístico, read-only** (script stdlib): resolve o arquivo (caminho, nome ou "a mais recente"), valida, detecta o **formato** da transcrição, extrai metadados do cabeçalho, calcula o **hash** do conteúdo, decide **append × replace** contra o log e **mapeia o terreno** — áreas da wiki com suas páginas, últimas entradas do log e um **snapshot do sistema de gestão** (seções do roadmap, lista de decisões numeradas + próximo número, últimas entradas do diário, ritos, estado do git, em qual máquina está rodando). Emite um JSON.
2. **Ler tudo, em páginas.** A ferramenta de leitura trunca arquivos longos (uma hora de reunião ≈ 48 mil tokens): a skill exige ler até o fim e proíbe sintetizar a partir da primeira página. Lê também o `SCHEMA.md`, só as páginas candidatas a destino, o glossário de entidades e os trechos necessários do log de decisões.
3. **Classificar (autônomo):** tema e áreas · tipo (inclusive **se a reunião é um rito de gestão**, e qual) · entidades pelo glossário · decisões, ações e bloqueios · **sensibilidade** · páginas-alvo · **e a ponte** (carimbo de rito, movimentos de execução, entrada de diário, evidência de hipótese).
4. **Checkpoint no chat** (padrão): entendimento · decodificação de ruído · estratégico × cauda operacional · nível de sensibilidade e o que **não** entra · plano da wiki · **plano da ponte como pré-visualização de diff** · perguntas de gatilho (só as reais) · gate. Sem corte silencioso.
5. **Gravar, nesta ordem:** síntese (template com uma seção **"Ponte pro planejamento"**) → páginas via Edit add-only → **regenerar os índices** com o script do framework → aplicar a ponte aprovada → append idempotente no log → lint.

## Saída e efeito
- **Síntese** com frontmatter OKF (`type: Transcrição`, tema, tipo, nível de acesso quando for reservada) e uma tabela **Ponte pro planejamento** registrando o que foi levado, o que foi recusado e o estado do commit.
- **N páginas de área** por Edit add-only; contradição vira nota datada.
- **Índices regenerados** (nunca editados à mão) + **`log.md`** com fonte, hash, páginas tocadas, decisões, ponte e **Notas de omissão**.
- **Fora da wiki:** edições cirúrgicas nos documentos de gestão, **só do que foi aprovado**.

## Idempotência
**Hash do arquivo + `log.md`**: hash novo → append; hash visto → replace (regrava a síntese, substitui a entrada, **não re-propaga**).

## As três travas da ponte (é aqui que mora o risco)

1. **Nunca decidir pelo humano.** A skill não cria decisão numerada; propõe "candidata a decisão" e quem numera é a pessoa.
2. **Commitar só o que tocou.** Nunca `git add -A`. Se o próprio alvo já estiver modificado por outra sessão, **não commita** — marca pendência.
3. **Não usar git onde não há git.** Pasta sincronizada entre máquinas costuma excluir o `.git`. Naquele ambiente a skill edita e registra "commit pendente".

## Gotchas / decisões de design
- **Diário é cronológico, não append.** Entrada retroativa entra na posição da data. Um backfill que anda para trás no tempo exige reordenar.
- **Glossário de entidades é obrigatório.** Nome que não bate com o glossário não é inferido: vira item de checkpoint, e a confirmação volta para o glossário com data (ver o exemplo do "handoff" em [02](../02-alimentadores.md)).
- **Nome de arquivo com acento:** o sistema de arquivos pode guardar em NFD enquanto o chat envia NFC — normalize (NFC + casefold) ao buscar por nome.
- **Uma gravação pode virar dois arquivos** (recortes de temas distintos): não é duplicata; cada um vira uma síntese, com link cruzado.
- **Dois níveis de confidencialidade** no frontmatter + uma lista curta do que **nunca** entra (remuneração individual, candidato, valuation em número, juízo sobre pessoa). Isso mantém neutras as páginas de área mesmo quando a reunião era reservada: o conteúdo útil circula, o sensível fica na síntese marcada.
- **Flags úteis:** `--seco` (dry-run, para antes do checkpoint) · `--auto` (pula o checkpoint com defaults conservadores **e restringe a ponte ao diário**) · `--so-wiki` (desliga a ponte).
- **O que a skill NÃO toca:** raw sources, outras wikis, documentos sensíveis do planejamento (valuation, planilha financeira, recrutamento).

## Essência replicável
*Síntese → propagação → **ponte proposta** → gate → escrita cirúrgica.* Três travas impedem a ponte de virar dano: **não decidir pelo humano**, **não commitar o que não é seu** e **não usar git onde o git não existe**. O resto do esqueleto é o de sempre — hash como idempotência, add-only, índice regenerado, log com as omissões auditáveis.
