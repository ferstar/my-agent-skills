#!/usr/bin/env python3
"""Convert Codex lifecycle hook payloads into content-free harness events."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import sys
import uuid
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness_observe import append_event_once, default_log_path, load_events, utc_now


LABEL_CLEANUP = re.compile(r"[^A-Za-z0-9._-]+")
EVENT_NAMESPACE = uuid.UUID("fab5f0f6-1b81-4c4f-b61f-021f4a3544cb")


def safe_label(value: Any, fallback: str = "unknown") -> str:
    cleaned = LABEL_CLEANUP.sub("-", str(value or fallback)).strip("-._")
    return (cleaned or fallback)[:64]


def turn_key(payload: dict[str, Any]) -> str:
    opaque = f"{payload.get('session_id', '')}|{payload.get('turn_id', '')}"
    return "codex-" + hashlib.sha256(opaque.encode()).hexdigest()[:24]


def event_id(payload: dict[str, Any], event_type: str) -> str:
    identity = f"{payload.get('session_id', '')}|{payload.get('turn_id', '')}|{event_type}"
    return str(uuid.uuid5(EVENT_NAMESPACE, identity))


def common_event(payload: dict[str, Any], event_type: str) -> dict[str, Any]:
    return {
        "schema_version": "1",
        "event_id": event_id(payload, event_type),
        "timestamp": utc_now(),
        "run_id": turn_key(payload),
        "event_type": event_type,
        "status": "ok",
        "runtime": "codex",
        "model": safe_label(payload.get("model")),
        "permission_mode": safe_label(payload.get("permission_mode")),
        "source": "codex-hook",
    }


def turn_duration_ms(path: Path, run_id: str, stopped_at: str) -> int | None:
    events, _ = load_events(path)
    starts = [
        event
        for event in events
        if event["run_id"] == run_id and event["event_type"] == "turn_started"
    ]
    if not starts:
        return None
    start = dt.datetime.fromisoformat(starts[-1]["timestamp"].replace("Z", "+00:00"))
    stop = dt.datetime.fromisoformat(stopped_at.replace("Z", "+00:00"))
    return max(0, int((stop - start).total_seconds() * 1000))


def process(payload: dict[str, Any], path: Path | None = None) -> dict[str, Any] | None:
    hook_name = payload.get("hook_event_name")
    event_type = {
        "UserPromptSubmit": "turn_started",
        "Stop": "turn_stopped",
    }.get(hook_name)
    if event_type is None:
        return None
    event = common_event(payload, event_type)
    destination = path or default_log_path()
    if event_type == "turn_stopped":
        duration = turn_duration_ms(destination, event["run_id"], event["timestamp"])
        if duration is not None:
            event["metrics"] = {"duration_ms": duration}
    append_event_once(destination, event)
    return event


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        if isinstance(payload, dict):
            process(payload)
    except Exception:
        # Observation is deliberately fail-open and must never block the task.
        pass
    # Stop hooks require JSON stdout; an empty object is a no-op for all events.
    print("{}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
