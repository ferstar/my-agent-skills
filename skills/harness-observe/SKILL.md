---
name: harness-observe
description: Autonomously audit native local Codex session JSONL for workflow quality, latency, cost shape, tool use, recurring failures, and eval candidates. Use when the user wants scheduled harness observability or evidence-driven harness improvement; do not use for ordinary task execution, application telemetry, or full transcript export.
argument-hint: "[audit window, default: 7 days]"
---

# Harness Observe

Treat native `$CODEX_HOME/sessions/**/*.jsonl` as the sole source of truth.
Derived metrics, audit reports, and eval candidates are disposable views. Do not
create a second authoritative event store and do not require the user to poll
files or run report commands manually.

## Deterministic scan

Run the bundled scanner first:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/scan_codex_sessions.py --days 7
```

The scanner reads structured records such as `task_started`, `task_complete`,
`token_count`, `turn_context`, and tool calls. It outputs only content-free
metrics:

- turn completion rate;
- duration and time-to-first-token median/P95;
- input/output token median/P95;
- tool calls per turn and tool distribution;
- model, approval-policy, and sandbox-policy distribution;
- opaque session/turn references for incomplete work;
- malformed JSONL count.

Do not infer semantic success from these metrics alone.

## AI audit

1. Check source health and establish the requested time window.
2. Compare completion, latency, token, and tool-use shape with a prior audit when
   comparable evidence is available.
3. Ignore isolated noise. Escalate corrupted input, persistent incomplete turns,
   repeated workflow failures, or meaningful latency/cost regression.
4. For a high-signal anomaly, locate the referenced native session and inspect
   only the minimum evidence needed to confirm cause, actual skills used,
   authority handling, outcome, and terminal-state verification.
5. Recommend exactly one disposition: `observe`, `promote-to-eval`,
   `change-skill`, `change-deterministic-tooling`, or `fix-instrumentation`.
6. If no actionable signal exists, report a short health result and stop.

Never copy prompts, responses, reasoning, commands, paths, URLs, tool arguments,
tool results, secrets, or customer data into reports or public fixtures. Session
and turn IDs are provenance pointers, not report content unless needed to make a
finding actionable.

## Scheduled operation

Prefer a scheduled Codex task over per-turn hooks. The task should run the scan,
perform the AI audit, and send a concise inbox report. Keep it read-only by
default; raw observations never grant edit, commit, push, merge, deploy,
publishing, or cleanup authority.

## Eval promotion

Promote a finding only after source-session evidence confirms a repeated cause
and the case can be reproduced without private content. Keep capability evals
separate from regression evals. Measure the proposed harness change against a
baseline using repeated trials and deterministic graders where possible.

## Report format

```text
Status: healthy | attention | invalid-source
Evidence: <3-5 comparable metrics>
Finding: <one confirmed pattern or "no actionable signal">
Disposition: <one allowed disposition>
Next: <one action, or none>
```
