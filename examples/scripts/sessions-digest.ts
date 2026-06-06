#!/usr/bin/env bun
/**
 * sessions-digest.ts — Estágio 1 da Camada B (curadoria das sessões), versão de REFERÊNCIA.
 *
 * Varre as sessões NOVAS do seu agente (desde a última curadoria), filtra ruído
 * e extrai um DIGEST barato: intenções do usuário + ferramentas usadas + pasta/domínio.
 * READ-ONLY sobre as sessões; só escreve o estado da rotina (./.curadoria-state.json).
 *
 * ⚠️ O FORMATO DE SESSÃO VARIA POR AGENTE. Este exemplo assume arquivos .jsonl
 * (uma linha JSON por evento) com eventos de tipo "user"/"assistant" — comum em
 * vários agentes de coding. Adapte parseSession() ao formato do SEU agente.
 *
 *   SESSIONS_DIRS=~/.meu-agente/sessions bun run sessions-digest.ts          # resumo
 *   SESSIONS_DIRS=dir1,dir2 bun run sessions-digest.ts --json                # JSON pro agente
 *   bun run sessions-digest.ts --count                                       # só o número (pro lembrete)
 *   bun run sessions-digest.ts --commit                                      # marca como processado
 */
import { Glob } from "bun";
import { statSync, existsSync } from "node:fs";
import { join } from "node:path";

const SESSIONS_DIRS = (process.env.SESSIONS_DIRS || "./sessions").split(",").map((s) => s.replace(/^~/, process.env.HOME || "~").trim());
const STATE_FILE = process.env.STATE_FILE || "./.curadoria-state.json";
const MIN_USER_MSGS = 2;     // < isso = sessão trivial, ignorada
const MAX_INTENT_LEN = 280;
const DEFAULT_LOOKBACK_DAYS = 7;
const args = process.argv.slice(2);
const flag = (n: string) => args.includes(n);

let sinceMs: number;
if (existsSync(STATE_FILE)) sinceMs = new Date(JSON.parse(await Bun.file(STATE_FILE).text()).last_run).getTime();
else sinceMs = Date.now() - DEFAULT_LOOKBACK_DAYS * 86_400_000;

function cleanUserText(s: string): string {
  // remova aqui o ruído específico do seu agente (system reminders, hooks injetados, etc.)
  return s.replace(/<[^>]+>[\s\S]*?<\/[^>]+>/g, "").replace(/\s+/g, " ").trim();
}

type Digest = { file: string; intents: string[]; tools: string[]; nUser: number; mtime: string };

// Adapte ao formato do SEU agente. Aqui: .jsonl, eventos {type:"user"|"assistant", message:{content, ...}}.
function parseSession(text: string): Omit<Digest, "file" | "mtime"> | null {
  const intents: string[] = []; const tools = new Set<string>();
  for (const line of text.split("\n")) {
    if (!line.trim()) continue;
    let ev: any; try { ev = JSON.parse(line); } catch { continue; }
    if (ev.type === "user") {
      const c = ev.message?.content;
      const raw = typeof c === "string" ? c : Array.isArray(c) ? c.filter((b: any) => b?.type === "text").map((b: any) => b.text).join(" ") : "";
      const t = cleanUserText(raw); if (t) intents.push(t.slice(0, MAX_INTENT_LEN));
    } else if (ev.type === "assistant" && Array.isArray(ev.message?.content)) {
      for (const b of ev.message.content) if (b?.type === "tool_use" && b.name) tools.add(b.name);
    }
  }
  if (intents.length < MIN_USER_MSGS) return null; // trivial
  return { intents, tools: [...tools], nUser: intents.length };
}

const digests: Digest[] = [];
for (const dir of SESSIONS_DIRS) {
  if (!existsSync(dir)) continue;
  for await (const f of new Glob("**/*.jsonl").scan({ cwd: dir, onlyFiles: true })) {
    // FILTRE O RUÍDO DO SEU AGENTE: ex. transcripts de subagente/workflow não são sessões reais.
    if (f.includes("/subagents/") || f.includes("/workflows/")) continue;
    const full = join(dir, f); const mt = statSync(full).mtimeMs; if (mt <= sinceMs) continue;
    const d = parseSession(await Bun.file(full).text());
    if (d) digests.push({ file: f, ...d, mtime: new Date(mt).toISOString() });
  }
}
digests.sort((a, b) => a.mtime.localeCompare(b.mtime));

if (flag("--count")) { console.log(digests.length); process.exit(0); }
if (flag("--commit")) await Bun.write(STATE_FILE, JSON.stringify({ last_run: new Date().toISOString(), last_count: digests.length }, null, 2));

if (flag("--json")) {
  console.log(JSON.stringify({ since: new Date(sinceMs).toISOString(), count: digests.length, digests }, null, 2));
} else {
  console.log(`# sessions-digest — ${digests.length} sessões novas substanciais desde ${new Date(sinceMs).toISOString().slice(0, 16)}`);
  console.log(`(--json → digests completos pro agente minerar · --commit → fecha a janela · --count → só o número)`);
}
