#!/usr/bin/env python3
"""Privacy-safe local JSONL observability for an agent harness."""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import json
import os
import re
import statistics
import sys
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable, Iterator


SCHEMA_VERSION = "1"
EVENT_TYPES = (
    "run_started",
    "turn_started",
    "turn_stopped",
    "phase_changed",
    "guard_decision",
    "verification",
    "run_finished",
    "feedback",
)
STATUSES = ("ok", "failed", "blocked", "skipped")
PHASES = ("DISCOVER", "DECIDE", "IMPLEMENT", "VERIFY", "SHIP", "DONE")
OUTCOMES = ("success", "partial", "failed", "blocked", "cancelled")
AUTHORITIES = (
    "read-only",
    "edit",
    "push",
    "merge",
    "deploy",
    "workflow-state",
    "publish",
    "cleanup",
)
DECISIONS = ("allow", "deny", "not-required")
FEEDBACK_VALUES = ("accepted", "reworked", "rejected")
METRIC_FIELDS = (
    "duration_ms",
    "input_tokens",
    "output_tokens",
    "tool_calls",
    "retries",
    "evidence_count",
    "changed_files_count",
)
ALLOWED_FIELDS = {
    "schema_version",
    "event_id",
    "timestamp",
    "run_id",
    "event_type",
    "status",
    "phase",
    "outcome",
    "terminal_state_met",
    "task_kind",
    "scope_id",
    "runtime",
    "model",
    "permission_mode",
    "source",
    "skills",
    "authority",
    "action",
    "decision",
    "error_code",
    "feedback",
    "metrics",
}
LABEL_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


class EventError(ValueError):
    """Raised when an event violates the public contract."""


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def default_log_path() -> Path:
    configured = os.environ.get("HARNESS_OBSERVABILITY_LOG")
    if configured:
        return Path(configured).expanduser()
    state_home = os.environ.get("XDG_STATE_HOME")
    if state_home:
        return Path(state_home) / "harness-observe" / "events.jsonl"
    local_app_data = os.environ.get("LOCALAPPDATA")
    if os.name == "nt" and local_app_data:
        return Path(local_app_data) / "harness-observe" / "events.jsonl"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "harness-observe" / "events.jsonl"
    return Path.home() / ".local" / "state" / "harness-observe" / "events.jsonl"


def parse_bool(value: str) -> bool:
    normalized = value.lower()
    if normalized in {"true", "1", "yes"}:
        return True
    if normalized in {"false", "0", "no"}:
        return False
    raise argparse.ArgumentTypeError("expected true or false")


def require_label(value: Any, field: str) -> None:
    if not isinstance(value, str) or not LABEL_PATTERN.fullmatch(value):
        raise EventError(
            f"{field} must be an opaque 1-64 character label using letters, numbers, '.', '_' or '-'"
        )


def validate_event(event: Any) -> None:
    if not isinstance(event, dict):
        raise EventError("event must be a JSON object")
    unknown = set(event) - ALLOWED_FIELDS
    if unknown:
        raise EventError(f"unknown or content-bearing fields: {', '.join(sorted(unknown))}")

    for field in ("schema_version", "event_id", "timestamp", "run_id", "event_type", "status"):
        if field not in event:
            raise EventError(f"missing required field: {field}")
    if event["schema_version"] != SCHEMA_VERSION:
        raise EventError(f"unsupported schema_version: {event['schema_version']!r}")
    try:
        uuid.UUID(event["event_id"])
    except (ValueError, TypeError, AttributeError) as exc:
        raise EventError("event_id must be a UUID") from exc
    try:
        parsed_timestamp = dt.datetime.fromisoformat(str(event["timestamp"]).replace("Z", "+00:00"))
    except ValueError as exc:
        raise EventError("timestamp must be RFC 3339 compatible") from exc
    if parsed_timestamp.tzinfo is None:
        raise EventError("timestamp must include a timezone")

    require_label(event["run_id"], "run_id")
    for field in (
        "task_kind",
        "scope_id",
        "runtime",
        "model",
        "permission_mode",
        "source",
        "action",
        "error_code",
    ):
        if field in event:
            require_label(event[field], field)
    for field in ("skills", "authority"):
        if field in event:
            values = event[field]
            if not isinstance(values, list) or len(values) != len(set(values)):
                raise EventError(f"{field} must be an array of unique values")
    for skill in event.get("skills", []):
        require_label(skill, "skills item")
    if any(item not in AUTHORITIES for item in event.get("authority", [])):
        raise EventError("authority contains an unsupported value")

    enums = {
        "event_type": EVENT_TYPES,
        "status": STATUSES,
        "phase": PHASES,
        "outcome": OUTCOMES,
        "decision": DECISIONS,
        "feedback": FEEDBACK_VALUES,
    }
    for field, choices in enums.items():
        if field in event and event[field] not in choices:
            raise EventError(f"{field} must be one of: {', '.join(choices)}")
    if "terminal_state_met" in event and not isinstance(event["terminal_state_met"], bool):
        raise EventError("terminal_state_met must be boolean")

    metrics = event.get("metrics", {})
    if not isinstance(metrics, dict) or set(metrics) - set(METRIC_FIELDS):
        raise EventError("metrics contains unsupported fields")
    for name, value in metrics.items():
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise EventError(f"metrics.{name} must be a non-negative integer")

    event_type = event["event_type"]
    if event_type == "run_finished":
        if "outcome" not in event or "terminal_state_met" not in event:
            raise EventError("run_finished requires outcome and terminal_state_met")
        if event["outcome"] in {"failed", "blocked"} and "error_code" not in event:
            raise EventError("failed or blocked run_finished requires a normalized error_code")
    if event_type == "guard_decision" and not {"action", "decision"}.issubset(event):
        raise EventError("guard_decision requires action and decision")
    if event_type == "feedback" and "feedback" not in event:
        raise EventError("feedback event requires feedback")


def load_events(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not path.exists():
        return [], []
    events: list[dict[str, Any]] = []
    errors: list[str] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, 1):
            if not raw.strip():
                errors.append(f"line {line_number}: blank lines are not allowed")
                continue
            try:
                event = json.loads(raw)
                validate_event(event)
            except (json.JSONDecodeError, EventError) as exc:
                errors.append(f"line {line_number}: {exc}")
                continue
            events.append(event)
    return events, errors


@contextmanager
def append_lock(path: Path) -> Iterator[None]:
    lock_path = path.with_suffix(path.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as lock_handle:
        if os.name == "nt":
            import msvcrt

            lock_handle.seek(0)
            lock_handle.write(b"0")
            lock_handle.flush()
            lock_handle.seek(0)
            msvcrt.locking(lock_handle.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                lock_handle.seek(0)
                msvcrt.locking(lock_handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)


def append_event(path: Path, event: dict[str, Any]) -> None:
    validate_event(event)
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(event, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    with append_lock(path):
        with path.open("a", encoding="utf-8") as handle:
            handle.write(encoded + "\n")
            handle.flush()
            os.fsync(handle.fileno())


def append_event_once(path: Path, event: dict[str, Any]) -> bool:
    """Append an event unless its deterministic id already exists."""
    validate_event(event)
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(event, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    with append_lock(path):
        if path.exists():
            with path.open(encoding="utf-8") as existing:
                for raw in existing:
                    try:
                        if json.loads(raw).get("event_id") == event["event_id"]:
                            return False
                    except json.JSONDecodeError:
                        continue
        with path.open("a", encoding="utf-8") as handle:
            handle.write(encoded + "\n")
            handle.flush()
            os.fsync(handle.fileno())
    return True


def build_event(args: argparse.Namespace) -> dict[str, Any]:
    event: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "event_id": str(uuid.uuid4()),
        "timestamp": utc_now(),
        "run_id": args.run_id,
        "event_type": args.event_type,
        "status": args.status,
    }
    simple_fields = (
        "phase",
        "outcome",
        "terminal_state_met",
        "task_kind",
        "scope_id",
        "runtime",
        "model",
        "permission_mode",
        "source",
        "action",
        "decision",
        "error_code",
        "feedback",
    )
    for field in simple_fields:
        value = getattr(args, field, None)
        if value is not None:
            event[field] = value
    if args.skill:
        event["skills"] = sorted(set(args.skill))
    if args.authority:
        event["authority"] = sorted(set(args.authority))
    metrics = {
        field: getattr(args, field)
        for field in METRIC_FIELDS
        if getattr(args, field, None) is not None
    }
    if metrics:
        event["metrics"] = metrics
    return event


def percentile(values: list[int], fraction: float) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int((len(ordered) - 1) * fraction)))
    return ordered[index]


def build_summary(events: list[dict[str, Any]]) -> dict[str, Any]:
    run_ids = {event["run_id"] for event in events}
    finished = [event for event in events if event["event_type"] == "run_finished"]
    outcomes = collections.Counter(event["outcome"] for event in finished)
    run_skills = {
        (event["run_id"], skill)
        for event in events
        for skill in event.get("skills", [])
    }
    skills = collections.Counter(skill for _, skill in run_skills)
    errors = collections.Counter(event["error_code"] for event in events if "error_code" in event)
    denials = sum(
        event.get("decision") == "deny"
        for event in events
        if event["event_type"] == "guard_decision"
    )
    durations = [
        event["metrics"]["duration_ms"]
        for event in finished
        if "duration_ms" in event.get("metrics", {})
    ]
    turn_durations = [
        event["metrics"]["duration_ms"]
        for event in events
        if event["event_type"] == "turn_stopped"
        and "duration_ms" in event.get("metrics", {})
    ]
    terminal_met = sum(event.get("terminal_state_met") is True for event in finished)
    turns_started = sum(event["event_type"] == "turn_started" for event in events)
    turns_stopped = sum(event["event_type"] == "turn_stopped" for event in events)
    return {
        "schema_version": SCHEMA_VERSION,
        "events": len(events),
        "runs": len(run_ids),
        "finished_runs": len(finished),
        "turns_started": turns_started,
        "turns_stopped": turns_stopped,
        "turn_completion_rate": round(turns_stopped / turns_started, 4) if turns_started else None,
        "terminal_state_met": terminal_met,
        "terminal_state_rate": round(terminal_met / len(finished), 4) if finished else None,
        "outcomes": dict(sorted(outcomes.items())),
        "skills": dict(skills.most_common()),
        "error_codes": dict(errors.most_common()),
        "guard_denials": denials,
        "duration_ms": {
            "median": int(statistics.median(durations)) if durations else None,
            "p95": percentile(durations, 0.95),
        },
        "turn_duration_ms": {
            "median": int(statistics.median(turn_durations)) if turn_durations else None,
            "p95": percentile(turn_durations, 0.95),
        },
    }


def summary_markdown(summary: dict[str, Any]) -> str:
    rate = summary["terminal_state_rate"]
    rate_text = "n/a" if rate is None else f"{rate:.1%}"
    lines = [
        "# Harness observation summary",
        "",
        f"- Events: {summary['events']}",
        f"- Runs: {summary['runs']}",
        f"- Finished runs: {summary['finished_runs']}",
        f"- Turns started / stopped: {summary['turns_started']} / {summary['turns_stopped']}",
        f"- Verified terminal state: {summary['terminal_state_met']} ({rate_text})",
        f"- Guard denials: {summary['guard_denials']}",
        f"- Duration median / p95: {summary['duration_ms']['median']} / {summary['duration_ms']['p95']} ms",
        f"- Turn duration median / p95: {summary['turn_duration_ms']['median']} / {summary['turn_duration_ms']['p95']} ms",
        "",
    ]
    for title, key in (("Outcomes", "outcomes"), ("Skills", "skills"), ("Error codes", "error_codes")):
        lines.extend((f"## {title}", "", "| Value | Count |", "| --- | ---: |"))
        values = summary[key]
        if values:
            lines.extend(f"| `{name}` | {count} |" for name, count in values.items())
        else:
            lines.append("| _none_ | 0 |")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_candidates(events: list[dict[str, Any]], minimum_count: int) -> dict[str, Any]:
    grouped: dict[tuple[str, str, tuple[str, ...]], list[dict[str, Any]]] = collections.defaultdict(list)
    for event in events:
        if "error_code" not in event:
            continue
        key = (
            event["error_code"],
            event.get("task_kind", "unknown"),
            tuple(sorted(event.get("skills", []))),
        )
        grouped[key].append(event)
    candidates = []
    for (error_code, task_kind, skills), matching in grouped.items():
        latest_by_run = {event["run_id"]: event for event in matching}
        distinct_runs = sorted(latest_by_run.values(), key=lambda event: event["timestamp"])
        if len(distinct_runs) < minimum_count:
            continue
        signature = "|".join((error_code, task_kind, ",".join(skills)))
        candidates.append(
            {
                "candidate_id": hashlib.sha256(signature.encode()).hexdigest()[:12],
                "state": "proposed",
                "error_code": error_code,
                "task_kind": task_kind,
                "skills": list(skills),
                "count": len(distinct_runs),
                "last_seen": distinct_runs[-1]["timestamp"],
                "event_ids": [event["event_id"] for event in distinct_runs[-5:]],
                "next": "Confirm source sessions, then add a privacy-safe reproducible eval fixture.",
            }
        )
    candidates.sort(key=lambda item: (-item["count"], item["candidate_id"]))
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now(),
        "minimum_count": minimum_count,
        "candidates": candidates,
    }


def cross_validate(events: Iterable[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    event_ids: set[str] = set()
    finished: collections.Counter[str] = collections.Counter()
    for event in events:
        if event["event_id"] in event_ids:
            errors.append(f"duplicate event_id: {event['event_id']}")
        event_ids.add(event["event_id"])
        if event["event_type"] == "run_finished":
            finished[event["run_id"]] += 1
    for run_id, count in finished.items():
        if count > 1:
            errors.append(f"run {run_id}: expected one run_finished event, found {count}")
    return errors


def add_record_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("record", help="append one validated event")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--event-type", choices=EVENT_TYPES, required=True)
    parser.add_argument("--status", choices=STATUSES, default="ok")
    parser.add_argument("--phase", choices=PHASES)
    parser.add_argument("--outcome", choices=OUTCOMES)
    parser.add_argument("--terminal-state-met", type=parse_bool)
    parser.add_argument("--task-kind")
    parser.add_argument("--scope-id")
    parser.add_argument("--runtime")
    parser.add_argument("--model")
    parser.add_argument("--permission-mode")
    parser.add_argument("--source")
    parser.add_argument("--skill", action="append")
    parser.add_argument("--authority", action="append", choices=AUTHORITIES)
    parser.add_argument("--action")
    parser.add_argument("--decision", choices=DECISIONS)
    parser.add_argument("--error-code")
    parser.add_argument("--feedback", choices=FEEDBACK_VALUES)
    for field in METRIC_FIELDS:
        parser.add_argument(f"--{field.replace('_', '-')}", type=int)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", type=Path, default=default_log_path())
    subparsers = parser.add_subparsers(dest="command", required=True)
    add_record_parser(subparsers)

    summary = subparsers.add_parser("summary", help="derive aggregate metrics")
    summary.add_argument("--format", choices=("json", "markdown"), default="markdown")

    candidates = subparsers.add_parser("candidates", help="derive repeated failure patterns")
    candidates.add_argument("--minimum-count", type=int, default=2)

    subparsers.add_parser("validate", help="validate the entire JSONL source")
    subparsers.add_parser("doctor", help="show source health without recording content")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    path = args.log.expanduser()
    if args.command == "record":
        try:
            event = build_event(args)
            append_event(path, event)
        except EventError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(event, ensure_ascii=False, sort_keys=True))
        return 0

    events, errors = load_events(path)
    errors.extend(cross_validate(events))
    if args.command == "validate":
        if errors:
            print("\n".join(errors), file=sys.stderr)
            return 1
        print(f"valid: {len(events)} events")
        return 0
    if args.command == "doctor":
        result = {
            "log": str(path),
            "exists": path.exists(),
            "events": len(events),
            "invalid": len(errors),
            "last_timestamp": events[-1]["timestamp"] if events else None,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 1 if errors else 0
    if errors:
        print("source is invalid; run validate for details", file=sys.stderr)
        return 1
    if args.command == "summary":
        result = build_summary(events)
        if args.format == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(summary_markdown(result), end="")
        return 0
    if args.command == "candidates":
        if args.minimum_count < 1:
            print("error: --minimum-count must be positive", file=sys.stderr)
            return 2
        result = build_candidates(events, args.minimum_count)
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
