#!/usr/bin/env python3
"""wiki_frontmatter.py — injeta/valida frontmatter OKF em lote numa wiki existente.

Para cada página SEM frontmatter (ou sem `type`): deriva `type` do mapa pasta→Tipo
(match mais específico vence), `title` do H1 e `description` do primeiro blockquote.
NUNCA altera o corpo. Página que já tem `type` é pulada. Dry-run por padrão.

Uso:
  python3 wiki_frontmatter.py <wiki_root> \
      --map "comercial/pessoas=Pessoa,comercial=Processo,sistemas=Sistema" \
      --default-type Documento [--write] [--json]
"""
import argparse, json, re, sys
from pathlib import Path

RESERVED = {"index.md", "log.md", "SCHEMA.md", "CLAUDE.md", "AGENTS.md", "README.md"}
SKIP_DIRS = {".arquivo", ".git", ".stfolder", ".stversions", "node_modules", "__pycache__"}

def is_noise(n): return ".bak-" in n or ".sync-conflict" in n or ".pre-symlink" in n

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("wiki_root"); ap.add_argument("--map", default="")
    ap.add_argument("--default-type", default="Documento")
    ap.add_argument("--write", action="store_true"); ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    root = Path(a.wiki_root).expanduser().resolve()
    tmap = []
    for pair in a.map.split(","):
        k, _, v = pair.strip().partition("=")
        if k and v: tmap.append((k.strip("/"), v))
    tmap.sort(key=lambda x: -len(x[0]))  # mais específico primeiro

    done, skipped, patched = [], [], []
    for p in sorted(root.rglob("*.md")):
        rel = p.relative_to(root)
        if p.name in RESERVED or is_noise(p.name) or set(rel.parts[:-1]) & SKIP_DIRS: continue
        t = p.read_text(encoding="utf-8", errors="ignore")
        has_fm = t.startswith("---\n") and t.find("\n---", 4) > 0
        if has_fm:
            end = t.find("\n---", 4)
            if re.search(r"^type:\s*\S", t[4:end], re.M):
                skipped.append(str(rel)); continue
            tipo = next((v for k, v in tmap if str(rel).startswith(k + "/")), a.default_type)
            novo = t[:4] + f"type: {tipo}\n" + t[4:]
            patched.append({"page": str(rel), "type": tipo, "acao": "type em frontmatter existente"})
            if a.write: p.write_text(novo, encoding="utf-8")
            continue
        tipo = next((v for k, v in tmap if str(rel).startswith(k + "/")), a.default_type)
        m = re.search(r"^#\s+(.+)$", t, re.M)
        title = (m.group(1).strip() if m else p.stem)[:150].replace('"', "'")
        m = re.search(r"^>\s*(.+)$", t, re.M)
        desc = re.sub(r"\*\*|\[|\]", "", m.group(1)).strip()[:180].replace('"', "'") if m else ""
        fm = f'---\ntype: {tipo}\ntitle: "{title}"\n' + (f'description: "{desc}"\n' if desc else "") + "---\n\n"
        done.append({"page": str(rel), "type": tipo})
        if a.write: p.write_text(fm + t, encoding="utf-8")

    out = {"wiki": str(root), "modo": "write" if a.write else "dry-run",
           "injetadas": len(done), "patch_type": len(patched), "ja_conformes": len(skipped),
           "por_tipo": {}, "paginas": done + patched}
    for d in done + patched:
        out["por_tipo"][d["type"]] = out["por_tipo"].get(d["type"], 0) + 1
    if a.json: print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(f"# wiki_frontmatter — {root} ({out['modo']})")
        print(f"  a injetar: {len(done)} | patch de type: {len(patched)} | já conformes: {len(skipped)}")
        for k, v in sorted(out["por_tipo"].items(), key=lambda x: -x[1]): print(f"    {k}: {v}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
