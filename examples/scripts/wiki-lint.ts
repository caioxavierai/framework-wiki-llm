#!/usr/bin/env bun
/**
 * wiki-lint.ts — Camada A da curadoria (saúde mecânica), versão de REFERÊNCIA.
 *
 * 100% READ-ONLY: detecta e reporta, NUNCA escreve na wiki. As correções são
 * aplicadas pelo agente, com aprovação humana (a régua "detecta sozinho, escreve com gate").
 *
 * Roda com Bun (https://bun.sh). Adapte WIKI_ROOT e ACTIVE_DIRS ao seu caso.
 *
 *   WIKI_ROOT=./minha-wiki bun run wiki-lint.ts          # relatório legível
 *   WIKI_ROOT=./minha-wiki bun run wiki-lint.ts --json   # saída JSON (pro agente consumir)
 *
 * Checa: links [[..]] quebrados · páginas órfãs · drift do índice ·
 *        header de data defasado · páginas estagnadas.
 */
import { Glob } from "bun";
import { statSync } from "node:fs";
import { join } from "node:path";

const WIKI = process.env.WIKI_ROOT || "./wiki";
const ROOT_DOCS = new Set(["index.md", "log.md", "SCHEMA.md", "CLAUDE.md", "AGENTS.md"]);
// Categorias "ativas" para o check de páginas estagnadas (ajuste ao seu domínio):
const ACTIVE_DIRS = (process.env.ACTIVE_DIRS || "projetos,conceitos").split(",").map((s) => s.trim()).filter(Boolean);
const STALE_DAYS = Number(process.env.STALE_DAYS || 60);
const DAY = 86_400_000;
const now = Date.now();

const noExt = (f: string) => f.replace(/\.md$/, "");
const base = (f: string) => noExt(f).split("/").pop()!;

// Remove blocos de código (fenced ``` e inline `) — evita falsos positivos de
// [[ ]] que são exemplos de template ou sintaxe de shell dentro de code blocks.
function stripCode(text: string): string {
  return text.replace(/```[\s\S]*?```/g, "").replace(/`[^`\n]*`/g, "");
}

// Extrai wikilinks normalizados (tira alias |, âncora #, .md; resolve ../ e ./).
function links(text: string, fromFile: string): string[] {
  const out: string[] = [];
  const re = /\[\[([^\]]+)\]\]/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(stripCode(text))) !== null) {
    let t = m[1].split("|")[0].split("#")[0].trim().replace(/\.md$/, "");
    if (!t) continue;
    if (t.startsWith("../") || t.startsWith("./")) {
      const dir = fromFile.includes("/") ? fromFile.slice(0, fromFile.lastIndexOf("/")) : "";
      t = join(dir, t).replace(/\\/g, "/");
    }
    out.push(t);
  }
  return out;
}

// 1) coletar todas as .md (ignora dotdirs como .git/.obsidian)
const allMd: string[] = [];
for await (const f of new Glob("**/*.md").scan({ cwd: WIKI, onlyFiles: true })) {
  if (f.split("/").some((p) => p.startsWith("."))) continue;
  allMd.push(f);
}
const pages = allMd.filter((f) => !ROOT_DOCS.has(f));

const resolveSet = new Set<string>();
for (const f of allMd) { resolveSet.add(noExt(f)); resolveSet.add(base(f)); }

type Doc = { f: string; text: string; mtime: number };
const docs: Doc[] = [];
for (const f of allMd) docs.push({ f, text: await Bun.file(join(WIKI, f)).text(), mtime: statSync(join(WIKI, f)).mtimeMs });
const byFile = new Map(docs.map((d) => [d.f, d]));

// CHECK 1 — links quebrados
const brokenLinks: { from: string; link: string }[] = [];
for (const d of docs)
  for (const l of links(d.text, d.f))
    if (!resolveSet.has(l)) brokenLinks.push({ from: d.f, link: l });

// CHECK 2/3 — órfãs e drift do índice
const allTargets = new Set<string>();
for (const d of docs) for (const l of links(d.text, d.f)) allTargets.add(l);
const indexDoc = byFile.get("index.md");
const indexTargets = new Set(indexDoc ? links(indexDoc.text, "index.md") : []);
const orphans = pages.filter((f) => !allTargets.has(noExt(f)) && !allTargets.has(base(f)));
const missingFromIndex = pages.filter((f) => !indexTargets.has(noExt(f)) && !indexTargets.has(base(f)));

// CHECK 4 — header de data do índice vs página mais recente
const headerDate = indexDoc?.text.match(/[Úu]ltima atualiza[çc][ãa]o:\s*(\d{4}-\d{2}-\d{2})/)?.[1] ?? null;
let recent = { f: "", mtime: 0 };
for (const d of docs) if (!ROOT_DOCS.has(d.f) && d.mtime > recent.mtime) recent = { f: d.f, mtime: d.mtime };
const mostRecentDate = recent.mtime ? new Date(recent.mtime).toISOString().slice(0, 10) : "—";
const staleHeader = { headerDate, mostRecentDate, isStale: headerDate ? headerDate < mostRecentDate : true };

// CHECK 5 — páginas estagnadas em categorias ativas
const stalePages = pages
  .filter((f) => ACTIVE_DIRS.some((d) => f.startsWith(d + "/")))
  .map((f) => ({ f, ageDays: Math.floor((now - byFile.get(f)!.mtime) / DAY) }))
  .filter((p) => p.ageDays > STALE_DAYS)
  .sort((a, b) => b.ageDays - a.ageDays);

const result = { wiki: WIKI, totals: { md: allMd.length, pages: pages.length }, brokenLinks, orphans, missingFromIndex, staleHeader, stalePages };

if (process.argv.includes("--json")) {
  console.log(JSON.stringify(result, null, 2));
} else {
  const c = (a: unknown[]) => a.length;
  console.log(`# wiki-lint (READ-ONLY) — ${WIKI}\nPáginas: ${pages.length}\n`);
  console.log(`## 1. Links quebrados: ${c(brokenLinks)}`);
  for (const b of brokenLinks) console.log(`   - [[${b.link}]]  (em ${b.from})`);
  console.log(`\n## 2. Órfãs: ${c(orphans)}`);
  for (const o of orphans) console.log(`   - ${o}`);
  console.log(`\n## 3. Fora do índice: ${c(missingFromIndex)}`);
  for (const m of missingFromIndex) console.log(`   - ${m}`);
  console.log(`\n## 4. Header de data: ${staleHeader.isStale ? "⚠️ DEFASADO" : "✅ ok"} (header ${staleHeader.headerDate ?? "ausente"} · página mais recente ${mostRecentDate})`);
  console.log(`\n## 5. Estagnadas >${STALE_DAYS}d em [${ACTIVE_DIRS.join(", ")}]: ${c(stalePages)}`);
  for (const s of stalePages) console.log(`   - ${s.f} (${s.ageDays}d)`);
  const drift = c(brokenLinks) + c(orphans) + c(missingFromIndex) + (staleHeader.isStale ? 1 : 0);
  console.log(`\n${drift === 0 && c(stalePages) === 0 ? "✅ wiki saudável" : `⚠️ ${drift} itens de drift + ${c(stalePages)} estagnadas`}`);
}
