#!/usr/bin/env python3
"""Extratos privados de sessões Codex para a curadoria existente (stdlib).

Não copia credenciais, bases SQLite, áudio ou transcrições completas. Lê o formato
JSONL observado em 2026-09; mudanças de formato precisam de nova validação.
Não escreve na wiki nem avança a janela de revisão.
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import socket
import sys
from pathlib import Path

# Pasta PRIVADA (0o700) dos extratos. Aponte para uma pasta sincronizada com WIKI_CODEX_BRIDGE_ROOT
# se quiser levar os extratos a outra máquina.
BRIDGE_ROOT = Path(os.environ.get("WIKI_CODEX_BRIDGE_ROOT")
                   or Path.home() / ".wiki-llm/codex-curadoria").expanduser()
SCHEMA_VERSION = 1
IGNORED_USER_PREFIXES = (
    "# AGENTS.md instructions", "<environment_context>", "<recommended_plugins>",
    "<realtime_delegation>", "<user_instructions>",
)


def timestamp(value):
    try:
        dt = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.astimezone().replace(tzinfo=None) if dt.tzinfo else dt
    except (AttributeError, TypeError, ValueError):
        return None


def private_text(value, limit=280):
    """Redução de exposição; nomes ainda podem existir no extrato PRIVADO."""
    value = re.sub(r"<([\w:-]+)\b[^>]*>[\s\S]*?</\1>", " ", value)
    value = re.sub(r"(?i)\bBearer\s+[^\s`\"']+", "Bearer [omitido]", value)
    value = re.sub(r"(?i)\b(?:api[_-]?key|password|senha|secret|token)\s*[:=]\s*[^\s,;]+",
                   "credencial=[omitida]", value)
    value = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[email omitido]", value)
    value = re.sub(r"(?<!\w)(?:\+?55\s*)?\(?\d{2}\)?[ .-]*\d{4,5}[ .-]*\d{4}(?!\w)",
                   "[telefone omitido]", value)
    value = re.sub(r"\b[A-Za-z0-9_+/=-]{45,}\b", "[valor longo omitido]", value)
    return re.sub(r"\s+", " ", value).strip()[:limit]


def message_text(content):
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    return " ".join(x.get("text", "") for x in content
                    if isinstance(x, dict) and x.get("type") in ("text", "input_text", "output_text"))


def parse_codex(path):
    """Só trabalho concluído; fala real tem prioridade sobre envelopes delegados."""
    events, meta, cutoff = [], {}, None
    with path.open(encoding="utf-8", errors="replace") as stream:
        for line in stream:
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if not isinstance(event, dict):
                continue
            payload = event.get("payload")
            if not isinstance(payload, dict):
                continue
            events.append(event)
            kind, detail = event.get("type"), payload.get("type")
            if kind == "session_meta":
                meta = payload
            completed = (
                kind == "event_msg" and detail in ("task_complete", "task_aborted")
                or kind == "realtime_item" and detail == "realtime_session_closed"
                or kind == "response_item" and detail == "message"
                and payload.get("role") == "assistant"
                and payload.get("phase") in ("final", "final_answer")
            )
            ts = timestamp(event.get("timestamp"))
            if completed and ts and (cutoff is None or ts > cutoff):
                cutoff = ts
    if not meta or not cutoff:
        return None
    origin = json.dumps([meta.get("source"), meta.get("thread_source")]).lower()
    if any(marker in origin for marker in ("subagent", "sub_agent", "memory_consolidation")):
        return None
    candidates, outcomes, tools, skills = [], [], set(), set()
    has_voice = False
    for event in events:
        ts = timestamp(event.get("timestamp"))
        if not ts or ts > cutoff:
            continue
        p = event["payload"]
        kind, detail = event.get("type"), p.get("type")
        raw = ""
        from_voice = False
        if kind == "realtime_item" and detail == "transcript_segment" and p.get("role") == "user":
            raw = p.get("text", "")
            has_voice = True
            from_voice = True
        elif kind == "response_item" and detail == "message":
            text = message_text(p.get("content"))
            if p.get("role") == "user" and not text.lstrip().startswith(IGNORED_USER_PREFIXES):
                raw = text
            elif p.get("role") == "assistant" and p.get("phase") in ("final", "final_answer"):
                safe = private_text(text, 1000)
                if safe:
                    outcomes.append(safe)
        elif kind == "response_item" and detail in ("function_call", "custom_tool_call"):
            if p.get("name"):
                tools.add(str(p["name"]))
            arg = p.get("arguments", p.get("input", ""))
            skills.update(re.findall(r"(?:\.claude|\.agents|\.codex)/skills/([\w.-]+)", str(arg)))
        if raw:
            safe = private_text(raw)
            if safe:
                candidates.append((safe, from_voice))
    # Some releases promote voice text into a normal user message as well.
    spoken = {text for text, is_voice in candidates if is_voice}
    intents = [text for text, is_voice in candidates if is_voice or text not in spoken]
    if len(intents) < 2:
        return None
    session_id = str(meta.get("id") or meta.get("session_id") or path.stem)
    return {"source": "codex", "sessionId": session_id, "cwd": meta.get("cwd", ""),
            "intents": intents[-40:], "outcomes": outcomes[-3:], "nUser": len(intents),
            "tools": sorted(tools), "skills": sorted(skills), "voice": has_voice,
            "lastEvent": cutoff.astimezone(datetime.timezone.utc).isoformat()}


def export_sessions(roots, destination=BRIDGE_ROOT, lookback_days=30):
    host = re.sub(r"[^A-Za-z0-9._-]", "_", socket.gethostname())
    dest = destination / host
    dest.mkdir(parents=True, exist_ok=True, mode=0o700)
    destination.chmod(0o700)
    dest.chmod(0o700)
    cutoff = datetime.datetime.now() - datetime.timedelta(days=lookback_days)
    count = voice = unreadable = 0
    seen = set()
    for root in roots:
        if not root.is_dir():
            continue
        for path in root.rglob("*.jsonl"):
            if any(x.startswith(".") for x in path.relative_to(root).parts):
                continue
            if ".sync-conflict-" in path.name:
                continue
            try:
                if datetime.datetime.fromtimestamp(path.stat().st_mtime) < cutoff:
                    continue
                row = parse_codex(path)
            except (OSError, ValueError, TypeError):
                unreadable += 1
                continue
            if not row or timestamp(row["lastEvent"]) < cutoff or row["sessionId"] in seen:
                continue
            seen.add(row["sessionId"])
            row.update(schemaVersion=SCHEMA_VERSION, host=host)
            target = dest / (hashlib.sha256(row["sessionId"].encode()).hexdigest()[:24] + ".json")
            data = json.dumps(row, ensure_ascii=False, indent=2) + "\n"
            if not target.exists() or target.read_text() != data:
                temp = target.with_suffix(f".{os.getpid()}.tmp")
                with temp.open("w", encoding="utf-8") as stream:
                    os.chmod(temp, 0o600)
                    stream.write(data)
                temp.replace(target)
            count += 1
            voice += int(row["voice"])
    return {"sessions": count, "voiceSessions": voice, "unreadable": unreadable}


def load_digests(root):
    if not root or not root.is_dir():
        return
    newest = {}
    for path in root.glob("*/*.json"):
        if ".sync-conflict-" in path.name:
            continue
        try:
            row = json.loads(path.read_text())
            if (row.get("schemaVersion") == SCHEMA_VERSION and row.get("source") == "codex"
                    and row.get("sessionId") and timestamp(row.get("lastEvent"))
                    and isinstance(row.get("intents"), list) and row.get("nUser", 0) >= 2):
                prior = newest.get(row["sessionId"])
                if not prior or timestamp(row["lastEvent"]) > timestamp(prior["lastEvent"]):
                    newest[row["sessionId"]] = row
        except (OSError, ValueError, TypeError):
            print("AVISO: extrato Codex inválido ignorado; revise a ponte de curadoria.", file=sys.stderr)
    yield from newest.values()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--hook", action="store_true", help="Saída JSON neutra para Stop; sem continuar a conversa")
    ap.add_argument("--destination", type=Path, default=BRIDGE_ROOT)
    ap.add_argument("--lookback-days", type=int, default=30)
    args = ap.parse_args()
    if args.hook:
        # Never use a caller-supplied path to copy arbitrary files into the shared folder.
        try:
            json.load(sys.stdin)
        except (ValueError, OSError):
            pass
    result = export_sessions([Path.home() / ".codex/sessions", Path.home() / ".codex/archived_sessions"],
                             args.destination.expanduser(), args.lookback_days)
    print(json.dumps({} if args.hook else result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
