#!/usr/bin/env python3
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "skills" / "rapidocr" / "scripts" / "run_rapidocr.py"
SKILL_MD = REPO_ROOT / "skills" / "rapidocr" / "SKILL.md"


def run_rapidocr(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        text=True,
        capture_output=True,
        check=False,
    )


def test_missing_image_path_exits_with_clear_error() -> None:
    result = run_rapidocr()
    assert result.returncode == 2
    assert "Missing local image path" in result.stderr


def test_help_is_available() -> None:
    result = run_rapidocr("--help")
    assert result.returncode == 0
    assert "Run RapidOCR" in result.stdout


def test_skill_docs_use_uv_tool_and_review_features() -> None:
    content = SKILL_MD.read_text(encoding="utf-8")
    assert "uv tool install --force rapidocr --with onnxruntime" in content
    assert not re.search(r"python\s+-m\s+pip\s+install\s+rapidocr", content)
    assert "review.low_confidence" in content
    assert "--table" in content


if __name__ == "__main__":
    for test in (
        test_missing_image_path_exits_with_clear_error,
        test_help_is_available,
        test_skill_docs_use_uv_tool_and_review_features,
    ):
        test()
    print("rapidocr smoke ok")
