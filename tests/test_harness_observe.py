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
            self.assertEqual(report["turns_completed"], 1)
            self.assertEqual(report["turn_completion_rate"], 1.0)
            self.assertEqual(report["duration_ms"]["median"], 1200)
            self.assertEqual(report["time_to_first_token_ms"]["median"], 300)
            self.assertEqual(report["input_tokens"]["median"], 100)
            self.assertEqual(report["tool_calls"], {"exec": 1})
            serialized = json.dumps(report)
            self.assertNotIn("/private/project", serialized)

    def test_incomplete_turn_keeps_only_opaque_provenance(self) -> None:
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
            report = SESSION_SCANNER.scan_files([path])
            self.assertEqual(
                report["incomplete_turn_refs"],
                [{"session_id": "session-2", "turn_id": "turn-2"}],
            )

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
