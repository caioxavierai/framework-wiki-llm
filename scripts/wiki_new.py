#!/usr/bin/env python3
"""wiki_new.py — scaffold de uma wiki nova do framework, já conformante OKF v0.2.

Instancia os templates/ do framework: 4 arquivos-raiz + 1 pasta por categoria com index.md.
Nunca sobrescreve arquivo existente (idempotente/aditivo).

Uso:
  python3 wiki_new.py <destino> --nome "Pessoal" \
      --categorias "comercial:processos comerciais;produtos:catálogo de produtos"
Os templates já escrevem "Wiki <nome>": passe só o nome (ex.: "Pessoal"), sem a palavra "Wiki".
Depois: preencher os <placeholders> restantes de SCHEMA.md (domínio), CLAUDE.md (hierarquia de
fontes) e index.md (ponteiros para fora).
"""
import argparse, sys
from pathlib import Path

TPL = Path(__file__).resolve().parent.parent / "templates"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("destino"); ap.add_argument("--nome", required=True)
    ap.add_argument("--categorias", required=True, help='"slug:descrição;slug2:descrição2"')
    a = ap.parse_args()
    dest = Path(a.destino).expanduser().resolve()
    dest.mkdir(parents=True, exist_ok=True)
    cats = []
    for c in a.categorias.split(";"):
        slug, _, desc = c.strip().partition(":")
        if slug: cats.append((slug.strip(), desc.strip() or "(completar descrição)"))
    if not cats: print("erro: nenhuma categoria", file=sys.stderr); return 1

    def render(tpl, **kw):
        t = (TPL / tpl).read_text(encoding="utf-8")
        for k, v in kw.items(): t = t.replace(k, v)
        return t

    def write(path, content):
        if path.exists(): print(f"  = {path.relative_to(dest)} (já existe, preservado)"); return
        path.write_text(content, encoding="utf-8"); print(f"  + {path.relative_to(dest)}")

    write(dest/"SCHEMA.md", render("SCHEMA.md", **{"<NOME-DA-WIKI>": a.nome}))
    write(dest/"CLAUDE.md", render("CLAUDE.md", **{"<NOME-DA-WIKI>": a.nome}))
    write(dest/"log.md",    render("log.md",    **{"<NOME-DA-WIKI>": a.nome}))
    areas = "\n".join(f"- [{s}]({s}/index.md) — {d} · 0 páginas" for s, d in cats)
    raiz = render("index-raiz.md", **{"<NOME-DA-WIKI>": a.nome})
    raiz = raiz.replace("- [<Categoria 1>](<categoria-1>/index.md) — <o que cobre> · 0 páginas\n"
                        "- [<Categoria 2>](<categoria-2>/index.md) — <o que cobre> · 0 páginas", areas)
    write(dest/"index.md", raiz)
    for s, d in cats:
        (dest/s).mkdir(exist_ok=True)
        body = render("index-pasta.md", **{"<Categoria>": s, "<categoria>": s, "<o que a área cobre>": d})
        body = body.replace("- [<exemplo>](<exemplo>.md) — <resumo em uma linha>\n", "")
        write(dest/s/"index.md", body)
    print(f"\nwiki '{a.nome}' criada em {dest} — validar: python3 {Path(__file__).parent}/wiki_lint.py {dest} --okf")
    print("falta preencher à mão: SCHEMA.md (domínio da wiki), CLAUDE.md (hierarquia de fontes), index.md (ponteiros para fora)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
