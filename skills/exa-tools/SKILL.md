---
name: exa-tools
description: "Use the bundled Exa API wrapper whenever a task needs live web research, current external sources, technical documentation lookup, code examples, API usage context, or company background research with source URLs, especially when local files are not enough and an MCP server is unnecessary."
argument-hint: "[command] [query]"
user-invocable: true
---

# Exa Tools

Use the bundled Python wrapper to call Exa directly from the local skill directory.

## Use this skill when

- The task needs live web research and the model should query Exa directly.
- The task needs technical documentation, code examples, or focused context for a library, API, framework, or error.
- The task needs a quick company background scan with source links.
- An MCP dependency would add friction and a simple local script is enough.

## Do not use this skill when

- Local repository search is enough.
- The task does not need current external information.
- Another tool already provides the required data more directly.

## Workflow

1. Confirm an Exa API key is available from `EXA_API_KEY` or `~/.config/exa/api_key`.
2. Pick the narrowest command that matches the request.
3. Run `scripts/exa_search.py` from this skill directory.
4. Summarize the result for the user with links, dates when available, and any obvious gaps or freshness limits.

## Command selection

### `web-search`

Use for live web results, news, product pages, docs pages, and general external research.

```bash
$SKILL_DIR/scripts/exa_search.py web-search --query "<query>"
```

Useful options:

- `--numResults` or `--num-results`: default `8`
- `--contextMaxCharacters` or `--context-max-characters`: default `10000`
- `--livecrawl`: `fallback`, `preferred`, `always`, `never`
- `--type`: `auto`, `fast`, `neural`, `deep`, `deep-reasoning`, `instant`
- `--json`: emit structured JSON instead of plain text

### `code-context`

Use for technical lookups when the user needs code snippets, API docs, or implementation context.

```bash
$SKILL_DIR/scripts/exa_search.py code-context --query "<query>"
```

Useful options:

- `--tokens`, `--tokens-num`, or `--tokensNum`: default `5000`
- `--livecrawl`: `fallback`, `preferred`, `always`, `never`
- `--json`: emit structured JSON instead of plain text

Note: this command falls back to Exa search if the context endpoint returns no content.

### `company-research`

Use for company overview, positioning, and background gathering.

```bash
$SKILL_DIR/scripts/exa_search.py company-research --companyName "<company>"
```

Useful options:

- `--numResults` or `--num-results`: default `3`
- `--json`: emit structured JSON instead of plain text

## Output expectations

- Prefer concise synthesis over dumping raw output.
- Include source URLs in the final answer.
- Mention publication dates when the result includes them.
- If the results are sparse, say so instead of overstating confidence.
- Use `--json` when the downstream task benefits from structured parsing or saving output.

## Examples

```bash
$SKILL_DIR/scripts/exa_search.py web-search \
  --query "OpenAI Responses API background mode" \
  --numResults 5 \
  --contextMaxCharacters 4000
```

```bash
$SKILL_DIR/scripts/exa_search.py code-context \
  --query "FastAPI streaming response example" \
  --tokensNum 4000
```

```bash
$SKILL_DIR/scripts/exa_search.py company-research \
  --companyName "Exa AI" \
  --numResults 6 \
  --json
```

## Files

- `scripts/exa_search.py`: direct Exa API wrapper used by this skill
