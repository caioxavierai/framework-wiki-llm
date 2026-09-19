#!/usr/bin/env python3
"""wiki_index.py — sincroniza os índices de uma wiki em dois níveis com o disco.

Modo SYNC (preserva curadoria): NUNCA reescreve descrição existente — só
(a) ADICIONA página que está no disco e fora do índice da pasta,
(b) CRIA index.md em pasta que tem páginas e não tem índice,
(c) CORRIGE a contagem "· N páginas" no índice raiz,
(d) REPORTA entradas mortas (não remove — remoção é decisão humana/lint).

Uso:
  python3 wiki_index.py <wiki_root> [--write] [--json]
Sem --write é dry-run (relatório). Com --write: backup .bak-<ts> antes de tocar.
"""
import argparse, datetime, json, re, sys
from pathlib import Path

RESERVED = {"index.md", "log.md", "SCHEMA.md", "CLAUDE.md", "AGENTS.md", "README.md"}
SKIP_DIRS = {".arquivo", ".git", ".stfolder", ".stversions", "node_modules", "__pycache__"}
MDLINK = re.compile(r"\]\(([^)#\s]+?\.md)(?:#[^)]*)?\)")
WIKILINK = re.compile(r"\[\[([^\]|#\n]+)")

def is_noise(n): return ".bak-" in n or ".sync-conflict" in n or ".pre-symlink" in n

def descr(p: Path) -> str:
    t = p.read_text(encoding="utf-8", errors="ignore")
    if t.startswith("---\n"):
        end = t.find("\n---", 4)
        m = re.search(r"^description:\s*(.+)$", t[4:end], re.M) if end > 0 else None
        if m: return m.group(1).strip().strip("\"'")[:140]
        t = t[end+4:] if end > 0 else t
    m = re.search(r"^>\s*(.+)$", t, re.M)
    if m: return re.sub(r"\*\*", "", m.group(1)).strip()[:140]
    m = re.search(r"^#\s+(.+)$", t, re.M)
    return (m.group(1).strip() if m else p.stem)[:140]

def idx_targets(idx: Path, root: Path):
    out = set()
    t = idx.read_text(encoding="utf-8", errors="ignore")
    for m in MDLINK.finditer(t):
        x = m.group(1)
        if x.startswith(("http", "//", "~", "mailto:")): continue
        out.add(((root / x.lstrip("/")) if x.startswith("/") else (idx.parent / x)).resolve())
    for m in WIKILINK.finditer(t):
        x = m.group(1).strip()
        out.add((root / f"{x}.md").resolve())
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("wiki_root"); ap.add_argument("--write", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    root = Path(a.wiki_root).expanduser().resolve()
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    rep = {"add": [], "create": [], "dead": [], "root_counts": []}

    dirs = sorted({p.parent for p in root.rglob("*.md")
                   if p.parent != root and p.name not in RESERVED and not is_noise(p.name)
                   and not (set(p.relative_to(root).parts[:-1]) & SKIP_DIRS)})
    for d in dirs:
        pages = sorted(q for q in d.iterdir()
                       if q.suffix == ".md" and q.name not in RESERVED and not is_noise(q.name))
        idx = d / "index.md"
        if idx.exists():
            known = idx_targets(idx, root)
            add = [q for q in pages if q.resolve() not in known]
            dead = [str(t) for t in known if str(t).startswith(str(d)) and not t.exists()]
            rep["dead"] += [f"{idx.relative_to(root)} -> {Path(x).name}" for x in dead]
            if add:
                lines = [f"- [{q.stem}]({q.name}) — {descr(q)}" for q in add]
                rep["add"].append({"index": str(idx.relative_to(root)), "entradas": lines})
                if a.write:
                    bak = idx.with_name(f"index.md.bak-{ts}")
                    if not bak.exists(): bak.write_bytes(idx.read_bytes())
                    idx.write_text(idx.read_text(encoding="utf-8").rstrip("\n") + "\n" + "\n".join(lines) + "\n", encoding="utf-8")
        else:
            rel = d.relative_to(root); up = "../" * len(rel.parts)
            lines = [f"- [{q.stem}]({q.name}) — {descr(q)}" for q in pages]
            body = (f"# {rel.parts[-1]}\n\n> Índice da pasta `{rel}/` — (completar descrição da área).\n"
                    f"> Voltar ao [índice da wiki]({up}index.md) · histórico em [`log.md`]({up}log.md).\n\n"
                    + "\n".join(lines) + "\n")
            rep["create"].append({"index": f"{rel}/index.md", "paginas": len(pages)})
            if a.write:
                idx.write_text(body, encoding="utf-8")

    ridx = root / "index.md"
    if ridx.exists():
        t = ridx.read_text(encoding="utf-8")
        def fix(m):
            folder = m.group(2)
            real = len([q for q in (root / folder).rglob("*.md")
                        if q.name != "index.md" and not is_noise(q.name)])
            if int(m.group(3)) != real:
                rep["root_counts"].append(f"{folder}: {m.group(3)} -> {real}")
                return f"{m.group(1)}{real} {'página' if real == 1 else 'páginas'}"
            return m.group(0)
        novo = re.sub(r"(\]\(([\w./-]+)/index\.md\)[^\n·]*·\s*)(\d+)(\s*páginas?)", fix, t)
        if novo != t and a.write:
            bak = ridx.with_name(f"index.md.bak-{ts}")
            if not bak.exists(): bak.write_bytes(ridx.read_bytes())
            ridx.write_text(novo, encoding="utf-8")

    total = len(rep["add"]) + len(rep["create"]) + len(rep["root_counts"])
    if a.json:
        print(json.dumps({"wiki": str(root), "modo": "write" if a.write else "dry-run",
                          "pendencias": total, **rep}, ensure_ascii=False, indent=2))
    else:
        print(f"# wiki_index — {root} ({'WRITE' if a.write else 'dry-run'})")
        for x in rep["add"]:
            print(f"  + {x['index']}: {len(x['entradas'])} entrada(s) a adicionar")
            for l in x["entradas"][:6]: print(f"      {l[:110]}")
        for x in rep["create"]: print(f"  ★ criar {x['index']} ({x['paginas']} páginas)")
        for x in rep["root_counts"]: print(f"  # contagem raiz: {x}")
        for x in rep["dead"][:10]: print(f"  ✗ entrada morta: {x}")
        print("→ índices em dia" if total == 0 and not rep["dead"] else f"→ {total} pendência(s), {len(rep['dead'])} morta(s)")
    return 0 if total == 0 and not rep["dead"] else 2

if __name__ == "__main__":
    sys.exit(main())
