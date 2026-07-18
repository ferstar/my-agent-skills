#!/usr/bin/env python3
"""Install or remove privacy-safe Codex lifecycle hooks."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any


STATUS_MESSAGE = "Recording content-free harness lifecycle event"


def default_config() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    return Path(codex_home).expanduser() / "hooks.json" if codex_home else Path.home() / ".codex" / "hooks.json"


def hook_script() -> Path:
    return Path(__file__).resolve().with_name("codex_hook.py")


def command_hook(script: Path) -> dict[str, Any]:
    escaped = str(script).replace('"', '\\"')
    windows = str(script).replace('"', '""')
    return {
        "type": "command",
        "command": f'python3 "{escaped}"',
        "commandWindows": f'py -3 "{windows}"',
        "timeout": 10,
        "statusMessage": STATUS_MESSAGE,
    }


def is_ours(handler: Any) -> bool:
    return isinstance(handler, dict) and (
        handler.get("statusMessage") == STATUS_MESSAGE
        or str(handler.get("command", "")).endswith('harness-observe/scripts/codex_hook.py"')
    )


def remove_ours(document: dict[str, Any]) -> None:
    hooks = document.setdefault("hooks", {})
    for event_name in ("UserPromptSubmit", "Stop"):
        groups = hooks.get(event_name, [])
        retained = []
        for group in groups:
            handlers = [handler for handler in group.get("hooks", []) if not is_ours(handler)]
            if handlers:
                copied = dict(group)
                copied["hooks"] = handlers
                retained.append(copied)
        if retained:
            hooks[event_name] = retained
        else:
            hooks.pop(event_name, None)


def install(document: dict[str, Any], script: Path) -> None:
    remove_ours(document)
    document.setdefault("description", "User lifecycle hooks.")
    hooks = document.setdefault("hooks", {})
    for event_name in ("UserPromptSubmit", "Stop"):
        hooks.setdefault(event_name, []).append({"hooks": [command_hook(script)]})


def read_document(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("hooks", {}), dict):
        raise ValueError("hooks config must be a JSON object with an optional hooks object")
    return value


def write_document(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(encoded)
        temporary = Path(handle.name)
    temporary.replace(path)


def configured(document: dict[str, Any]) -> bool:
    for event_name in ("UserPromptSubmit", "Stop"):
        groups = document.get("hooks", {}).get(event_name, [])
        if not any(is_ours(handler) for group in groups for handler in group.get("hooks", [])):
            return False
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("install", "uninstall", "check"))
    parser.add_argument("--config", type=Path, default=default_config())
    args = parser.parse_args(argv)
    try:
        document = read_document(args.config.expanduser())
        if args.action == "check":
            print("configured" if configured(document) else "not configured")
            return 0 if configured(document) else 1
        if args.action == "install":
            install(document, hook_script())
        else:
            remove_ours(document)
        write_document(args.config.expanduser(), document)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"{args.action}: {args.config.expanduser()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
