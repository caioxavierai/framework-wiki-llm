# scripts/

Ferramentas do framework. **Python 3, só biblioteca padrão** — nada de `pip install`, roda em qualquer máquina.

**A régua:** detecta sozinho, escreve com gate. Só `wiki_new.py`, `wiki_index.py` e `wiki_frontmatter.py` escrevem, e os dois últimos só com `--write` (sem ele é dry-run). O resto é somente leitura.

| Script | O que faz | Exemplo |
|---|---|---|
| `wiki_new.py` | Cria uma wiki nova a partir dos [templates](../templates/), já no formato de dois níveis e conformante com OKF. Nunca sobrescreve. | `python3 scripts/wiki_new.py ~/minha-wiki --nome "Pessoal" --categorias "ferramentas:o que uso;conceitos:ideias"` |
| `wiki_lint.py` | **Camada A** — saúde da wiki (read-only): links quebrados, órfãs, índice fora de sincronia, narrativa infiltrada em índice, páginas estagnadas, conformidade OKF. Sai com 0 se saudável, 2 se há achados. | `python3 scripts/wiki_lint.py ~/minha-wiki --okf` |
| `wiki_index.py` | Sincroniza os índices com o disco: adiciona página que falta, cria índice de pasta que falta, corrige a contagem "· N páginas". Nunca reescreve descrição existente. Dry-run por padrão; com `--write`, faz backup `.bak-<ts>` antes. | `python3 scripts/wiki_index.py ~/minha-wiki --write` |
| `wiki_frontmatter.py` | Injeta o frontmatter OKF (`type`, `title`, `description`) em lote numa wiki que já existe, derivando o `type` da pasta. Não altera o corpo. Dry-run por padrão. | `python3 scripts/wiki_frontmatter.py ~/minha-wiki --map "ferramentas=Ferramenta,conceitos=Conceito" --write` |
| `wiki_sessions_digest.py` | **Camada B, estágio 1** — digest barato das sessões novas do seu agente (intenções, ferramentas, skills), desde a última curadoria. Read-only sobre as sessões. | `python3 scripts/wiki_sessions_digest.py --json` |
| `wiki_codex_bridge.py` | Opcional. Exporta extratos privados de sessões do Codex para o digest incluir. Só com `WIKI_CODEX_BRIDGE_ROOT` ou o padrão `~/.wiki-llm/codex-curadoria` (pasta `0700`). | `python3 scripts/wiki_codex_bridge.py` |
| `test_codex_curadoria.py` | Testes do digest e da ponte (fixtures fictícias). | `python3 -m unittest discover -s scripts -p test_codex_curadoria.py -v` |

## Fechar a janela da curadoria

O digest guarda a última run e sabe só o que veio depois dela. Ao aprovar o relatório, feche a janela **no instante em que o digest foi gerado**, não em "agora":

```bash
python3 scripts/wiki_sessions_digest.py --commit --as-of "<generatedAt do --json aprovado>"
```

Para separar as sessões por assunto, passe regras de domínio: `--domains "cliente-a=Cliente A,interno=Interno"` (a palavra é buscada no caminho da sessão).

## Estado local (não vai pro git)

A curadoria cria três arquivos **ao lado dos scripts**: `.curadoria-state.json` (última run), `uso-historico.json` (item → última vez visto, base da detecção de abandono) e `.codex-curadoria-reviewed.json` (marca por sessão Codex). São específicos de quem roda e estão no `.gitignore`.
