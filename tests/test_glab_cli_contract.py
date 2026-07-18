import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
GLAB_ROOT = REPO_ROOT / "skills" / "glab"


def run_help(*args: str) -> str:
    result = subprocess.run(
        ["glab", *args, "--help"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout + result.stderr


def flags(help_text: str) -> set[str]:
    found = set()
    for token in help_text.replace(",", " ").split():
        if token.startswith("--"):
            found.add(token.split("=", 1)[0])
    return found


@unittest.skipUnless(shutil.which("glab"), "glab is not installed")
class GlabCliContractTests(unittest.TestCase):
    def test_installed_version_is_callable(self) -> None:
        result = subprocess.run(
            ["glab", "--version"], check=True, capture_output=True, text=True
        )
        self.assertIn("glab", result.stdout.lower())

    def test_issue_flags(self) -> None:
        list_flags = flags(run_help("issue", "list"))
        self.assertTrue({"--all", "--closed"} <= list_flags)
        self.assertNotIn("--state", list_flags)
        self.assertIn("--unlabel", flags(run_help("issue", "update")))
        self.assertNotIn("--yes", flags(run_help("issue", "delete")))

    def test_merge_request_flags_and_notes(self) -> None:
        create_flags = flags(run_help("mr", "create"))
        self.assertTrue(
            {"--source-branch", "--target-branch", "--description"} <= create_flags
        )
        self.assertTrue(
            {"--source", "--target", "--description-file"}.isdisjoint(create_flags)
        )
        merge_flags = flags(run_help("mr", "merge"))
        self.assertTrue({"--sha", "--remove-source-branch", "--yes"} <= merge_flags)

        note_help = run_help("mr", "note")
        for subcommand in ("list", "resolve", "reopen"):
            self.assertIn(subcommand, note_help)
        self.assertIn("--state", flags(run_help("mr", "note", "list")))

    def test_ci_and_artifact_contracts(self) -> None:
        list_flags = flags(run_help("ci", "list"))
        self.assertTrue({"--ref", "--per-page", "--sha", "--status"} <= list_flags)
        self.assertTrue({"--branch", "--limit"}.isdisjoint(list_flags))

        cancel_help = run_help("ci", "cancel")
        self.assertIn("pipeline", cancel_help)
        self.assertIn("job", cancel_help)

        artifact_help = run_help("job", "artifact")
        self.assertIn("<refName> <jobName>", artifact_help)
        self.assertIn("--path", flags(artifact_help))

    def test_api_and_repository_contracts(self) -> None:
        api_flags = flags(run_help("api"))
        self.assertTrue({"--raw-field", "--paginate", "--input"} <= api_flags)
        self.assertIn("archive", run_help("repo", "archive").lower())
        self.assertTrue(
            {"--direction", "--url"} <= flags(run_help("repo", "mirror"))
        )


class GlabSkillRegressionTests(unittest.TestCase):
    def test_docs_do_not_use_removed_command_forms(self) -> None:
        markdown = "\n".join(path.read_text() for path in GLAB_ROOT.rglob("*.md"))
        self.assertNotIn("glab ci cancel <pipeline-id>", markdown)
        self.assertNotIn("glab ci artifact", markdown)
        self.assertNotIn("glab repo mirror source-repo target-repo", markdown)

    def test_helpers_do_not_declare_local_at_top_level(self) -> None:
        for path in (GLAB_ROOT / "scripts").glob("*.sh"):
            self.assertNotIn("local ret=", path.read_text(), path.name)

    @unittest.skipUnless(shutil.which("jq"), "jq is not installed")
    def test_helpers_reach_terminal_success_with_mock_glab(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_glab = Path(tmpdir) / "glab"
            mock_glab.write_text(
                "#!/usr/bin/env bash\n"
                "if [[ \"$1 $2\" == \"ci status\" ]]; then\n"
                "  printf '%s\\n' '{\"status\":\"success\",\"id\":123}'\n"
                "elif [[ \"$1 $2\" == \"mr view\" ]]; then\n"
                "  printf '%s\\n' '{\"state\":\"merged\",\"merged_at\":\"2026-07-18T00:00:00Z\"}'\n"
                "else\n"
                "  exit 2\n"
                "fi\n"
            )
            mock_glab.chmod(mock_glab.stat().st_mode | stat.S_IXUSR)
            env = os.environ.copy()
            env["PATH"] = f"{tmpdir}:{env['PATH']}"

            cases = (
                ("glab-pipeline-watch.sh", "--timeout", "1"),
                ("glab-mr-await.sh", "1", "--timeout", "1"),
            )
            for script, *args in cases:
                result = subprocess.run(
                    ["bash", str(GLAB_ROOT / "scripts" / script), *args],
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                self.assertEqual(0, result.returncode, result.stderr or result.stdout)


if __name__ == "__main__":
    unittest.main()
