# Harness event schema

The JSONL file is append-only. Each line is one independently valid event. The
schema is deliberately small so it can survive changes in model, agent runtime,
and observability backend.

## Required fields

| Field | Meaning |
| --- | --- |
| `schema_version` | Event contract version, currently `1` |
| `event_id` | Globally unique event identifier |
| `timestamp` | UTC RFC 3339 timestamp |
| `run_id` | Opaque identifier shared by one task run |
| `event_type` | Harness lifecycle event |
| `status` | Status of this event, not an inferred run outcome |

## Optional fields

| Field | Meaning |
| --- | --- |
| `phase` | `DISCOVER`, `DECIDE`, `IMPLEMENT`, `VERIFY`, `SHIP`, or `DONE` |
| `outcome` | Final or intermediate outcome |
| `terminal_state_met` | Whether observable completion conditions were verified |
| `task_kind` | Low-cardinality task class such as `repo-change` |
| `scope_id` | Opaque, non-sensitive grouping label; never a repo path or URL |
| `runtime` | Low-cardinality agent runtime such as `codex` |
| `model` | Model slug when the runtime supplies one |
| `permission_mode` | Runtime permission-mode label |
| `source` | Producer class such as `codex-hook` |
| `skills` | Skills actually used in the run |
| `authority` | Independently granted authorities |
| `action` | Low-cardinality action class such as `merge` or `deploy` |
| `decision` | `allow`, `deny`, or `not-required` for guard events |
| `error_code` | Normalized failure class, never a raw error message |
| `feedback` | `accepted`, `reworked`, or `rejected` |
| `metrics` | Non-negative counts and duration only |

Allowed metric keys are `duration_ms`, `input_tokens`, `output_tokens`,
`tool_calls`, `retries`, `evidence_count`, and `changed_files_count`.

## Privacy rules

The event stream is metadata-only by default. Producers must not add arbitrary
objects or free text. In particular, never store these fields or their content:

- prompt, response, reasoning, or transcript;
- command, path, URL, host name, or branch name;
- tool arguments or tool results;
- secrets, access tokens, customer identifiers, or source content.

Use a stable `error_code` such as `ci-first-failure-not-isolated`, not the raw
error line. Use `scope_id` such as `public-repo`, not a local directory.

## Source-of-truth rule

Summaries, dashboards, caches, candidate lists, and exported OpenTelemetry data
are derived views. They may be deleted and regenerated. Never write a derived
classification back over historical JSONL events; append a correction or
feedback event instead.

An adapter may map these records to OpenTelemetry spans or logs, but it must
preserve `run_id`, `event_id`, lifecycle semantics, and content-free defaults.

Codex lifecycle hooks use `turn_started` and `turn_stopped`. These events prove
that a turn ran and how long it took; they do not claim that the task succeeded.
Only an outcome-aware producer may append `run_finished`.
