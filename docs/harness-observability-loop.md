# Local harness observability and improvement loop

[简体中文](harness-observability-loop.zh-CN.md)

## Purpose

A personal harness needs enough evidence to answer four questions:

1. Did the run reach its observable terminal state?
2. Which workflow or authority boundary helped or failed?
3. Which failures repeat often enough to deserve an eval?
4. Did a harness change improve outcomes without unacceptable safety, latency,
   or token-count regression?

This repository uses a local append-only JSONL stream as the only authoritative
observability state. Reports, dashboards, and eval candidates are derived views.

## Architecture

```text
agent runtime / workflow checkpoint
                |
                v
    deterministic lifecycle hooks
                |
                v
     content-free JSONL events
          (source of truth)
                |
        +-------+--------+
        |                |
        v                v
 deterministic       recurring failure
   summaries            candidates
        |                |
        +-------+--------+
                v
       reviewed eval fixture
                |
                v
      baseline -> change -> regression gate
```

The JSONL layer records lifecycle facts and harness semantics such as phase, authority, skill use,
verified outcome, normalized failure class, latency, and token counts. It does
not duplicate full runtime traces.

## Why JSONL first

- Append-only records preserve history and make correction explicit.
- One event per line is easy to inspect, stream, validate, back up, and process.
- The format has no service dependency and works offline.
- A future OpenTelemetry or hosted-observability adapter can be rebuilt from the
  source events without changing their meaning.
- Keeping one source of truth avoids disagreement between a local database,
  dashboard state, and eval backlog.

OpenTelemetry's GenAI conventions are useful as an interchange target, but they
remain under active development. They also treat prompt and response content as
explicit opt-in data because it may be sensitive. The local contract therefore
starts with stable, content-free workflow outcomes rather than mirroring every
vendor field.

## What to observe

Observe decisions and outcomes, not every action.

| Signal | Examples | Improvement question |
| --- | --- | --- |
| Outcome | success, partial, failed, blocked | Is the harness reliably useful? |
| Terminal state | verified or not verified | Is it declaring completion too early? |
| Phase | DISCOVER through DONE | Where does work stall? |
| Skill use | low-cardinality skill names | Which routes help or overlap? |
| Authority | independent granted actions | Are unsafe actions being prevented? |
| Guard decision | allow or deny | Where is permission friction or protection? |
| Failure class | normalized `error_code` | Which failure deserves the next eval? |
| Cost shape | duration, token counts, retries | Did quality gains become too expensive? |
| Feedback | accepted, reworked, rejected | Did the outcome satisfy the user? |

Do not record prompt text, model output, reasoning, commands, paths, URLs, host
names, branch names, tool arguments, tool results, secrets, or customer data.
Keep an `event_id` so a human can return to the original session when detailed
diagnosis is necessary.

## Minimal operating loop

### 1. Install deterministic lifecycle hooks

For Codex, install `UserPromptSubmit` and `Stop` hooks:

```bash
python3 <skill-dir>/scripts/install_codex_hooks.py install
python3 <skill-dir>/scripts/install_codex_hooks.py check
```

Review and trust the exact hook definitions once through Codex's `/hooks` UI.
Codex passes the prompt and latest assistant message to these lifecycle events,
but the adapter deliberately ignores both. It hashes session and turn IDs into
an opaque run ID and appends only `turn_started`, `turn_stopped`, runtime labels,
and derived duration.

Hooks are more reliable than asking the model to remember a default logging
instruction. They still cannot determine whether the task succeeded, which
skills were semantically active, or whether the real terminal state was
verified. The adapter never infers those facts from final prose.

### 2. Record semantic outcomes

An outcome-aware eval runner, workflow, or explicit review may record
`run_started` and exactly one `run_finished` event for non-trivial work.
Add `phase_changed`, `guard_decision`, or `verification` only when the event is
meaningful to a future decision.

```bash
python3 <skill-dir>/scripts/harness_observe.py record \
  --run-id task-20260718-01 \
  --event-type run_finished \
  --phase DONE \
  --status ok \
  --outcome success \
  --terminal-state-met true \
  --task-kind repo-change \
  --skill agent-preflight \
  --duration-ms 42000
```

The default source path is resolved from `HARNESS_OBSERVABILITY_LOG`, then
`$CODEX_HOME/harness-observe/events.jsonl`, and finally
`~/.codex/harness-observe/events.jsonl`. This keeps hook configuration and
observation state in one Codex control-plane directory. Use `--log` before the
subcommand to override it.

### 3. Validate and summarize

```bash
python3 <skill-dir>/scripts/harness_observe.py validate
python3 <skill-dir>/scripts/harness_observe.py summary --format markdown
```

Run validation before trusting a report. Summary output is deliberately
reproducible and disposable.

### 4. Propose candidates

```bash
python3 <skill-dir>/scripts/harness_observe.py candidates --minimum-count 2
```

Candidates group repeated normalized failure patterns. They contain event IDs,
not reconstructed prompts. A candidate is not automatically an eval: inspect
the source sessions, confirm the diagnosis, sanitize the case, and define an
observable expected outcome.

### 5. Promote and compare

Maintain two suites:

- capability evals measure current headroom and may initially have a low pass
  rate;
- regression evals protect behaviors that should remain nearly always correct.

For each proposed harness change:

1. capture a baseline using multiple trials;
2. prefer deterministic outcome and tool-use graders;
3. use a separately calibrated model grader only for subjective behavior;
4. compare success, safety, duration, retries, and token counts;
5. retain the change only when the evidence justifies it;
6. promote the confirmed case to the regression suite.

This is controlled evolution, not uncontrolled self-modification. Raw traces do
not authorize skill edits, commits, pushes, or deployment.

## Review cadence

- Per failed run: normalize one useful error code.
- Weekly: review outcome rate, unverified terminal states, guard denials, and
  repeated candidates.
- Monthly or before model migration: rerun the stable regression suite and a
  sample of capability cases.
- After a repeated user correction: add feedback, reproduce the case, and
  decide whether it belongs in a skill, `AGENTS.md`, a deterministic script, or
  nowhere.

## Industry basis

- OpenAI recommends using runtime traces first for debugging and then feeding
  higher-signal examples into systematic agent evaluation:
  [Integrations and observability](https://developers.openai.com/api/docs/guides/agents/integrations-observability).
- OpenAI's improvement-loop example connects traces, human and model feedback,
  reusable evals, ranked harness changes, and an implementation handoff:
  [Build an Agent Improvement Loop](https://developers.openai.com/cookbook/examples/agents_sdk/agent_improvement_loop).
- Anthropic separates tasks, repeated trials, graders, traces, and environment
  outcomes, and distinguishes capability suites from regression suites:
  [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents).
- OpenTelemetry provides vendor-neutral GenAI traces and metrics while keeping
  prompt/content capture opt-in:
  [Inside the LLM Call](https://opentelemetry.io/blog/2026/genai-observability/).
- Codex lifecycle hooks provide deterministic turn-scoped `UserPromptSubmit`
  and `Stop` events with stable session and turn identifiers:
  [Codex Hooks](https://developers.openai.com/codex/hooks).
