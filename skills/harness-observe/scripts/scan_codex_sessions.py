#!/usr/bin/env python3
"""Derive content-free harness metrics from native Codex session JSONL."""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import json
import os
import statistics
import time
from pathlib import Path
from typing import Any, Iterable


DEFAULT_ACTIVE_GRACE_SECONDS = 30 * 60


def codex_home() -> Path:
    configured = os.environ.get("CODEX_HOME")
    return Path(configured).expanduser() if configured else Path.home() / ".codex"


def percentile(values: list[int], fraction: float) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int((len(ordered) - 1) * fraction)))
    return ordered[index]


def distribution(values: list[int]) -> dict[str, int | None]:
    return {
        "median": int(statistics.median(values)) if values else None,
        "p95": percentile(values, 0.95),
    }


def opaque_scope(value: Any) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    return hashlib.sha256(value.encode()).hexdigest()[:12]


def safe_counter(counter: collections.Counter[str]) -> dict[str, int]:
    return dict(counter.most_common())


def item_timestamp(item: dict[str, Any]) -> float | None:
    value = item.get("timestamp")
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.timestamp()


def touch_turn(turn: dict[str, Any], seen_at: float) -> None:
    turn["last_seen_at"] = max(turn.get("last_seen_at", seen_at), seen_at)


def scan_files(
    paths: Iterable[Path],
    *,
    now: float | None = None,
    active_grace_seconds: int = DEFAULT_ACTIVE_GRACE_SECONDS,
    record_cutoff: float | None = None,
) -> dict[str, Any]:
    if active_grace_seconds < 0:
        raise ValueError("active_grace_seconds must be non-negative")
    sessions: set[str] = set()
    scopes: set[str] = set()
    turns: dict[tuple[str, str], dict[str, Any]] = {}
    calls_seen: set[str] = set()
    tools: collections.Counter[str] = collections.Counter()
    invalid_lines = 0
    records_without_timestamp = 0
    files_scanned = 0

    for path in paths:
        files_scanned += 1
        session_id = path.stem.rsplit("-", 1)[-1]
        current_turn: str | None = None
        try:
            file_timestamp = path.stat().st_mtime
        except OSError:
            invalid_lines += 1
            continue
        try:
            handle = path.open(encoding="utf-8")
        except OSError:
            invalid_lines += 1
            continue
        with handle:
            for raw in handle:
                try:
                    item = json.loads(raw)
                except json.JSONDecodeError:
                    invalid_lines += 1
                    continue
                payload = item.get("payload")
                if not isinstance(payload, dict):
                    continue
                record_timestamp = item_timestamp(item)
                if record_timestamp is None:
                    records_without_timestamp += 1
                seen_at = file_timestamp if record_timestamp is None else record_timestamp
                item_type = item.get("type")
                payload_type = payload.get("type")
                if item_type == "session_meta":
                    supplied = payload.get("session_id") or payload.get("id")
                    if isinstance(supplied, str) and supplied:
                        session_id = supplied
                if record_cutoff is not None and (
                    record_timestamp is None or record_timestamp < record_cutoff
                ):
                    continue
                sessions.add(session_id)
                if item_type == "session_meta":
                    scope = opaque_scope(payload.get("cwd"))
                    if scope:
                        scopes.add(scope)
                    continue
                if item_type == "turn_context":
                    supplied = payload.get("turn_id")
                    if not isinstance(supplied, str) or not supplied:
                        continue
                    current_turn = supplied
                    turn = turns.setdefault((session_id, supplied), {})
                    touch_turn(turn, seen_at)
                    for source, target in (
                        ("model", "model"),
                        ("approval_policy", "approval"),
                    ):
                        value = payload.get(source)
                        if isinstance(value, str) and value:
                            turn[target] = value
                    sandbox = payload.get("sandbox_policy")
                    sandbox_type = sandbox.get("type") if isinstance(sandbox, dict) else sandbox
                    if isinstance(sandbox_type, str) and sandbox_type:
                        turn["sandbox"] = sandbox_type
                    continue
                if item_type == "event_msg" and payload_type == "task_started":
                    turn_id = payload.get("turn_id")
                    if isinstance(turn_id, str) and turn_id:
                        current_turn = turn_id
                        turn = turns.setdefault((session_id, turn_id), {})
                        turn["started"] = True
                        touch_turn(turn, seen_at)
                    continue
                if item_type == "event_msg" and payload_type == "task_complete":
                    turn_id = payload.get("turn_id")
                    if not isinstance(turn_id, str) or not turn_id:
                        continue
                    current_turn = turn_id
                    turn = turns.setdefault((session_id, turn_id), {})
                    turn["started"] = True
                    turn["completed"] = True
                    touch_turn(turn, seen_at)
                    for source, target in (
                        ("duration_ms", "duration_ms"),
                        ("time_to_first_token_ms", "ttft_ms"),
                    ):
                        value = payload.get(source)
                        if isinstance(value, int) and value >= 0:
                            turn[target] = value
                    continue
                if item_type == "event_msg" and payload_type == "turn_aborted":
                    supplied = payload.get("turn_id")
                    turn_id = supplied if isinstance(supplied, str) and supplied else current_turn
                    if turn_id:
                        current_turn = turn_id
                        turn = turns.setdefault((session_id, turn_id), {})
                        turn["started"] = True
                        turn["aborted"] = True
                        touch_turn(turn, seen_at)
                    continue
                if item_type == "event_msg" and payload_type == "token_count" and current_turn:
                    info = payload.get("info")
                    usage = info.get("last_token_usage") if isinstance(info, dict) else None
                    if isinstance(usage, dict):
                        turn = turns.setdefault((session_id, current_turn), {})
                        touch_turn(turn, seen_at)
                        for source, target in (
                            ("input_tokens", "input_tokens"),
                            ("output_tokens", "output_tokens"),
                        ):
                            value = usage.get(source)
                            if isinstance(value, int) and value >= 0:
                                turn[target] = value
                    continue
                if item_type == "response_item" and payload_type in {"custom_tool_call", "function_call"}:
                    call_id = payload.get("call_id") or payload.get("id")
                    name = payload.get("name")
                    if not isinstance(call_id, str) or call_id in calls_seen:
                        continue
                    calls_seen.add(call_id)
                    if isinstance(name, str) and name:
                        tools[name] += 1
                    if current_turn:
                        turn = turns.setdefault((session_id, current_turn), {})
                        touch_turn(turn, seen_at)
                        turn["tool_calls"] = turn.get("tool_calls", 0) + 1
                    continue
                if current_turn:
                    touch_turn(turns.setdefault((session_id, current_turn), {}), seen_at)

    started = [turn for turn in turns.values() if turn.get("started")]
    completed = [turn for turn in started if turn.get("completed")]
    aborted = [turn for turn in started if not turn.get("completed") and turn.get("aborted")]
    active_cutoff = (time.time() if now is None else now) - active_grace_seconds
    active_keys = {
        key
        for key, turn in turns.items()
        if turn.get("started")
        and not turn.get("completed")
        and not turn.get("aborted")
        and turn.get("last_seen_at", 0) >= active_cutoff
    }
    orphaned_keys = {
        key
        for key, turn in turns.items()
        if turn.get("started")
        and not turn.get("completed")
        and not turn.get("aborted")
        and turn.get("last_seen_at", 0) < active_cutoff
    }
    settled_count = len(completed) + len(aborted) + len(orphaned_keys)
    durations = [turn["duration_ms"] for turn in completed if "duration_ms" in turn]
    ttft = [turn["ttft_ms"] for turn in completed if "ttft_ms" in turn]
    input_tokens = [turn["input_tokens"] for turn in completed if "input_tokens" in turn]
    output_tokens = [turn["output_tokens"] for turn in completed if "output_tokens" in turn]
    tool_counts = [turn.get("tool_calls", 0) for turn in completed]
    models = collections.Counter(turn["model"] for turn in started if "model" in turn)
    approvals = collections.Counter(turn["approval"] for turn in started if "approval" in turn)
    sandboxes = collections.Counter(turn["sandbox"] for turn in started if "sandbox" in turn)
    active_refs = [
        {"session_id": session_id, "turn_id": turn_id}
        for session_id, turn_id in turns
        if (session_id, turn_id) in active_keys
    ]
    orphaned_refs = [
        {"session_id": session_id, "turn_id": turn_id}
        for session_id, turn_id in turns
        if (session_id, turn_id) in orphaned_keys
    ]
    return {
        "schema_version": "2",
        "files_scanned": files_scanned,
        "sessions": len(sessions),
        "scopes": len(scopes),
        "turns_started": len(started),
        "turns_completed": len(completed),
        "turns_aborted": len(aborted),
        "turns_active": len(active_keys),
        "turns_orphaned": len(orphaned_keys),
        "turn_completion_rate": round(len(completed) / settled_count, 4) if settled_count else None,
        "turn_terminal_rate": (
            round((len(completed) + len(aborted)) / settled_count, 4)
            if settled_count
            else None
        ),
        "invalid_lines": invalid_lines,
        "records_without_timestamp": records_without_timestamp,
        "duration_ms": distribution(durations),
        "time_to_first_token_ms": distribution(ttft),
        "input_tokens": distribution(input_tokens),
        "output_tokens": distribution(output_tokens),
        "tool_calls_per_turn": distribution(tool_counts),
        "tool_calls": safe_counter(tools),
        "models": safe_counter(models),
        "approval_policies": safe_counter(approvals),
        "sandbox_policies": safe_counter(sandboxes),
        "active_turn_refs": active_refs[-20:],
        "orphaned_turn_refs": orphaned_refs[-20:],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sessions-root", type=Path, default=codex_home() / "sessions")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--active-grace-minutes", type=int, default=30)
    args = parser.parse_args()
    if args.days < 1:
        parser.error("--days must be positive")
    if args.active_grace_minutes < 0:
        parser.error("--active-grace-minutes must be non-negative")
    cutoff = dt.datetime.now().timestamp() - args.days * 86400
    root = args.sessions_root.expanduser()
    paths = sorted(
        path for path in root.rglob("*.jsonl") if path.is_file() and path.stat().st_mtime >= cutoff
    ) if root.exists() else []
    report = scan_files(
        paths,
        active_grace_seconds=args.active_grace_minutes * 60,
        record_cutoff=cutoff,
    )
    report["window_days"] = args.days
    report["active_grace_minutes"] = args.active_grace_minutes
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
