#!/usr/bin/env python3
"""wiki_lint.py — checker READ-ONLY de saúde de uma wiki LLM.

Stdlib pura, roda em qualquer máquina e entende as DUAS formas de link —
[[wikilink]] e [texto](relativo.md).

Uso:
  python3 wiki_lint.py <wiki_root> [--json] [--active-dirs a,b] [--stale-days 60] [--okf]

Checks (silêncio = saudável):
  broken_links          [[x]] ou [t](x.md) sem alvo no disco
  orphans               página sem nenhum link de entrada (índice conta)
  folder_index_drift    página no disco fora do index.md da própria pasta
  missing_folder_index  pasta com páginas e sem index.md
  root_index_drift      área com conteúdo fora do index.md raiz
  index_narrative       histórico infiltrado em índice (Última atualização / Contexto anterior)
  stale                 stale_after vencido, ou mtime > N dias em --active-dirs
  okf                   (--okf) página sem frontmatter parseável ou sem type

Exit: 0 saudável · 2 há achados. Nunca escreve.
"""
import argparse, datetime, json, re, sys
from pathlib import Path

RESERVED = {"index.md", "log.md", "SCHEMA.md", "CLAUDE.md", "AGENTS.md", "README.md"}
SKIP_DIRS = {".arquivo", ".git", ".stfolder", ".stversions", "node_modules", "__pycache__"}
WIKILINK = re.compile(r"\[\[([^\]|#\n]+)")
MDLINK = re.compile(r"\]\(([^)#\s]+?\.md)(?:#[^)]*)?\)")
NARRATIVE = re.compile(r"Última atualização|Ultima atualização|Contexto anterior")

def is_noise(name: str) -> bool:
    return ".bak-" in name or ".sync-conflict" in name or ".pre-symlink" in name

def strip_code(text: str) -> str:
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    return re.sub(r"`[^`\n]*`", "", text)

def frontmatter(text: str):
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end < 0:
        return None
    fm = {}
    for line in text[4:end].split("\n"):
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if m:
            fm[m.group(1)] = m.group(2).strip().strip("\"'")
    return fm

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("wiki_root")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--active-dirs", default="")
    ap.add_argument("--stale-days", type=int, default=60)
    ap.add_argument("--okf", action="store_true")
    a = ap.parse_args()
    root = Path(a.wiki_root).expanduser().resolve()
    if not root.is_dir():
        print(f"erro: {root} não existe", file=sys.stderr); return 1
    active = {d.strip() for d in a.active_dirs.split(",") if d.strip()}
    today = datetime.date.today()

    all_md = [p for p in root.rglob("*.md")
              if not is_noise(p.name) and not (set(p.relative_to(root).parts[:-1]) & SKIP_DIRS)]
    pages = [p for p in all_md if p.name not in RESERVED]
    stems = {}
    for p in pages:
        stems.setdefault(p.stem, []).append(p)

    texts = {p: p.read_text(encoding="utf-8", errors="ignore") for p in all_md}
    F = {k: [] for k in ("broken_links", "orphans", "folder_index_drift", "missing_folder_index",
                          "root_index_drift", "index_narrative", "stale", "okf")}
    inbound, resolved_by_file = set(), {}

    for p in all_md:
        body = strip_code(texts[p])
        targets = set()
        for m in MDLINK.finditer(body):
            t = m.group(1)
            if t.startswith(("http", "//", "mailto:")):
                continue
            tp = (root / t.lstrip("/")) if t.startswith("/") else (p.parent / t)
            tp = Path(tp).resolve() if not t.startswith("~") else Path(t).expanduser().resolve()
            if tp.exists():
                targets.add(tp)
            else:
                F["broken_links"].append(f"{p.relative_to(root)} -> {t}")
        for m in WIKILINK.finditer(body):
            t = m.group(1).strip().rstrip("/")
            if not t or re.match(r"^\.+$", t) or any(c in t for c in '${}"'):
                continue
            tp = (p.parent / f"{t}.md") if t.startswith(".") else (root / f"{t}.md")
            if tp.exists():
                targets.add(tp.resolve())
            elif "/" not in t and t in stems:
                targets.add(stems[t][0].resolve())
            elif (root / t).is_dir():
                pass
            else:
                F["broken_links"].append(f"{p.relative_to(root)} -> [[{t}]]")
        resolved_by_file[p] = targets
        inbound |= targets

    for p in pages:
        if p.resolve() not in inbound:
            F["orphans"].append(str(p.relative_to(root)))

    root_idx = root / "index.md"
    for idx in [p for p in all_md if p.name == "index.md"]:
        n = len(NARRATIVE.findall(strip_code(texts[idx])))
        if n:
            F["index_narrative"].append(f"{idx.relative_to(root)} ({n} ocorrência{'s' if n>1 else ''})")
        if idx == root_idx:
            continue
        local = [q for q in idx.parent.iterdir()
                 if q.suffix == ".md" and q.name not in RESERVED and not is_noise(q.name)]
        for q in local:
            if q.resolve() not in resolved_by_file.get(idx, set()):
                F["folder_index_drift"].append(f"{q.relative_to(root)} fora de {idx.relative_to(root)}")

    dirs_with_pages = {}
    for p in pages:
        d = p.parent
        if d != root:
            dirs_with_pages.setdefault(d, 0)
            dirs_with_pages[d] += 1
    for d in sorted(dirs_with_pages):
        if not (d / "index.md").exists():
            F["missing_folder_index"].append(f"{d.relative_to(root)}/ ({dirs_with_pages[d]} páginas)")

    if root_idx.exists():
        rt = resolved_by_file.get(root_idx, set())
        for d in sorted({p.relative_to(root).parts[0] for p in pages if len(p.relative_to(root).parts) > 1}):
            area = (root / d).resolve()
            if not any(str(t).startswith(str(area)) for t in rt):
                F["root_index_drift"].append(f"{d}/ fora do index.md raiz")

    for p in pages:
        fm = frontmatter(texts[p]) or {}
        sa = fm.get("stale_after", "")[:10]
        if sa:
            try:
                if datetime.date.fromisoformat(sa) <= today:
                    F["stale"].append(f"{p.relative_to(root)} (stale_after {sa})")
            except ValueError:
                pass
        elif active and p.relative_to(root).parts[0] in active:
            age = (today - datetime.date.fromtimestamp(p.stat().st_mtime)).days
            if age > a.stale_days:
                F["stale"].append(f"{p.relative_to(root)} ({age}d sem edição)")
        if a.okf and (frontmatter(texts[p]) is None or not (frontmatter(texts[p]) or {}).get("type")):
            F["okf"].append(str(p.relative_to(root)))

    total = sum(len(v) for v in F.values())
    if a.json:
        print(json.dumps({"wiki": str(root), "ok": total == 0, "total": total,
                          "summary": {k: len(v) for k, v in F.items()},
                          "findings": {k: (v[:100] if k == "okf" else v) for k, v in F.items() if v}},
                         ensure_ascii=False, indent=2))
    else:
        print(f"# wiki_lint — {root}  ({len(pages)} páginas)")
        for k, v in F.items():
            if not v and k == "okf" and not a.okf:
                continue
            print(f"  {'✓' if not v else '✗'} {k}: {len(v)}")
            for item in v[:12]:
                print(f"      {item}")
            if len(v) > 12:
                print(f"      … +{len(v)-12}")
        print("→ wiki saudável" if total == 0 else f"→ {total} achados")
    return 0 if total == 0 else 2

if __name__ == "__main__":
    sys.exit(main())
