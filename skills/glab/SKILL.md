---
name: glab
description: GitLab CLI workflows with `glab` for issues, merge requests, CI/CD, and API automation. Use when the user needs GitLab command-line operations, GitLab API calls, issue or MR updates, pipeline checks, threaded discussion replies, or self-hosted GitLab workflows.
---

# glab

Use `glab` for GitLab operations from the terminal.

## Routing

- Load `references/cli_quick_reference.md` for common commands and flags.
- Load `references/workflows.md` for end-to-end issue, MR, and CI workflows.
- Load `references/rest_api_commands.md` for API-heavy tasks and request patterns.
- Load `references/troubleshooting.md` when auth, flags, API behavior, or instance config goes wrong.

## Core rules

- Prefer `glab api` over interactive flows for automation.
- Use `-R owner/repo` or encoded project paths when outside a Git repository.
- URL-encode `<namespace>/<project>` as `<namespace>%2F<project>` in API paths.
- For long multiline Markdown bodies, prefer `--raw-field description="$(cat file)"` over fragile inline escaping.
- Validate issue or MR text after updates by reading the API response.
- Check command-specific flags with `glab <command> --help` before scripting uncommon operations.
- For self-hosted GitLab, set `GITLAB_HOST` when needed.

## Common command patterns

```bash
# Auth
glab auth status

# Issues
glab issue list -R owner/repo --assignee=@me
glab issue view 123 -R owner/repo

# Merge requests
glab mr list -R owner/repo
glab mr create --title "Title" --description "Closes #123"

# CI/CD
glab ci status
glab ci lint
```

## API preference

```bash
# GET
glab api projects/<namespace>%2F<project>/issues/123

# POST
glab api --method POST projects/<namespace>%2F<project>/issues \
  --field title="Bug" \
  --field description="Details"

# PUT with multiline body
DESC_FILE=/tmp/issue-description.md
glab api --method PUT projects/<namespace>%2F<project>/issues/123 \
  --raw-field description="$(cat "$DESC_FILE")"
```

## GraphQL note

When REST cannot change a work item type, use GraphQL mutations such as `workItemConvert` or `workItemUpdate`. See `references/rest_api_commands.md` and `references/workflows.md` for exact patterns.

## Discussion replies

Reply to issue or MR discussions through the discussions API instead of plain issue notes when the user wants a threaded reply. See `references/workflows.md` for the exact sequence.
