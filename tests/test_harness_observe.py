import importlib.util
import json
import tempfile
import unittest
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "harness-observe" / "scripts" / "harness_observe.py"
SPEC = importlib.util.spec_from_file_location("harness_observe", SCRIPT)
assert SPEC and SPEC.loader
HARNESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HARNESS)


def load_script(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CODEX_HOOK = load_script("codex_hook", SCRIPT.with_name("codex_hook.py"))
HOOK_INSTALLER = load_script("install_codex_hooks", SCRIPT.with_name("install_codex_hooks.py"))


def event(**overrides):
    value = {
        "schema_version": "1",
        "event_id": str(uuid.uuid4()),
        "timestamp": "2026-07-18T12:00:00Z",
        "run_id": "test-run",
        "event_type": "run_started",
        "status": "ok",
    }
    value.update(overrides)
    return value


class HarnessObserveTests(unittest.TestCase):
    def test_privacy_boundary_rejects_unknown_content_fields(self) -> None:
        for field in ("prompt", "response", "command", "path", "url", "tool_result"):
            with self.subTest(field=field), self.assertRaises(HARNESS.EventError):
                HARNESS.validate_event(event(**{field: "private value"}))

    def test_run_finished_requires_observable_outcome(self) -> None:
        with self.assertRaisesRegex(HARNESS.EventError, "outcome and terminal_state_met"):
            HARNESS.validate_event(event(event_type="run_finished"))
        HARNESS.validate_event(
            event(
                event_type="run_finished",
                phase="DONE",
                outcome="success",
                terminal_state_met=True,
            )
        )

    def test_failed_finish_requires_normalized_error_code(self) -> None:
        with self.assertRaisesRegex(HARNESS.EventError, "normalized error_code"):
            HARNESS.validate_event(
                event(event_type="run_finished", outcome="failed", terminal_state_met=False)
            )

    def test_append_summary_and_candidate_derivation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "events.jsonl"
            for index in range(2):
                HARNESS.append_event(
                    path,
                    event(
                        event_id=str(uuid.uuid4()),
                        run_id=f"run-{index}",
                        event_type="run_finished",
                        status="failed",
                        outcome="failed",
                        terminal_state_met=False,
                        task_kind="repo-change",
                        skills=["agent-preflight"],
                        error_code="terminal-state-not-verified",
                        metrics={"duration_ms": 1000 + index},
                    ),
                )
            events, errors = HARNESS.load_events(path)
            self.assertEqual(errors, [])
            summary = HARNESS.build_summary(events)
            self.assertEqual(summary["runs"], 2)
            self.assertEqual(summary["outcomes"], {"failed": 2})
            self.assertEqual(summary["terminal_state_rate"], 0.0)
            candidates = HARNESS.build_candidates(events, minimum_count=2)
            self.assertEqual(len(candidates["candidates"]), 1)
            self.assertEqual(candidates["candidates"][0]["count"], 2)
            self.assertEqual(candidates["candidates"][0]["state"], "proposed")

    def test_duplicate_finish_is_invalid_source_state(self) -> None:
        events = [
            event(
                event_id=str(uuid.uuid4()),
                event_type="run_finished",
                outcome="success",
                terminal_state_met=True,
            ),
            event(
                event_id=str(uuid.uuid4()),
                event_type="run_finished",
                outcome="success",
                terminal_state_met=True,
            ),
        ]
        self.assertRegex(HARNESS.cross_validate(events)[0], "expected one run_finished")

    def test_candidates_and_skill_counts_use_distinct_runs(self) -> None:
        repeated = [
            event(
                event_id=str(uuid.uuid4()),
                event_type="verification",
                skills=["artifact-verify"],
                error_code="archive-invalid",
            ),
            event(
                event_id=str(uuid.uuid4()),
                event_type="verification",
                skills=["artifact-verify"],
                error_code="archive-invalid",
            ),
        ]
        self.assertEqual(HARNESS.build_summary(repeated)["skills"], {"artifact-verify": 1})
        self.assertEqual(HARNESS.build_candidates(repeated, 2)["candidates"], [])

    def test_codex_hooks_ignore_content_and_are_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "events.jsonl"
            common = {
                "session_id": "session-private-id",
                "turn_id": "turn-private-id",
                "model": "gpt-test",
                "permission_mode": "default",
            }
            started = {**common, "hook_event_name": "UserPromptSubmit", "prompt": "secret prompt"}
            stopped = {
                **common,
                "hook_event_name": "Stop",
                "last_assistant_message": "secret response",
                "stop_hook_active": False,
            }
            CODEX_HOOK.process(started, path)
            CODEX_HOOK.process(started, path)
            CODEX_HOOK.process(stopped, path)
            CODEX_HOOK.process(stopped, path)
            raw = path.read_text(encoding="utf-8")
            self.assertNotIn("secret prompt", raw)
            self.assertNotIn("secret response", raw)
            self.assertNotIn("session-private-id", raw)
            events, errors = HARNESS.load_events(path)
            self.assertEqual(errors, [])
            self.assertEqual([item["event_type"] for item in events], ["turn_started", "turn_stopped"])
            self.assertIn("duration_ms", events[-1]["metrics"])

    def test_codex_hook_installer_preserves_other_hooks(self) -> None:
        document = {
            "description": "Existing hooks",
            "hooks": {"SessionStart": [{"hooks": [{"type": "command", "command": "existing"}]}]},
        }
        HOOK_INSTALLER.install(document, Path("/example/harness-observe/scripts/codex_hook.py"))
        self.assertTrue(HOOK_INSTALLER.configured(document))
        self.assertIn("SessionStart", document["hooks"])
        HOOK_INSTALLER.remove_ours(document)
        self.assertFalse(HOOK_INSTALLER.configured(document))
        self.assertIn("SessionStart", document["hooks"])

    def test_schema_and_trigger_evals_are_machine_readable(self) -> None:
        schema = json.loads(
            (ROOT / "skills" / "harness-observe" / "references" / "event.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertFalse(schema["additionalProperties"])
        self.assertIn("terminal_state_met", schema["properties"])
        evals = json.loads(
            (ROOT / "evals" / "harness-observe" / "evals.json").read_text(encoding="utf-8")
        )["evals"]
        self.assertEqual(len(evals), 6)
        self.assertTrue(any("harness-observe" in item["expected_skills"] for item in evals))
        self.assertTrue(any("harness-observe" in item["forbidden_skills"] for item in evals))


if __name__ == "__main__":
    unittest.main()
