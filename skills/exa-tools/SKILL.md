---
name: exa-tools
description: "Use the bundled Exa API wrapper whenever a task needs live web research, current external sources, technical documentation lookup, code examples, API usage context, or company background research with source URLs, especially when local files are not enough and an MCP server is unnecessary."
argument-hint: "[command] [query]"
user-invocable: true
---

# Exa Tools

Use the bundled Python wrapper to call Exa directly from the local skill directory.

## Runtime

- Always invoke the script with `uv run`.
- Do not call `python` directly and do not rely on the shebang entrypoint.
- `uv` keeps invocation consistent while still allowing the environment to provide the interpreter.

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
2. Confirm `uv` is available in the current shell.
3. Pick the narrowest command that matches the request.
4. Run `uv run "$SKILL_DIR/scripts/exa_search.py" ...` from this skill directory.
5. Summarize the result for the user with links, dates when available, and any obvious gaps or freshness limits.

## Command selection

### Priority for code development

For coding tasks, prefer commands in this order:

1. `code-context`: default for API docs, code examples, library usage, migration notes, and implementation context.
2. `web-search`: use when you need broader source coverage, freshness controls, domain filters, or product/news pages.
3. `answer`: use only when the user explicitly wants a synthesized answer, comparison, or concise summary with citations after source grounding.

Do not default to `answer` for code development when the user likely needs raw docs, exact parameters, or copyable examples.

### `web-search`

Use for live web results, news, product pages, docs pages, and general external research.

```bash
uv run "$SKILL_DIR/scripts/exa_search.py" \
  web-search --query "<query>"
```

Useful options:

- `--numResults` or `--num-results`: default `8`
- `--contextMaxCharacters` or `--context-max-characters`: default `10000`
- `--include-domain`: repeatable domain allowlist for source quality control
- `--exclude-domain`: repeatable domain denylist
- `--maxAgeHours` or `--max-age-hours`: content freshness target in hours
- `--livecrawl`: compatibility option for deprecated Exa livecrawl modes
- `--livecrawlTimeout` or `--livecrawl-timeout`: crawl timeout in milliseconds
- `--start-published-date` / `--end-published-date`: limit results by publication date
- `--type`: `auto`, `fast`, `neural`, `deep`, `deep-reasoning`, `instant`
- `--json`: emit structured JSON instead of plain text

Prefer `--maxAgeHours` for freshness control. Do not combine it with `--livecrawl`.

### `code-context`

Use for technical lookups when the user needs code snippets, API docs, or implementation context.

```bash
uv run "$SKILL_DIR/scripts/exa_search.py" \
  code-context --query "<query>"
```

Useful options:

- `--tokens`, `--tokens-num`, or `--tokensNum`: default `5000`
- `--include-domain`: repeatable domain allowlist for focused technical sources
- `--exclude-domain`: repeatable domain denylist
- `--livecrawl`: `fallback`, `preferred`, `always`, `never`
- `--json`: emit structured JSON instead of plain text

Note: this command falls back to Exa search if the context endpoint returns no content.

### `answer`

Use for direct answers or concise summaries when the user wants Exa to return a synthesized answer with citations.

For code development, treat this as a secondary command. Prefer `code-context` or `web-search` first unless the user is clearly asking for synthesis, comparison, or a short cited summary.

```bash
uv run "$SKILL_DIR/scripts/exa_search.py" \
  answer --query "<query>"
```

Useful options:

- `--include-domain`: repeatable domain allowlist for answer grounding
- `--exclude-domain`: repeatable domain denylist
- `--text`: include full text in returned citations
- `--json`: emit structured JSON instead of plain text

`--include-domain` / `--exclude-domain` accept domain filters, path-specific filters such as `docs.exa.ai/reference`, and subdomain wildcards such as `*.github.com`.

### `company-research`

Use for company overview, positioning, and background gathering.

```bash
uv run "$SKILL_DIR/scripts/exa_search.py" \
  company-research --companyName "<company>"
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
uv run "$SKILL_DIR/scripts/exa_search.py" \
  web-search \
  --query "OpenAI Responses API background mode" \
  --numResults 5 \
  --contextMaxCharacters 4000
```

```bash
uv run "$SKILL_DIR/scripts/exa_search.py" \
  code-context \
  --query "FastAPI streaming response example" \
  --tokensNum 4000
```

```bash
uv run "$SKILL_DIR/scripts/exa_search.py" \
  answer \
  --query "What changed in the latest Exa Python SDK release?" \
  --include-domain docs.exa.ai \
  --text
```

```bash
uv run "$SKILL_DIR/scripts/exa_search.py" \
  company-research \
  --companyName "Exa AI" \
  --numResults 6 \
  --json
```

## Files

- `scripts/exa_search.py`: direct Exa API wrapper used by this skill
