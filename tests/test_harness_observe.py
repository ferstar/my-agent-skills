import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCANNER = ROOT / "skills" / "harness-observe" / "scripts" / "scan_codex_sessions.py"
SPEC = importlib.util.spec_from_file_location("scan_codex_sessions", SCANNER)
assert SPEC and SPEC.loader
SESSION_SCANNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SESSION_SCANNER)


class HarnessObserveTests(unittest.TestCase):
    def test_native_session_scanner_derives_content_free_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "rollout-test-session.jsonl"
            records = [
                {
                    "type": "session_meta",
                    "payload": {"session_id": "session-1", "cwd": "/private/project"},
                },
                {
                    "type": "turn_context",
                    "payload": {
                        "turn_id": "turn-1",
                        "model": "gpt-test",
                        "approval_policy": "never",
                        "sandbox_policy": {"type": "workspace-write"},
                    },
                },
                {
                    "type": "event_msg",
                    "payload": {"type": "task_started", "turn_id": "turn-1"},
                },
                {
                    "type": "response_item",
                    "payload": {"type": "custom_tool_call", "call_id": "call-1", "name": "exec"},
                },
                {
                    "type": "event_msg",
                    "payload": {
                        "type": "token_count",
                        "info": {"last_token_usage": {"input_tokens": 100, "output_tokens": 20}},
                    },
                },
                {
                    "type": "event_msg",
                    "payload": {
                        "type": "task_complete",
                        "turn_id": "turn-1",
                        "duration_ms": 1200,
                        "time_to_first_token_ms": 300,
                    },
                },
            ]
            path.write_text("".join(json.dumps(item) + "\n" for item in records), encoding="utf-8")
            report = SESSION_SCANNER.scan_files([path])
            self.assertEqual(report["schema_version"], "2")
            self.assertEqual(report["turns_completed"], 1)
            self.assertEqual(report["turns_aborted"], 0)
            self.assertEqual(report["turns_active"], 0)
            self.assertEqual(report["turns_orphaned"], 0)
            self.assertEqual(report["turn_completion_rate"], 1.0)
            self.assertEqual(report["turn_terminal_rate"], 1.0)
            self.assertEqual(report["duration_ms"]["median"], 1200)
            self.assertEqual(report["time_to_first_token_ms"]["median"], 300)
            self.assertEqual(report["input_tokens"]["median"], 100)
            self.assertEqual(report["tool_calls"], {"exec": 1})
            serialized = json.dumps(report)
            self.assertNotIn("/private/project", serialized)

    def test_orphaned_turn_keeps_only_opaque_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "rollout-test-session.jsonl"
            records = [
                {"type": "session_meta", "payload": {"session_id": "session-2"}},
                {
                    "type": "event_msg",
                    "payload": {"type": "task_started", "turn_id": "turn-2"},
                },
            ]
            path.write_text("".join(json.dumps(item) + "\n" for item in records), encoding="utf-8")
            report = SESSION_SCANNER.scan_files(
                [path], now=path.stat().st_mtime + 120, active_grace_seconds=60
            )
            self.assertEqual(
                report["orphaned_turn_refs"],
                [{"session_id": "session-2", "turn_id": "turn-2"}],
            )
            self.assertEqual(report["turns_orphaned"], 1)
            self.assertEqual(report["active_turn_refs"], [])

    def test_turn_states_separate_completed_aborted_active_and_orphaned(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            paths = []
            cases = (
                ("completed", "task_complete", "2026-01-01T00:00:00Z"),
                ("aborted", "turn_aborted", "2026-01-01T00:00:00Z"),
                ("active", None, "2026-01-01T01:59:30Z"),
                ("orphaned", None, "2026-01-01T00:00:00Z"),
            )
            for name, terminal, timestamp in cases:
                path = Path(temp) / f"rollout-{name}.jsonl"
                records = [
                    {
                        "timestamp": timestamp,
                        "type": "session_meta",
                        "payload": {"session_id": f"session-{name}"},
                    },
                    {
                        "timestamp": timestamp,
                        "type": "event_msg",
                        "payload": {"type": "task_started", "turn_id": f"turn-{name}"},
                    },
                ]
                if terminal:
                    records.append(
                        {
                            "timestamp": timestamp,
                            "type": "event_msg",
                            "payload": {"type": terminal, "turn_id": f"turn-{name}"},
                        }
                    )
                path.write_text(
                    "".join(json.dumps(item) + "\n" for item in records), encoding="utf-8"
                )
                paths.append(path)

            now = SESSION_SCANNER.dt.datetime.fromisoformat(
                "2026-01-01T02:00:00+00:00"
            ).timestamp()
            report = SESSION_SCANNER.scan_files(paths, now=now, active_grace_seconds=60)

            self.assertEqual(report["turns_started"], 4)
            self.assertEqual(report["turns_completed"], 1)
            self.assertEqual(report["turns_aborted"], 1)
            self.assertEqual(report["turns_active"], 1)
            self.assertEqual(report["turns_orphaned"], 1)
            self.assertEqual(report["turn_completion_rate"], 0.3333)
            self.assertEqual(report["turn_terminal_rate"], 0.6667)
            self.assertEqual(
                report["active_turn_refs"],
                [{"session_id": "session-active", "turn_id": "turn-active"}],
            )
            self.assertEqual(
                report["orphaned_turn_refs"],
                [{"session_id": "session-orphaned", "turn_id": "turn-orphaned"}],
            )

    def test_record_cutoff_excludes_old_turns_from_recently_modified_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "rollout-long-lived-session.jsonl"
            records = []
            for name, timestamp in (
                ("old", "2026-01-01T00:00:00Z"),
                ("recent", "2026-01-08T00:00:00Z"),
            ):
                records.extend(
                    [
                        {
                            "timestamp": timestamp,
                            "type": "session_meta",
                            "payload": {"session_id": "session-long-lived"},
                        },
                        {
                            "timestamp": timestamp,
                            "type": "event_msg",
                            "payload": {"type": "task_started", "turn_id": f"turn-{name}"},
                        },
                        {
                            "timestamp": timestamp,
                            "type": "response_item",
                            "payload": {
                                "type": "custom_tool_call",
                                "call_id": f"call-{name}",
                                "name": name,
                            },
                        },
                        {
                            "timestamp": timestamp,
                            "type": "event_msg",
                            "payload": {"type": "task_complete", "turn_id": f"turn-{name}"},
                        },
                    ]
                )
            path.write_text(
                "".join(json.dumps(item) + "\n" for item in records), encoding="utf-8"
            )

            cutoff = SESSION_SCANNER.dt.datetime.fromisoformat(
                "2026-01-07T00:00:00+00:00"
            ).timestamp()
            report = SESSION_SCANNER.scan_files([path], record_cutoff=cutoff)

            self.assertEqual(report["turns_started"], 1)
            self.assertEqual(report["turns_completed"], 1)
            self.assertEqual(report["tool_calls"], {"recent": 1})
            self.assertEqual(report["records_without_timestamp"], 0)

    def test_trigger_evals_cover_autonomy_privacy_and_non_trigger(self) -> None:
        evals = json.loads(
            (ROOT / "evals" / "harness-observe" / "evals.json").read_text(encoding="utf-8")
        )["evals"]
        ids = {item["id"] for item in evals}
        self.assertEqual(len(evals), 6)
        self.assertIn("scheduled-autonomous-audit", ids)
        self.assertIn("full-transcript-export-is-rejected", ids)
        self.assertIn("ordinary-task-does-not-trigger", ids)
        self.assertFalse(any(item["id"].startswith("hook-") for item in evals))


if __name__ == "__main__":
    unittest.main()
