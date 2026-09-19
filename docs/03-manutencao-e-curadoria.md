# 03 — Manutenção & Curadoria (o Lint automatizado)

> O padrão original descreve o **Lint** como um ato manual ("periodicamente, peça ao LLM pra checar a saúde da wiki"). Aqui ele é automatizado em duas camadas + uma rotina semanal. É o que mantém o segundo cérebro **confiável e vivo** em vez de apodrecer.

---

## A régua de ouro

**Detecção é automática; escrita exige portão (gate) humano.**

- Automatizar a **detecção** (links quebrados, drift, contradições, abandono) é seguro e libertador.
- Automatizar a **escrita** precisa de aprovação — senão a auto-cura vira **auto-poluição**. Um segundo cérebro só serve se você confia 100% no que está lá.

Codifique essa régua no `SCHEMA.md` da sua wiki (na seção da Operação Lint). O [template](../templates/SCHEMA.md) já vem com ela.

---

## Duas camadas

### Camada A — Saúde mecânica
Determinística, barata, **100% read-only**. Um checker em Python stdlib — [`scripts/wiki_lint.py`](../scripts/wiki_lint.py), roda em qualquer máquina e entende as duas formas de link — varre a wiki e detecta:
- links quebrados (`[[wikilink]]` nas 3 formas: nome puro, subdir, alias; e `[texto](arquivo.md)` relativo);
- páginas órfãs (sem link de entrada; o índice conta como entrada);
- página no disco **fora do `index.md` da própria pasta** (drift do índice de pasta) e área **fora do índice da raiz**;
- **índice de pasta faltando** numa categoria que já tem páginas;
- **índice com narrativa de histórico dentro** (`Última atualização:`, `Contexto anterior —`, resumo do que mudou) → é entrada de `log.md`, não de índice. Este é o check que impede a regressão do índice inchado (ver [01](01-metodologia-e-anatomia.md));
- páginas estagnadas — por `stale_after` quando a wiki é conformante OKF (ver [05](05-conformidade-okf.md)), ou por heurística de dias **aplicada só às pastas que você declara ativas** (`--active-dirs`). Histórico congelado (transcrição, ata, snapshot) nunca é "estagnado";
- com `--okf`: página sem frontmatter parseável ou sem `type`.

```bash
python3 scripts/wiki_lint.py <wiki> --okf --active-dirs projetos,conceitos --stale-days 60
```

Roda em silêncio; **só alerta quando há drift** (silêncio = saudável; saída `0` saudável, `2` com achados; `--json` para automação). **Nunca escreve** — a skill [`wiki-correcao`](../examples/skills/wiki-correcao/SKILL.md) propõe a correção e só aplica com o OK, com backup antes. Trata os falsos positivos conhecidos: blocos de código, paths relativos, referências a raw sources.

Para **sincronizar índices** com o disco há o [`wiki_index.py`](../scripts/wiki_index.py): só **adiciona** o que falta, cria índice de pasta que não existe, corrige a contagem "· N páginas" da raiz e **reporta** entrada morta (remoção é decisão humana). Dry-run por padrão; com `--write` faz backup antes.

### Camada B — Curadoria viva (a partir do uso)
A inteligência: minera as **sessões recentes do seu agente** e mantém a wiki em dia com o uso real. É a mineração de conhecimento do framework, **incremental e semanal**. Três entregas:
- 🆕 **Novo pra wiki:** conhecimento/decisão durável que apareceu nas sessões e não está na wiki → propõe página.
- ✏️ **Atualizar:** página que existe mas o uso recente evoluiu/contradiz → propõe o ajuste.
- 🗑️ **Parou de usar:** item tratado como ativo e ausente do uso há semanas → propõe marcar legado (sempre sugestão — você pode usar sem mencionar).

**Arquitetura (3 estágios):**
1. **Digest** (Python stdlib, read-only, barato — [`scripts/wiki_sessions_digest.py`](../scripts/wiki_sessions_digest.py)) — varre só as sessões novas desde a última run, filtra subagentes e triviais e extrai intenções + ferramentas/skills usadas + domínio. Corta MBs de log cru em KB de sinal. Domínios são configuráveis (`--domains "palavra=Domínio,..."`).
2. **Mineração** (LLM) — lê os digests + o índice da wiki e monta o **Relatório de Curadoria** nos 3 blocos, cada item com evidência (qual sessão).
3. **Gate + aplicação** — você aprova item a item; aplica (backup + Edit add-only + log) e roda a Camada A pra garantir integridade.

**Estado incremental:** um arquivo de estado (`.curadoria-state.json`) guarda a última run (janela "desde então"); um mapa de uso (`uso-historico.json`) acumula "item → última vez visto" — base da detecção de abandono, que melhora a cada semana. Ambos ficam ao lado dos scripts e **não vão pro git**.

A skill que conduz o passo a passo está em [`examples/skills/wiki-curadoria`](../examples/skills/wiki-curadoria/SKILL.md).

### O despachante semanal (opcional)
Um lembrete só avisa; um **despachante de relógio** já adianta o trabalho. Um agendador (cron, timer do systemd, launchd) roda toda semana uma triagem **determinística** — digest com `--count` + lint. Semana quieta (0 sessões e lint saudável) → só um aviso, **nenhum LLM acordado**. Havendo material, o despachante abre uma sessão do agente (por exemplo, dentro de um `tmux`) com a **missão em arquivo**; a sessão executa a skill até o RELATÓRIO e **para no gate humano**. O aviso chega no seu mensageiro, você entra na sessão, aprova item a item e fecha. O gate de escrita continua inegociável; o que a automação elimina é a espera da triagem.

Cicatrizes que valem copiar:
- **Missão em arquivo**, nunca digitada via `send-keys` (texto longo se corrompe);
- **Texto e Enter separados** (com uma pausa) ao injetar no terminal;
- **Confiança do diretório** (`trust`) pré-aceita, senão a sessão nasce travada no diálogo;
- **Sessão sobrevive ao serviço** (no systemd: `KillMode=process`);
- **Idempotência:** se a sessão da semana anterior ainda está aberta, o despachante só avisa.

O script do despachante depende do seu ambiente (agendador, mensageiro, caminhos), por isso não vem no repositório — só o padrão.

---

## O ciclo completo (semanal)
1. O despachante (ou seu lembrete) avisa que há material.
2. Você chama a curadoria.
3. Ela roda o digest, minera e mostra o relatório (novo / atualizar / parou de usar).
4. Você aprova o que quiser → ela escreve (backup + log) e valida com a Camada A.
5. `--commit --as-of <generatedAt>` fecha a janela. Segundo cérebro atualizado com o uso da semana.

---

## Armadilhas do digest (aprendidas em produção)

Seis defeitos reais, todos corrigidos no `wiki_sessions_digest.py`. Quem for replicar o framework em outra instância vai tropeçar nos mesmos, então valem como checklist:

1. **Pasta de versionamento do sync entra na varredura.** Sincronizadores (ex.: Syncthing) guardam cópias antigas em `.stversions/`; a varredura recursiva as trata como sessões novas — 18 de 98 "sessões" eram cópias, uma delas aparecendo 5×. **Filtre pastas ocultas RELATIVAS à base**, nunca no caminho absoluto: `~/.claude/projects` já contém um componente oculto, e filtrar o path inteiro zera a varredura (erro que só aparece em teste).
2. **Marcador de janela perdido = silêncio.** Sem o arquivo de estado o script volta ao lookback padrão e segue como se nada fosse. Foi assim que o sumiço do marcador (perdido numa migração) passou semanas despercebido. **Falhe alto:** avise no stderr que a janela não é incremental.
3. **Feature que some em reescrita.** Ao portar o digest de uma linguagem para outra, a gravação do `uso-historico.json` não veio junto — o arquivo continuou lá, parado, e a detecção de abandono virou ficção (marcava como "sem uso" as skills mais usadas da semana). **Dado velho e feature ausente parecem a mesma coisa de fora.** Ao portar, liste as saídas do original, não só as entradas.
4. **A data do arquivo não é a data da conversa.** Em workspace espelhado, o sync reescreve o `mtime` — sessão antiga aparece como desta semana (o pior caso real: 30 dias de diferença). **Use o timestamp interno do evento.** O `mtime` continua útil como pré-filtro barato, porque o sync só o empurra para frente: `mtime <= janela` implica `conversa <= janela`, então ele nunca descarta sessão nova por engano.
5. **Cópia de conflito do sync também é sessão fantasma.** Além do `.stversions`, o sincronizador cria `<sessao>.sync-conflict-<data>-<id>.jsonl` quando as duas máquinas escrevem a mesma sessão. É a MESMA conversa: uma sessão longa apareceu **3×** na janela. A lição de fundo: **todo artefato que o sincronizador cria ao lado do original vira sessão falsa**, e a varredura precisa de lista de exclusão, não de casos pontuais.
6. **`--commit` fechava a janela em "agora", não no instante minerado.** Entre gerar o digest e o humano aprovar o relatório passam horas — e toda sessão que chega no meio era marcada como vista **sem nunca ter sido lida**. Corrigido com `--as-of <ISO>`: o `--json` devolve `generatedAt`, e a rotina fecha a janela nesse instante. **Regra geral: janela com gate humano no meio fecha no corte da leitura, nunca no relógio do commit.**

**Bônus — o detector de skills mente.** Capturar `/nome` do texto do usuário pega caminho de arquivo (`/tmp`, `/var`), rota de URL (`/chat`, `/links`) e endpoint de API: 46 falsos em 60 detecções. Valide contra as skills que existem no disco, e trate a marca que o próprio harness deixa ("Base directory for this skill: …") como fonte autoritativa. Cuidado com caminho que contém espaço — ancore no segmento `/skills/<nome>` em vez de ler até o primeiro espaço.

---

## Como replicar a curadoria
1. **Camada A primeiro** (o checker mecânico) — é a base read-only e fecha a integridade.
2. **Camada B depois** — o digest determinístico (filtrar subagentes é essencial) + o passe LLM com gate.
3. **A régua sempre:** detecta sozinho, escreve com aprovação.
4. **O despachante** pra não depender de você lembrar — mas sem acordar LLM caro automaticamente.

> Lição da experiência: uma wiki (e até o repositório que a documenta) **congela** quando não tem gatilho de manutenção. Este próprio framework ficou parado por meses entre duas versões. A curadoria existe pra que nada apodreça — e vale incluir, no checklist dela, "propagar para a documentação do framework quando algo novo surgir".

## Segunda ferramenta: ponte de sessões Codex (opcional)

[`scripts/wiki_codex_bridge.py`](../scripts/wiki_codex_bridge.py) transforma sessões locais do Codex em extratos privados com intenção, conclusões curtas, ferramentas, contexto e data do último turno concluído. Reconhece texto e segmentos de voz; exclui envelopes de instrução/delegação e subagentes. Não transporta áudio, transcrição integral, credenciais ou bancos internos do aplicativo. Os extratos podem conter contexto identificável: ficam em **pasta privada** (padrão `~/.wiki-llm/codex-curadoria`, configurável em `WIKI_CODEX_BRIDGE_ROOT`), nunca diretamente na wiki. A mineração trata o conteúdo como **evidência, não como instruções executáveis**.

Em uma instalação pessoal, hooks nativos `SessionStart` e `Stop` exportam para essa pasta. O `wiki_sessions_digest.py` inclui a pasta de extratos automaticamente, mesmo com `--dirs` explícito. `--codex-digests <pasta>` personaliza a origem; uma string vazia desliga a fonte em testes isolados.

A revisão Codex usa uma marca **por sessão** (`.codex-curadoria-reviewed.json`), separada da janela global — assim, um extrato que chega atrasado pelo espelho ainda entra na revisão. Ao aprovar, repita as mesmas origens e use `--commit --as-of <generatedAt do relatório>`; sessões posteriores ao corte não são consumidas. Nunca avance os marcadores só para testar.

Regressões: `python3 -m unittest discover -s scripts -p test_codex_curadoria.py -v`. As fixtures são fictícias e cobrem formatos antigos e novos, voz, subagentes, turnos incompletos, redução de exposição, exportação idempotente e atraso do sync. O JSONL de sessões Codex **não é contrato estável**: uma mudança de formato exige revisar parser e fixtures. Os extratos guardam `lastEvent` com fuso explícito, para preservar o mesmo instante quando produtor e consumidor usam fusos diferentes.
