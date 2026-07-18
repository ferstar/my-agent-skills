# Local harness observability and improvement loop

[简体中文](harness-observability-loop.zh-CN.md)

## Architecture

```text
native Codex session JSONL (sole source of truth)
                     |
                     v
       deterministic content-free scanner
                     |
                     v
       scheduled AI high-signal review
                     |
            +--------+--------+
            |                 |
            v                 v
      concise inbox      sanitized eval
          report           candidate
                              |
                              v
                 baseline -> change -> regression
```

Codex already records structured task lifecycle, duration, TTFT, token usage,
tool calls, model, approval policy, and sandbox policy in local session JSONL.
Using it directly avoids a lower-fidelity duplicate event stream and removes
per-turn hook latency and recursion risk.

## Deterministic metrics

```bash
PYTHONDONTWRITEBYTECODE=1 \
  python3 <skill-dir>/scripts/scan_codex_sessions.py --days 7
```

The scanner emits only aggregate metrics and opaque incomplete-turn references.
It never exports prompt, response, reasoning, command, path, URL, tool argument,
or tool result content.

Metrics alone cannot prove success, actual skill use, or verified terminal
state. The scheduled AI reviews source sessions only for repeated or otherwise
high-signal anomalies, then reports a confirmed finding or a short healthy
status.

## Autonomous review

A scheduled Codex task should:

1. scan a stable recent window;
2. report malformed source data immediately;
3. compare completion, P50/P95 latency, TTFT, token shape, and tool-use shape;
4. minimally inspect source sessions only for actionable anomalies;
5. propose one disposition: observe, promote to eval, change a skill, change
   deterministic tooling, or fix instrumentation;
6. avoid edits and delivery actions unless separately authorized.

This is controlled evolution. The audit can propose a sanitized eval but cannot
authorize self-modification, commit, push, merge, deploy, publishing, or cleanup.

## Review cadence

- Weekly: scan recent sessions and send one low-noise inbox report.
- After a repeated correction: confirm the source pattern and consider an eval.
- Before a harness change: capture a comparable baseline.
- After a harness change: rerun capability and regression trials.

## Industry basis

- [OpenAI integrations and observability](https://developers.openai.com/api/docs/guides/agents/integrations-observability)
- [OpenAI agent improvement loop](https://developers.openai.com/cookbook/examples/agents_sdk/agent_improvement_loop)
- [Anthropic: Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
- [OpenTelemetry GenAI observability](https://opentelemetry.io/blog/2026/genai-observability/)
