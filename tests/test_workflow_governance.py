import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"


def skill_text(name: str) -> str:
    return (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")


class WorkflowGovernanceTests(unittest.TestCase):
    def test_skill_metadata_is_publication_ready(self) -> None:
        for path in SKILLS.glob("*/SKILL.md"):
            text = path.read_text(encoding="utf-8")
            self.assertLessEqual(len(text.splitlines()), 500, f"{path}: body is too long")
            match = re.match(r"^---\n(?P<header>.*?)\n---\n", text, re.DOTALL)
            self.assertIsNotNone(match, f"{path}: missing YAML frontmatter")
            header = match.group("header")
            name = re.search(r"^name:\s*([^\n]+)$", header, re.MULTILINE)
            description = re.search(r"^description:\s*([^\n]+)$", header, re.MULTILINE)
            self.assertIsNotNone(name, f"{path}: missing name")
            self.assertIsNotNone(description, f"{path}: missing description")
            self.assertRegex(name.group(1), r"^[a-z0-9-]{1,64}$")
            self.assertLessEqual(len(description.group(1)), 1024)

    def test_public_skill_docs_do_not_leak_private_conventions(self) -> None:
        forbidden = {
            "non-example GitLab host": re.compile(
                r"gitlab\.(?!com\b|example\.(?:com|org)\b)[a-z0-9.-]+", re.IGNORECASE
            ),
            "macOS user absolute path": re.compile(r"/Users/(?!<username>)[^/<\s]+"),
            "Windows user absolute path": re.compile(r"C:\\Users\\(?!<username>)[^\\<\s]+", re.IGNORECASE),
            "product-specific defaults section": re.compile(r"^##\s+[^\n]+\s+Defaults\s*$", re.MULTILINE),
        }
        checked = (
            list(SKILLS.rglob("*.md"))
            + list((ROOT / "docs").rglob("*.md"))
            + list((ROOT / "evals").rglob("*.json"))
            + [ROOT / "AGENTS.md"]
        )
        for path in checked:
            text = path.read_text(encoding="utf-8")
            for label, pattern in forbidden.items():
                self.assertIsNone(pattern.search(text), f"{path}: leaked {label}")
        host_alias = re.compile(r"\bmy-(?!agent-skills\b)[a-z0-9-]+\b", re.IGNORECASE)
        for path in (SKILLS / "remote-health" / "SKILL.md", ROOT / "AGENTS.md"):
            self.assertIsNone(host_alias.search(path.read_text(encoding="utf-8")), f"{path}: leaked host alias")

    def test_checkpoint_contract_is_shared_by_preflight_and_ship_loop(self) -> None:
        required = [
            "DISCOVER | DECIDE | IMPLEMENT | VERIFY | SHIP | DONE",
            "objective:",
            "scope:",
            "authority:",
            "evidence:",
            "changes:",
            "verification:",
            "terminal_state:",
            "next:",
            "drift_facts:",
        ]
        for name in ("agent-preflight", "codex-ship-loop"):
            text = skill_text(name)
            for item in required:
                self.assertIn(item, text, f"{name}: missing checkpoint field {item}")
            self.assertRegex(text, r"[Oo]n resume.*drift|resume.*drift-prone")

    def test_prompt_contract_has_independent_authority_and_terminal_state(self) -> None:
        path = ROOT / "docs/prompt-workflow-contract.md"
        text = path.read_text(encoding="utf-8")
        for item in (
            "objective:",
            "evidence:",
            "scope:",
            "authority:",
            "terminal_state:",
            "read-only | edit | push | merge | deploy | workflow-state | publish | cleanup",
            "Authority is not transitive",
            "Read back every mutated remote object",
        ):
            self.assertIn(item, text)
        for name in ("agent-preflight", "codex-ship-loop"):
            self.assertIn("docs/prompt-workflow-contract.md", skill_text(name))

    def test_chinese_readme_and_prompt_contract_are_first_class(self) -> None:
        english = (ROOT / "README.md").read_text(encoding="utf-8")
        chinese = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
        chinese_contract = (
            ROOT / "docs/prompt-workflow-contract.zh-CN.md"
        ).read_text(encoding="utf-8")
        self.assertIn("README.zh-CN.md", english)
        self.assertIn("README.md", chinese)
        self.assertIn("Prompt 工作流方法论", chinese)
        self.assertIn("prompt-workflow-contract.zh-CN.md", chinese)
        for item in (
            "objective:",
            "evidence:",
            "scope:",
            "authority:",
            "terminal_state:",
            "权限不传递",
        ):
            self.assertIn(item, chinese_contract)

    def test_prompt_contract_fixtures_cover_progressive_authority(self) -> None:
        path = ROOT / "evals/prompt-workflow-contract/evals.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(
            {item["id"] for item in data["evals"]},
            {
                "terse-review-is-read-only",
                "fix-and-push-stops-before-merge",
                "merge-with-testing-handoff",
                "exact-sha-deploy-terminal-state",
                "resume-refreshes-only-drift",
            },
        )
        for item in data["evals"]:
            self.assertTrue(item["prompt"])
            self.assertTrue(item["expected_output"])
            self.assertGreaterEqual(len(item["assertions"]), 4)

    def test_redundant_legacy_skills_are_removed(self) -> None:
        for name in ("gitlab-mr-context", "path-verify"):
            self.assertFalse((SKILLS / name).exists())
        workflows = (SKILLS / "glab" / "references" / "workflows.md").read_text(encoding="utf-8")
        self.assertIn("Context and merge-readiness snapshot", workflows)

    def test_artifact_verification_is_read_only_and_separate(self) -> None:
        artifact = skill_text("artifact-verify")
        release = skill_text("release-deploy-preflight")
        self.assertIn("do not use to trigger builds, releases, deploys", artifact)
        self.assertIn("Use `artifact-verify`", release)
        self.assertIn("complete artifact", artifact)
        self.assertIn("archive", artifact)
        self.assertIn("lock", artifact)

    def test_link_scripts_preserve_source_to_install_direction(self) -> None:
        shell = (ROOT / "scripts/link-user-skills.sh").read_text(encoding="utf-8")
        powershell = (ROOT / "scripts/link-user-skills.ps1").read_text(encoding="utf-8")
        self.assertIn('skills_dir="$repo_root/skills"', shell)
        self.assertIn('ln -s "$skill" "$target"', shell)
        self.assertNotIn('ln -s "$target" "$skill"', shell)
        self.assertIn("New-Item -ItemType Junction -Path $Target -Target $Skill", powershell)
        self.assertNotIn("New-Item -ItemType Junction -Path $Skill -Target $Target", powershell)

    def test_standalone_public_skills_keep_one_upstream_source(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("https://github.com/ferstar/fast-context", readme)
        self.assertFalse((SKILLS / "fast-context").exists())

    def test_required_trigger_fixtures_are_present(self) -> None:
        path = ROOT / "evals/workflow-governance/evals.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        ids = {item["id"] for item in data["evals"]}
        self.assertEqual(
            ids,
            {
                "review-only",
                "merge-issue-to-test",
                "exact-sha-deploy-health",
                "ci-first-failure",
                "source-install-link-direction",
                "artifact-content-verification",
                "agent-boundary-hardening",
                "explicit-goal-definition",
                "tianbot-current-docs",
            },
        )
        for item in data["evals"]:
            self.assertTrue(item["prompt"])
            self.assertTrue(item["expected_output"])
            self.assertGreaterEqual(len(item["assertions"]), 3)


if __name__ == "__main__":
    unittest.main()
