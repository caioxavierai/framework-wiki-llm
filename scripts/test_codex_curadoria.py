"""Regressões da ponte Codex; fixtures artificiais, sem ler sessões pessoais."""
import contextlib
import datetime
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import wiki_codex_bridge as bridge
import wiki_sessions_digest as digest


def event(kind, payload, second=0):
    return {"type": kind, "timestamp": f"2026-09-13T10:00:{second:02d}Z", "payload": payload}


def user(text, second):
    return event("response_item", {"type": "message", "role": "user",
                                  "content": [{"type": "input_text", "text": text}]}, second)


def meta(**extra):
    return event("session_meta", {"id": "fixture-session", "cwd": "/test/projeto-a", "source": "cli", **extra})


def final(second=20):
    return event("response_item", {"type": "message", "role": "assistant", "phase": "final_answer",
                                  "content": [{"type": "output_text", "text": "Decisão fictícia verificada."}]}, second)


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def session(self, events, name="session.jsonl"):
        path = self.root / name
        path.write_text("\n".join(json.dumps(x) for x in events) + "\n")
        return path

    def base(self):
        return [meta(), user("Analise o fluxo fictício.", 1), user("A proposta está aprovada para o exemplo.", 2), final()]

    def test_codex_ignores_injected_guidance_and_keeps_real_intents(self):
        rows = [meta(), user("# AGENTS.md instructions\nInstrução de configuração", 1),
                user("<environment_context>config</environment_context>", 2),
                user("<recommended_plugins>plugins</recommended_plugins>", 3),
                user("Primeira pergunta real", 4), user("Segunda pergunta real", 5), final()]
        row = bridge.parse_codex(self.session(rows))
        self.assertEqual(row["nUser"], 2)
        self.assertEqual(row["intents"], ["Primeira pergunta real", "Segunda pergunta real"])

    def test_voice_skips_delegation_and_duplicate_promotion(self):
        rows = [meta(), event("realtime_item", {"type": "transcript_segment", "role": "user", "text": "Primeira fala"}, 1),
                user("Primeira fala", 2), user("<realtime_delegation>Primeira fala e instruções extras</realtime_delegation>", 3),
                event("realtime_item", {"type": "transcript_segment", "role": "user", "text": "Segunda fala"}, 4), final()]
        row = bridge.parse_codex(self.session(rows))
        self.assertTrue(row["voice"])
        self.assertEqual(row["intents"], ["Primeira fala", "Segunda fala"])

    def test_voice_repeated_real_turns_are_preserved(self):
        rows = [meta()] + [event("realtime_item", {"type": "transcript_segment", "role": "user", "text": "Pode seguir"}, i) for i in (1, 2)] + [final()]
        self.assertEqual(bridge.parse_codex(self.session(rows))["nUser"], 2)

    def test_voice_without_delegated_task_is_read_after_close(self):
        rows = [meta()] + [event("realtime_item", {"type": "transcript_segment", "role": "user", "text": f"Fala {i}"}, i) for i in (1, 2)]
        rows.append(event("realtime_item", {"type": "realtime_session_closed"}, 3))
        self.assertTrue(bridge.parse_codex(self.session(rows))["voice"])

    def test_unfinished_turn_is_not_exported(self):
        path = self.session(self.base() + [user("Ainda estou decidindo", 30)])
        self.assertEqual(bridge.parse_codex(path)["nUser"], 2)
        self.assertIsNone(bridge.parse_codex(self.session(self.base()[:-1], "active.jsonl")))

    def test_exported_timestamp_preserves_the_instant_across_timezones(self):
        row = bridge.parse_codex(self.session(self.base()))
        actual = datetime.datetime.fromisoformat(row["lastEvent"])
        self.assertIsNotNone(actual.tzinfo)
        self.assertEqual(actual, datetime.datetime(2026, 9, 13, 10, 0, 20, tzinfo=datetime.timezone.utc))

    def test_subagents_are_excluded(self):
        rows = self.base(); rows[0] = meta(source={"subagent": {"parent_thread_id": "parent"}})
        self.assertIsNone(bridge.parse_codex(self.session(rows)))

    def test_malformed_tail_does_not_discard_finished_work(self):
        path = self.session(self.base())
        with path.open("a") as stream: stream.write('{"unfinished":')
        self.assertEqual(bridge.parse_codex(path)["nUser"], 2)

    def test_tools_and_skill_paths_are_extracted(self):
        rows = self.base(); rows.insert(3, event("response_item", {"type": "function_call", "name": "exec_command", "arguments": '{"cmd":"cat ~/.claude/skills/minha-skill/SKILL.md"}'}, 3))
        row = bridge.parse_codex(self.session(rows))
        self.assertEqual(row["tools"], ["exec_command"])
        self.assertEqual(row["skills"], ["minha-skill"])

    def test_redacts_contact_and_secret_examples(self):
        text = bridge.private_text("email teste@example.invalid telefone +55 11 99999-0000 token=FAKE_SECRET Bearer FAKE_BEARER", 500)
        for value in ("teste@example.invalid", "99999-0000", "FAKE_SECRET", "FAKE_BEARER"):
            self.assertNotIn(value, text)

    def test_existing_claude_format_is_preserved(self):
        rows = [{"type": "user", "timestamp": "2026-09-13T10:00:00Z", "message": {"content": "Primeira pergunta"}},
                {"type": "user", "timestamp": "2026-09-13T10:00:01Z", "message": {"content": [{"type": "text", "text": "Segunda pergunta"}]}},
                {"type": "assistant", "timestamp": "2026-09-13T10:00:02Z", "message": {"content": [{"type": "tool_use", "name": "Read"}]}}]
        row = digest.parse(self.session(rows))
        self.assertEqual(row["nUser"], 2); self.assertEqual(row["tools"], ["Read"])

    def test_nested_message_format_is_preserved(self):
        rows = [{"type": "message", "timestamp": f"2026-09-13T10:00:0{i}Z", "message": {"role": "user", "content": [{"type": "text", "text": f"Pergunta {i}"}]}} for i in (1, 2)]
        rows.append({"type": "message", "timestamp": "2026-09-13T10:00:03Z", "message": {"role": "assistant", "content": [{"type": "toolCall", "name": "exec"}]}})
        row = digest.parse(self.session(rows))
        self.assertEqual(row["nUser"], 2); self.assertEqual(row["tools"], ["exec"])

    def test_export_is_private_and_idempotent(self):
        self.session(self.base())
        dest = self.root / "exports"
        first = bridge.export_sessions([self.root], dest, lookback_days=36500)
        exported = next(dest.glob("*/*.json")); before = exported.stat().st_mtime_ns
        bridge.export_sessions([self.root], dest, lookback_days=36500)
        self.assertEqual(first["sessions"], 1)
        self.assertEqual(exported.stat().st_mode & 0o777, 0o600)
        self.assertEqual(exported.stat().st_mtime_ns, before)

    def make_digest(self, session_id="late", last_event="2026-09-10T10:00:00", host="host"):
        dest = self.root / "digests" / host; dest.mkdir(parents=True, exist_ok=True)
        row = {"schemaVersion": 1, "source": "codex", "sessionId": session_id,
               "cwd": "/test/projeto-a", "lastEvent": last_event, "nUser": 2,
               "intents": ["Pergunta um", "Pergunta dois"], "tools": [], "skills": []}
        (dest / (session_id + ".json")).write_text(json.dumps(row))

    def run_digest(self, *extra):
        state = self.root / "state.json"
        if not state.exists(): state.write_text(json.dumps({"last_run": "2026-09-12T10:00:00"}))
        args = ["digest", "--dirs", str(self.root / "empty"), "--codex-digests", str(self.root / "digests"), "--json", *extra]
        output = io.StringIO()
        with patch.object(digest, "STATE", state), patch.object(digest, "USO", self.root / "usage.json"), patch.object(digest, "CODEX_REVIEWED", self.root / "reviewed.json"), patch.object(sys, "argv", args), contextlib.redirect_stdout(output), contextlib.redirect_stderr(io.StringIO()):
            digest.main()
        return json.loads(output.getvalue())

    def test_late_sync_is_included_despite_advanced_global_window(self):
        self.make_digest()
        self.assertEqual(self.run_digest()["count"], 1)

    def test_commit_marks_only_the_reviewed_cutoff(self):
        self.make_digest("before", "2026-09-12T09:00:00")
        self.make_digest("after", "2026-09-13T10:00:00")
        result = self.run_digest("--commit", "--as-of", "2026-09-12T12:00:00")
        self.assertEqual(result["count"], 1)
        reviewed = json.loads((self.root / "reviewed.json").read_text())
        self.assertIn("before", reviewed); self.assertNotIn("after", reviewed)
        self.assertEqual(self.run_digest()["count"], 1)

    def test_same_session_on_two_hosts_uses_newest_snapshot(self):
        self.make_digest("same", "2026-09-10T10:00:00", "old-host")
        self.make_digest("same", "2026-09-11T10:00:00", "new-host")
        rows = list(bridge.load_digests(self.root / "digests"))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["lastEvent"], "2026-09-11T10:00:00")


if __name__ == "__main__":
    unittest.main()
