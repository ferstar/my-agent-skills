# glab Detailed Workflows

## Authentication

```bash
# Interactive login
glab auth login

# Self-hosted GitLab
glab auth login --hostname gitlab.example.org

# Environment variables
export GITLAB_TOKEN=your-token
export GITLAB_HOST=gitlab.example.org
```

## Merge Request Workflow

### Context and merge-readiness snapshot

Resolve the active GitLab host from arguments, repository remotes, or authenticated configuration; never hardcode a private instance. URL-encode `<namespace>/<project>` in API paths.

```bash
project='<namespace>%2F<project>'
iid='<iid>'
glab api "projects/$project/merge_requests/$iid" | jq '{iid,title,state,source_branch,target_branch,merge_status,detailed_merge_status,sha,web_url}'
glab api "projects/$project/merge_requests/$iid/changes" | jq -r '.changes[].new_path'
glab api "projects/$project/merge_requests/$iid/pipelines" | jq '.[0] | {id,status,sha,web_url}'
glab api "projects/$project/merge_requests/$iid/discussions?per_page=100" | jq 'map({id,resolved: ([.notes[].resolved] | all),notes: [.notes[] | {id,author:.author.username,body}]})'
```

Before making a review or merge decision, report the MR state and exact head SHA, pipeline status, unresolved discussions, changed files, linked issue state and labels, and validation evidence. Review-only requests stop after reporting; they do not authorize edits, comments, labels, merge, or cleanup.

Prefer newer live discussions over stale issue or MR body text. Immediately before an authorized merge, refresh the head SHA, pipeline, discussions, and mergeability rather than replaying all stable context.

### Creating MR

```bash
# Push branch first
git push -u origin feature-branch

# Create MR
glab mr create --title "Add feature" --description "Implements X"

# Create MR and auto-close an issue on merge
glab mr create --title "Fix bug" --description "Closes #123"

# With reviewers and labels
glab mr create --title "Fix bug" --reviewer=alice,bob --label="bug,urgent"
```

Notes:

- If your MR description already contains `Closes #<iid>`, prefer plain `glab mr create` over `glab mr create --related-issue`. In the current CLI/server combination, `--related-issue` can still mutate the result, including duplicating `Closes #<iid>` and unexpectedly creating a Draft MR.
- After creation, always run `glab mr view <iid>` and verify title, draft state, labels, and the rendered body. If `glab mr create` added or changed more than intended, patch it immediately with `glab mr update` or `glab api --method PUT`.

### Reviewing MR

```bash
# List MRs for review
glab mr list --reviewer=@me

# Checkout locally
glab mr checkout <mr-number>

# Approve
glab mr approve <mr-number>

# Comment
glab mr note create <mr-number> -m "LGTM"

# Resolve a discussion by note ID or discussion ID
glab mr note resolve 3107030349 <mr-number>

# Reopen a discussion by note ID or discussion ID
glab mr note reopen 3107030349 <mr-number>

# Merge
glab mr merge <mr-number>
```

Safer merge pattern:

```bash
# 1. Re-check the exact head SHA and mergeability right before merge
MR_JSON=$(glab api "projects/<namespace>%2F<project>/merge_requests/<iid>")
HEAD_SHA=$(jq -r '.sha' <<<"$MR_JSON")
jq '{state, detailed_merge_status, sha}' <<<"$MR_JSON"

# 2. Merge against the exact reviewed SHA
glab mr merge <iid> --sha "$HEAD_SHA" --remove-source-branch --yes

# 3. If the terminal prints "No pipeline running", treat it as informational.
#    Confirm success from the returned merge result or a fresh `glab mr view`.
glab mr view <iid>
```

## Issue Workflow

### Scope Hygiene

- Create an issue only after the task boundary is concrete enough to describe the problem, expected outcome, and scope without guessing.
- If you must create the issue early because the repository workflow requires it, write the body as a symptom-driven placeholder and revisit it after diagnosis.
- When later evidence changes the real scope, update the issue title/body before MR creation or merge. Also update the MR description so `Closes #<iid>` points to an issue that matches what actually shipped.
- Before applying final status labels such as `done`, run `glab issue view <iid>` and check that the issue is not stale, overly narrow, or contradicted by the MR.
- Prefer updating a too-narrow issue over creating a second issue for the same active branch unless the new work is independently shippable.

### Using CLI Commands

```bash
# Create
glab issue create --title "Bug" --label=bug --assignee=@me

# List
glab issue list --assignee=@me
glab issue list --label=doing

# Update
glab issue update 123 --label="doing"
glab issue update 123 --unlabel="todo"

# Close
glab issue close 123
```

After MR merge:

- If the issue was auto-closed through `Closes #<iid>`, run `glab issue view <iid>` and verify both `state` and labels.
- If GitLab closed the issue but left workflow labels such as `doing`, fix them explicitly with `glab issue update <iid> --unlabel doing --label done`.
- If the intended workflow requires verification after merge, keep the issue open and apply the repository's testing/verification label. Do not include `Closes #<iid>` in that MR.

### Using API (Recommended for Automation)

```bash
# Create issue
glab api --method POST "projects/namespace%2Fproject/issues" \
  --field title="Bug title" \
  --field description="Bug description" \
  --field labels="bug,todo"

# Update issue
glab api --method PUT "projects/namespace%2Fproject/issues/123" \
  --field description="Updated description"

# Update issue with real newlines (avoid literal \n)
DESC=$(cat <<'EOF'
背景:
- 现状说明...

验收标准:
- 条件 A
- 条件 B
EOF
)
glab api --method PUT "projects/namespace%2Fproject/issues/123" \
  --field "description=$DESC"
# Verify no escaped newline remains
glab api "projects/namespace%2Fproject/issues/123" | jq -r '.description' | rg '\\\\n' || true

# Add comment
glab api --method POST "projects/namespace%2Fproject/issues/123/notes" \
  --field body="Comment text"

# Reply to a comment (threaded discussion)
# 1. Get discussion ID
DISC_ID=$(glab api "projects/namespace%2Fproject/issues/123/discussions" | \
  jq -r '.[0].id')
# 2. Reply to discussion
glab api --method POST "projects/namespace%2Fproject/issues/123/discussions/$DISC_ID/notes" \
  --field body="Reply text"

# Delete comment
glab api --method DELETE "projects/namespace%2Fproject/issues/123/notes/<note_id>"

# Close issue
glab api --method PUT "projects/namespace%2Fproject/issues/123" \
  --field state_event="close"
```

## Sub-tasks (Work Items) - GitLab CE

**Only Task type can be a child of an Issue.** Regular issues cannot have parent-child relationships.

For issue-board-driven workflows, prefer a plain `Issue` as the unit that moves across columns. `Task` is best used as a child work item under an issue, not as the primary board card.

If a child task must become a board-tracked item, convert it to an issue and keep the relationship as a normal linked item:

1. Remove the parent hierarchy link from the task.
2. Convert the task to `Issue`.
3. Add a `relates_to` link back to the parent issue.

Example:

```bash
# IDs are global work item IDs
TASK_ID="gid://gitlab/WorkItem/1582"
PARENT_ID="gid://gitlab/WorkItem/1552"
ISSUE_TYPE_ID="gid://gitlab/WorkItems::Type/1"

# 1. Detach from parent
glab api graphql -f query="
mutation {
  workItemUpdate(input: {
    id: \"$TASK_ID\"
    hierarchyWidget: { parentId: null }
  }) {
    errors
  }
}"

# 2. Convert Task -> Issue
glab api graphql -f query="
mutation {
  workItemConvert(input: {
    id: \"$TASK_ID\"
    workItemTypeId: \"$ISSUE_TYPE_ID\"
  }) {
    errors
    workItem { iid workItemType { name } }
  }
}"

# 3. Keep the parent relationship as a normal linked item
glab api graphql -f query="
mutation {
  workItemAddLinkedItems(input: {
    id: \"$TASK_ID\"
    linkType: RELATED
    workItemsIds: [\"$PARENT_ID\"]
  }) {
    errors
  }
}"
```

### Method 1: REST API (create Task, then link)

```bash
# 1. Create Task type issue
glab api --method POST "projects/<namespace>%2F<project>/issues" \
  --field title="Task title" \
  --field issue_type="task"

# 2. Link to parent via GraphQL (see Method 2 for parent ID)
```

### Method 2: GraphQL (create + link in one call)

```bash
# 1. Get parent issue global ID
PARENT_ID=$(glab api graphql -f query='
query($path: ID!, $iid: String!) {
  project(fullPath: $path) {
    issue(iid: $iid) { id }
  }
}' -F path="namespace/project" -F iid="123" | jq -r '.data.project.issue.id')

# 2. Create task linked to parent
glab api graphql -f query='
mutation($path: ID!, $title: String!, $pid: ID!) {
  workItemCreate(input: {
    projectPath: $path
    title: $title
    workItemTypeId: "gid://gitlab/WorkItems::Type/5"
    hierarchyWidget: { parentId: $pid }
  }) {
    workItem { iid title }
    errors
  }
}' -F path="namespace/project" -F title="Task title" -F pid="$PARENT_ID"
```

### Delete Issue/Task (GraphQL only)

```bash
# 1. Get global ID (NOT iid)
GLOBAL_ID=$(glab api graphql -f query='
query {
  project(fullPath: "namespace/project") {
    issue(iid: "123") { id }
  }
}' | jq -r '.data.project.issue.id')
# Returns: gid://gitlab/Issue/456

# 2. Delete using global ID
glab api graphql -f query="
mutation {
  workItemDelete(input: {
    id: \"$GLOBAL_ID\"
  }) {
    errors
  }
}"
```

Work Item Type IDs:
- `gid://gitlab/WorkItems::Type/1` - Issue (cannot be child)
- `gid://gitlab/WorkItems::Type/5` - Task (can be child of Issue)

## CI/CD Workflow

```bash
# Watch pipeline
glab ci view

# List pipelines for a ref / branch
glab ci list --ref my-branch

# Check status
glab ci status

# View logs
glab ci trace

# Retry failed
glab ci retry <job-id|job-name>

# Lint config
glab ci lint

# Trigger pipeline
glab api --method POST "projects/:id/pipeline" --field ref="main"
```

## Repository Operations

```bash
# Clone
glab repo clone owner/repo

# Fork
glab repo fork owner/repo

# View details
glab repo view
```

## Working Outside Repository

Always use `-R` flag or API with full path:

```bash
# CLI flag
glab issue list -R owner/repo
glab mr list -R namespace/project

# API (URL-encode the path)
glab api projects/namespace%2Fproject/issues
```

## Milestones

```bash
# List milestones
glab api "projects/<namespace>%2F<project>/milestones" | jq '.[] | {iid, title, state}'

# Create milestone
glab api --method POST "projects/<namespace>%2F<project>/milestones" \
  --field title="2025.Q1" \
  --field description="Q1 交付目标" \
  --field due_date="2025-03-31"

# Update milestone
glab api --method PUT "projects/<namespace>%2F<project>/milestones/6" \
  --field state_event="close"

# Get issues in milestone
glab api "projects/<namespace>%2F<project>/milestones/6/issues"
```

## Time Tracking

Use Quick Actions in issue comments or description:

```
/estimate 4h          # Set estimate (supports: 1w, 2d, 3h, 30m)
/spend 2h             # Log time spent
/spend 1h 2025-01-04  # Log time on specific date
/remove_estimate      # Clear estimate
/remove_time_spent    # Clear all logged time
```

Via API:
```bash
# Set estimate (seconds)
glab api --method POST "projects/<id>/issues/123/time_estimate" --field duration="4h"

# Add time spent
glab api --method POST "projects/<id>/issues/123/add_spent_time" --field duration="2h"

# Get time stats
glab api "projects/<id>/issues/123" | jq '.time_stats'
```

## Quick Actions Reference

Use in issue/MR description or comments:

| Action | Command |
|--------|---------|
| Assign | `/assign @user` |
| Label | `/label ~doing ~C` |
| Remove label | `/unlabel ~todo` |
| Milestone | `/milestone %"2025.Q1"` |
| Due date | `/due 2025-12-31` |
| Relate | `/relate #123` |
| Close | `/close` |
| Reopen | `/reopen` |

## JSON Output for Scripting

```bash
# Get JSON output
glab mr list --output=json | jq '.[] | .title'

# API always returns JSON
glab api projects/:id/issues | jq '.[0].title'
```
