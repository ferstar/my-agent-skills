---
name: glab
description: GitLab CLI (glab) operations - issues, MRs, CI/CD, API. Use when user needs GitLab command-line workflows.
allowed-tools: Bash, Read, Grep, Glob
---

# GitLab CLI (glab)

Perform GitLab operations from terminal: issues, merge requests, CI/CD, repositories, and API.

## Quick Routing

| Task | Action |
|------|--------|
| Quick lookup | Load `references/cli_quick_reference.md` |
| Issue/MR workflow examples | Load `references/workflows.md` |
| Complete API reference | Load `references/rest_api_commands.md` |
| Error resolution | Load `references/troubleshooting.md` |

## Search Patterns

When Claude needs specific information, use these grep patterns to load the right reference:

| Information Needed | Search Pattern |
|-------------------|----------------|
| MR create/update | `grep -r "mr create\|mr update" references/` |
| Issue comment/reply | `grep -r "discussion\|note" references/` |
| CI/CD pipeline | `grep -r "pipeline\|ci" references/` |
| Time tracking | `grep -r "estimate\|spend\|time" references/` |
| Milestone management | `grep -r "milestone" references/` |
| Sub-task/Task | `grep -r "workItem\|Task\|sub-task" references/` |

## Essential: API Command

Prefer `glab api` over interactive commands for automation:

```bash
# GET
glab api projects/<namespace>%2F<project>/issues/123

# POST (create)
glab api --method POST projects/<namespace>%2F<project>/issues \
  --field title="Bug" \
  --field description="Details"

# PUT (update, short text)
glab api --method PUT projects/<namespace>%2F<project>/issues/123 \
  --field description="New content"

# PUT (update, long multiline Markdown — preferred)
DESC_FILE=/tmp/issue-description.md
glab api projects/<namespace>%2F<project>/issues/123 | jq -r '.description' > "$DESC_FILE"
cat >> "$DESC_FILE" <<'EOF'

## Extra Notes
Your multiline markdown here.
EOF

glab api --method PUT projects/<namespace>%2F<project>/issues/123 \
  --raw-field description="$(cat "$DESC_FILE")"

# Validate after update
glab api projects/<namespace>%2F<project>/issues/123 | jq -r '.description'

# Pagination: use URL params in URL, NOT flags
glab api "projects/<id>/jobs?per_page=100"
glab api --paginate "projects/<id>/pipelines?per_page=100"
```

### Long body quick rules

- Short text → `--field`
- Long multiline Markdown → `--raw-field description="$(cat file)"`
- `description@file` / `body@file` may be unreliable in some `glab api` contexts
- Always quote command substitution exactly
- Always validate rendered text after update

## Work Item Type Conversion (GraphQL)

When REST `PUT /issues/:iid` cannot change `issue_type` (for example `can not be changed to Task`), use GraphQL mutation `workItemConvert`.
This conversion is bidirectional: `issue -> task` and `task -> issue`.

```bash
# Convert Issue -> Task
# Example:
#   Work Item ID: 345  (gid://gitlab/WorkItem/345)
#   Task Type ID: 5    (gid://gitlab/WorkItems::Type/5)
glab api graphql -f query='
mutation {
  workItemConvert(input:{
    id:"gid://gitlab/WorkItem/345",
    workItemTypeId:"gid://gitlab/WorkItems::Type/5"
  }) {
    workItem { id iid webUrl workItemType { id name } }
    errors
  }
}'
```

```bash
# Convert Task -> Issue
# Example:
#   Work Item ID: 345
#   Issue Type ID: <query from project workItemTypes, do not hardcode>
glab api graphql -f query='
mutation {
  workItemConvert(input:{
    id:"gid://gitlab/WorkItem/345",
    workItemTypeId:"gid://gitlab/WorkItems::Type/<ISSUE_TYPE_ID>"
  }) {
    workItem { id iid webUrl workItemType { id name } }
    errors
  }
}'
```

Set parent-child hierarchy (for example make `#1-#5` children of `#6`) with `workItemUpdate`:

```bash
glab api graphql -f query='
mutation {
  workItemUpdate(input:{
    id:"gid://gitlab/WorkItem/345",
    hierarchyWidget:{ parentId:"gid://gitlab/WorkItem/350" }
  }) {
    workItem {
      id
      iid
      widgets {
        type
        ... on WorkItemWidgetHierarchy { hasParent parent { id iid webUrl } }
      }
    }
    errors
  }
}'
```

Tips:
- Keep the same Work Item ID (`gid://gitlab/WorkItem/<id>`); conversion changes type, not ID.
- Query/verify IDs first from REST issue API (`projects/<id>/issues/<iid>` -> `id`) or GraphQL.
- Check `.data.<mutation>.errors` is empty before continuing.

## Quick Commands

```bash
# Auth
glab auth status

# Issues
glab issue list -R owner/repo --assignee=@me
glab issue view 123 -R owner/repo

# MRs
glab mr list -R owner/repo
glab mr create --title "Title" --description "Closes #123"

# CI/CD
glab ci status
glab ci lint
```

## Common Errors

| Error | Solution |
|-------|----------|
| `401 Unauthorized` | Run `glab auth login` |
| `404 Not Found` | Check path, use URL-encoded `%2F` for `/` |
| `not a git repository` | Add `-R owner/repo` flag |
| `Unknown flag: --state` (issue list) | Use `--opened` / `--closed` / `--all` and confirm with `glab issue list --help` |
| `HTTP 415` from `glab api --input` | Switch to form fields, e.g. `--field description=...` |
| `source branch already has MR` | Find with `glab mr list --source-branch=<branch>` |

## Notes

- Use `-R owner/repo` when outside git repository
- Use `--output=json` for scripting
- Check per-command flags with `glab <command> --help` before automation
- Never send literal `\n` in issue/MR `title`/`description`/`body`; use real newlines (multiline args, here-doc, or `$'...\n...'`).
- After issue/MR text updates, validate rendered text via API output (e.g. `jq -r '.description'`) and ensure no escaped `\\n` remains.
- For self-hosted GitLab: `export GITLAB_HOST=gitlab.example.org`
- All `<namespace>/<project>` placeholders must be URL-encoded as `<namespace>%2F<project>`

## Comment/Reply to Discussion

To reply to a specific comment (threaded discussion) in issues or MRs:

```bash
# 1. Get discussion ID for issue
DISC_ID=$(glab api "projects/namespace%2Fproject/issues/123/discussions" | jq -r '.[0].id')

# 2. Reply to discussion
glab api --method POST "projects/namespace%2Fproject/issues/123/discussions/$DISC_ID/notes" \
  --field body="Reply text"

# For MR, replace path: merge_requests/456 instead of issues/123
```
