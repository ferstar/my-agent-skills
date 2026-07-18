# Agent Boundary Hardening Patterns

## Common failure modes

### 1. Positive-only prompting
The prompt explains the intended business task, but never states what must be refused.

### 2. Over-broad shell permission
Examples:
- `Bash(*)`
- `Write(*)`
- `Edit(*)`

### 3. Contradictory whitelist and deny
Example pattern:
- allow: `Bash(repo-script *)`
- deny: `Bash(*)`

This can make the whitelist ineffective depending on rule evaluation.

### 4. Missing mixed-request rule
The prompt never says what to do when the user asks for both an in-scope task and an out-of-scope command.

## Safe repair patterns

### No-shell agent
- Prompt: explicitly refuse system commands and tool-boundary tests
- Settings: deny or omit Bash, add `defaultMode: "dontAsk"`

### Script-whitelist agent
- Prompt: name the only approved scripts
- Settings: allow only those exact `Bash(...)` patterns
- Settings: keep sensitive-file denies and narrow write paths

### Single-endpoint retrieval agent
- Prompt: name the only approved endpoint or access path
- Settings: whitelist only the exact curl or wrapper-script shape
- Prompt: refuse any other URL, host, or network request

## Minimal fix checklist

1. State the agent's exact scope in one sentence.
2. Add one explicit boundary section.
3. Add at least one refusal sentence for shell-boundary testing.
4. Remove `Bash(*)` if not strictly necessary.
5. Add `defaultMode: "dontAsk"` if missing.
6. Validate JSON after editing.
