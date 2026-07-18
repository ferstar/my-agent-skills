---
name: harness-observe
description: Record and analyze privacy-safe local JSONL events for a personal agent harness. Use when the user wants harness observability, workflow metrics, recurring-failure analysis, eval candidates, or an evidence-driven improvement loop; do not use for ordinary task execution or full transcript capture.
argument-hint: "record | summary | candidates | validate | doctor"
---

# Harness Observe

Use a local append-only JSONL event stream as the sole source of truth for
harness observability. Derived reports and eval candidates are disposable and
must be reproducible from that stream.

## Boundary

This skill observes workflow behavior; it does not execute, approve, merge,
deploy, or publish the work being observed. It also does not replace
application telemetry or preserve full transcripts.

Default collection is content-free. Never record prompts, responses, reasoning,
commands, file paths, URLs, host names, tool arguments, tool results, access
tokens, credentials, customer data, or arbitrary free text. Token *counts* are
allowed.

## Event lifecycle

Prefer deterministic runtime hooks for lifecycle coverage:

1. A Codex `UserPromptSubmit` hook appends `turn_started` without reading or
   retaining the supplied prompt.
2. A Codex `Stop` hook appends `turn_stopped` and derived duration without
   reading or retaining the assistant message.
3. An outcome-aware producer may append `run_started`, `phase_changed`,
   `guard_decision`, `verification`, exactly one `run_finished`, and `feedback`.

Do not emit events for routine reads or every tool call. Native runtime tracing
may capture those details separately; this event stream records the harness
semantics needed for improvement.

Lifecycle hooks cannot prove success, skill use, or terminal-state completion.
Do not parse final assistant prose to guess those facts. Keep lifecycle coverage
and semantic outcome evaluation separate.

## Commands

The standard-library CLI resolves its default log from
`HARNESS_OBSERVABILITY_LOG`, then the platform state directory.

```bash
python3 scripts/harness_observe.py doctor

python3 scripts/install_codex_hooks.py install
python3 scripts/install_codex_hooks.py check

python3 scripts/harness_observe.py record \
  --run-id task-20260718-01 \
  --event-type run_finished \
  --phase DONE \
  --status ok \
  --outcome success \
  --terminal-state-met true \
  --task-kind repo-change \
  --skill agent-preflight \
  --skill codex-ship-loop \
  --duration-ms 42000

python3 scripts/harness_observe.py summary --format markdown
python3 scripts/harness_observe.py candidates --minimum-count 2
python3 scripts/harness_observe.py validate
```

Pass `--log <path>` before the subcommand to use a different source file.
After installing or changing Codex hooks, review and trust their exact definition
through Codex's `/hooks` UI. Observation is fail-open and must never block work.

## Improvement loop

```text
JSONL events
  -> deterministic summary
  -> repeated failure/blocked pattern
  -> proposed eval candidate
  -> human review and reproducible fixture
  -> measured harness change
  -> regression gate
```

`candidates` proposes patterns; it never edits skills or evals. Promote a
candidate only when the underlying session evidence confirms the diagnosis and
the case can be reproduced without private data. Keep capability evals separate
from near-100%-pass regression evals.

Prefer code-based outcome graders. Use model graders only for behavior that
cannot be checked deterministically, and calibrate them with periodic human
review. Compare repeated trials rather than treating one model run as proof.

## Review cadence

- After a failed or blocked run: validate the event and normalize `error_code`.
- Weekly: inspect summary deltas and repeated candidates.
- Before changing a skill: establish a baseline from the relevant eval cases.
- After changing a skill: rerun capability and regression cases; retain the
  change only when outcome quality improves without unacceptable safety, time,
  or token-count regression.

Read [`references/event-schema.md`](references/event-schema.md) when adding a
producer or adapter. The machine-readable schema is
[`references/event.schema.json`](references/event.schema.json).
