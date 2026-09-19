#!/usr/bin/env python3
"""wiki_sessions_digest.py — Estágio 1 da Camada B (curadoria): digest das sessões novas.

Varre sessões .jsonl novas desde a última curadoria, filtra triviais/subagentes e
extrai: intenções do usuário + tools usadas. READ-ONLY sobre as sessões; o estado
fica em .curadoria-state.json AO LADO DESTE SCRIPT (numa pasta sincronizada, a janela
de curadoria é UMA, compartilhada entre as máquinas).

  python3 wiki_sessions_digest.py [--dirs d1,d2] [--json | --count] [--commit] [--lookback-days 7]
                                  [--as-of <ISO>] [--domains "palavra=Dominio,..."]
Default de dirs: ~/.claude/projects.

Lições incorporadas (cada uma nasceu de um defeito real em produção):
  1. Pasta oculta entra na varredura: o sincronizador guarda versões antigas em
     `.stversions/` e cópias de conflito como `<sessao>.sync-conflict-<data>-<id>.jsonl`.
     São a MESMA conversa — sem exclusão, ela entra 2-3x na janela. A exclusão é
     RELATIVA à base: o caminho absoluto de `~/.claude/projects` já contém `.claude`,
     então filtrar oculta no path inteiro zera a varredura.
  2. Marcador de janela perdido = silêncio. Sem `.curadoria-state.json` o script cai no
     lookback padrão; agora avisa no stderr (falhe alto: a janela não é incremental).
  3. `uso-historico.json` (detecção de abandono) precisa ser escrito pelo `--commit`.
     Numa reescrita de linguagem a feature se perdeu e o arquivo ficou parado — dado
     velho e feature ausente parecem a mesma coisa de fora. Reimplementada: grava a
     última data vista de cada tool/skill/domínio.
  4. A data do arquivo NÃO é a data da conversa: o sync reescreve o mtime ao espelhar.
     A data vem do timestamp interno do evento; o mtime segue como pré-filtro barato
     (é sempre >= a data real, então nunca descarta sessão nova por engano) e fallback.
  5. `--commit` fecha a janela no instante MINERADO, não em "agora": entre gerar o
     digest e aprovar o relatório passam horas. Use `--as-of <generatedAt do --json>`;
     sessão que chega no meio não pode ser marcada como vista sem ter sido lida.
"""
import argparse, datetime, json, re, sys
from pathlib import Path
from wiki_codex_bridge import BRIDGE_ROOT, load_digests, parse_codex

STATE = Path(__file__).parent / ".curadoria-state.json"
USO = Path(__file__).parent / "uso-historico.json"
CODEX_REVIEWED = Path(__file__).parent / ".codex-curadoria-reviewed.json"
MIN_USER_MSGS, MAX_INTENT = 2, 280
DRIFT_ALERT_DAYS = 2  # divergência data-real × mtime que vira aviso

def clean(s):
    s = re.sub(r"<[^>]+>[\s\S]*?</[^>]+>", "", s)
    return re.sub(r"\s+", " ", s).strip()

def to_local(ts: str):
    """ISO-8601 do evento (normalmente UTC com Z) → datetime naive local, comparável com `since`."""
    try:
        dt = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None
    return dt.astimezone().replace(tzinfo=None) if dt.tzinfo else dt

# skill aparece como "Base directory for this skill: <path>".
# Ancorar no segmento /skills/<nome> em vez de pegar o path inteiro: há caminhos COM ESPAÇO
# ("~/Library/Application Support/...") em que um \S+ para no espaço e captura "Application".
SKILL_ANCHORED = re.compile(r"Base directory for this skill:.*?/skills/([A-Za-z0-9][\w.\-]*)")
SKILL_DIR = re.compile(r"Base directory for this skill:\s*(\S+)")  # fallback (path sem /skills/)
# ...e como slash-command digitado pelo usuário: /nome ou /plugin:nome
SLASH = re.compile(r"(?:^|\s)/([a-z][a-z0-9-]{1,40}(?::[a-z][a-z0-9-]{1,40})?)\b")

def _installed_skills():
    """Nomes de skills existentes no disco — usado para validar o que o regex de slash acha.

    Sem isso o `/nome` captura caminho de arquivo (/tmp, /var, /private), rota de URL
    (/chat, /links, /config) e endpoint de API (/observations, /promotions): na varredura
    de 25/08 foram 46 falsos em 60 detecções. A checagem contra o disco derruba isso a zero.
    Se as pastas não existirem (outra máquina), só a detecção por "Base directory" vale —
    degrada para menos cobertura, nunca para dado sujo.
    """
    names = set()
    for d in (Path.home() / ".claude/skills", Path.home() / ".claude/plugins/cache"):
        if not d.is_dir(): continue
        for f in d.rglob("SKILL.md"):
            names.add(f.parent.name)
        if d.name == "skills":
            names |= {p.name for p in d.iterdir() if p.is_dir()}
    return names

SKILLS_OK = _installed_skills()

def skills_from(text: str):
    out = set()
    anchored = SKILL_ANCHORED.findall(text)    # fonte autoritativa: o próprio harness disse
    out |= set(anchored)
    if not anchored:                           # fallback: path que não passa por /skills/
        for p in SKILL_DIR.findall(text):
            parts = [x for x in p.rstrip("/").split("/") if x]
            if parts:
                out.add(parts[-1])
    for m in SLASH.findall(text):              # fonte ruidosa: só passa se a skill existe
        if not SKILLS_OK or m.split(":")[-1] in SKILLS_OK:
            out.add(m)
    return out

# Regras (substring do caminho/cwd, minúscula → domínio). Vazia por padrão; preencha aqui
# ou via --domains. Ex.: [("cliente-a", "Cliente A"), ("interno", "Interno")]. A 1ª que casar vence.
DOMAIN_RULES: list[tuple[str, str]] = []

def domain_of(rel_path: str):
    p = rel_path.lower()
    for needle, domain in DOMAIN_RULES:
        if needle in p: return domain
    return "geral"

def parse(path: Path):
    intents, tools, skills, stamps = [], set(), set(), []
    for line in path.read_text(encoding="utf-8", errors="ignore").split("\n"):
        if not line.strip(): continue
        try: ev = json.loads(line)
        except ValueError: continue
        if ev.get("type") == "session_meta":
            return parse_codex(path)
        ts = ev.get("timestamp")
        if isinstance(ts, str):
            d = to_local(ts)
            if d: stamps.append(d)
        role = ev.get("type")
        if role == "message":  # formato com evento `message` aninhado
            role = (ev.get("message") or {}).get("role")
        if role == "user":
            c = (ev.get("message") or {}).get("content")
            raw = c if isinstance(c, str) else " ".join(
                b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text") if isinstance(c, list) else ""
            t = clean(raw)
            if t:
                intents.append(t[:MAX_INTENT])
                skills |= skills_from(t)
        elif role == "assistant":
            c = (ev.get("message") or {}).get("content")
            if isinstance(c, list):
                for b in c:
                    if isinstance(b, dict) and b.get("type") in ("tool_use", "toolCall") and b.get("name"):
                        tools.add(b["name"])
    if len(intents) < MIN_USER_MSGS: return None
    return {"intents": intents, "tools": sorted(tools), "nUser": len(intents),
            "skills": sorted(skills), "lastEvent": max(stamps).isoformat() if stamps else None}

def bump(hist: dict, key: str, day: str):
    """Guarda sempre a data MAIS RECENTE já vista (o histórico é 'última vez', não 'última escrita')."""
    if day > hist.get(key, ""):
        hist[key] = day

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dirs", default=str(Path.home() / ".claude/projects"))
    ap.add_argument("--codex-digests", default=str(BRIDGE_ROOT),
                    help="Extratos privados do Codex sincronizados; string vazia desativa esta fonte")
    ap.add_argument("--domains", default="",
                    help='Regras de domínio "palavra=Dominio,palavra2=Dominio2" (substring do caminho/cwd)')
    ap.add_argument("--json", action="store_true"); ap.add_argument("--count", action="store_true")
    ap.add_argument("--commit", action="store_true"); ap.add_argument("--lookback-days", type=int, default=7)
    ap.add_argument("--as-of", default=None, help="ISO: fecha a janela NESTE instante, não em 'agora'. "
                    "Use o generatedAt do --json que foi realmente minerado — entre gerar o digest e "
                    "aprovar o relatório passam horas, e sessão que chega no meio não pode ser marcada "
                    "como vista sem ter sido lida.")
    a = ap.parse_args()
    for pair in a.domains.split(","):
        needle, _, domain = pair.strip().partition("=")
        if needle and domain: DOMAIN_RULES.append((needle.strip().lower(), domain.strip()))
    review_cutoff = to_local(a.as_of) if a.as_of else None
    if a.as_of and review_cutoff is None:
        ap.error("--as-of deve ser uma data ISO válida")
    reviewed = json.loads(CODEX_REVIEWED.read_text()) if CODEX_REVIEWED.exists() else {}

    if STATE.exists():
        since = datetime.datetime.fromisoformat(json.loads(STATE.read_text())["last_run"].rstrip("Z"))
    else:
        since = datetime.datetime.now() - datetime.timedelta(days=a.lookback_days)
        print(f"⚠️  {STATE.name} NÃO existe — a janela caiu no default de {a.lookback_days} dias "
              f"(desde {since.isoformat()[:16]}). Se não é a 1ª run, o marcador se perdeu: material "
              f"pode ser repetido ou pulado. Rode com --commit ao fim para recriá-lo.", file=sys.stderr)

    digests, drifted, skipped_old = [], 0, 0
    for d in a.dirs.split(","):
        base = Path(d.strip()).expanduser()
        if not base.is_dir(): continue
        for f in base.rglob("*.jsonl"):
            rel = f.relative_to(base)
            # oculta RELATIVA à base (.stversions do Syncthing). No path absoluto não dá:
            # ~/.claude/projects já contém componente oculto e zeraria a varredura.
            if any(part.startswith(".") for part in rel.parts): continue
            rp = str(rel)
            if "/subagents/" in f"/{rp}" or "/workflows/" in f"/{rp}": continue
            # cópia de conflito do Syncthing: <sessao>.sync-conflict-<data>-<id>.jsonl.
            # É a MESMA sessão duplicada — sem isso uma conversa entra 2-3x na janela
            # (mesma família do bug do .stversions, corrigido em 25/08/2026).
            if ".sync-conflict-" in f.name: continue
            mt = datetime.datetime.fromtimestamp(f.stat().st_mtime)
            # pré-filtro barato: o sync só empurra o mtime pra FRENTE, então mtime >= data real.
            # Logo mtime <= since ⟹ conversa <= since. Nunca descarta sessão nova por engano.
            if mt <= since: continue
            r = parse(f)
            if not r: continue
            real = to_local(r["lastEvent"]) if r["lastEvent"] else None
            when = real or mt
            if review_cutoff and when > review_cutoff:
                continue
            if when <= since:  # sessão antiga que só CHEGOU agora pelo espelho
                skipped_old += 1
                continue
            drift = abs((mt - when).days)
            if drift >= DRIFT_ALERT_DAYS: drifted += 1
            digests.append({"file": rp, **r, "mtime": mt.isoformat(),
                            "date": when.isoformat(), "syncDriftDays": drift,
                            "domain": domain_of(r.get("cwd") or rp)})
    # Marca própria por sessão: uma exportação que chega depois do sync não é perdida
    # só porque a janela global já avançou na outra máquina.
    if a.codex_digests:
        direct_ids = {e.get("sessionId") for e in digests if e.get("source") == "codex"}
        for row in load_digests(Path(a.codex_digests).expanduser()):
            key = row["sessionId"]
            when = to_local(row["lastEvent"])
            last_review = to_local(reviewed.get(key))
            if key in direct_ids or (last_review and when <= last_review):
                continue
            if review_cutoff and when > review_cutoff:
                continue
            direct_ids.add(key)
            digests.append({**row, "file": "codex:" + key, "date": when.isoformat(),
                            "mtime": when.isoformat(), "syncDriftDays": 0,
                            "domain": domain_of(row.get("cwd", ""))})
    digests.sort(key=lambda x: x["date"])

    if a.count: print(len(digests)); return 0

    if a.commit:
        corte = a.as_of or datetime.datetime.now().isoformat()
        STATE.write_text(json.dumps({"last_run": corte,
                                     "last_count": len(digests)}, indent=2))
        print(f"janela fechada em {corte[:19]}", file=sys.stderr)
        hist = json.loads(USO.read_text()) if USO.exists() else {}
        for e in digests:
            day = e["date"][:10]
            for t in e["tools"]: bump(hist, f"tool:{t}", day)
            for s in e["skills"]: bump(hist, f"skill:{s}", day)
            bump(hist, f"domain:{e['domain']}", day)
        USO.write_text(json.dumps(dict(sorted(hist.items())), indent=2, ensure_ascii=False))
        for e in digests:
            if e.get("source") == "codex":
                reviewed[e["sessionId"]] = e["lastEvent"]
        CODEX_REVIEWED.write_text(json.dumps(reviewed, indent=2))

    if a.json:
        print(json.dumps({"since": since.isoformat(), "generatedAt": datetime.datetime.now().isoformat(), "count": len(digests),
                          "skippedOldSynced": skipped_old, "syncDrifted": drifted,
                          "digests": digests}, ensure_ascii=False, indent=2))
    else:
        print(f"# sessions-digest — {len(digests)} sessões novas substanciais desde {since.isoformat()[:16]}")
        if skipped_old:
            print(f"  ({skipped_old} sessão(ões) antiga(s) ignorada(s): chegaram agora pelo espelho, "
                  f"mas a conversa é anterior à janela)")
        if drifted:
            print(f"  ({drifted} com data de arquivo ≥{DRIFT_ALERT_DAYS}d à frente da conversa — sync, não atividade)")
        print("(--json → digests completos · --commit → fecha a janela · --count → só o número)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
