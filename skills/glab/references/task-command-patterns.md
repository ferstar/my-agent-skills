<!-- Command paths below are relative to the skill root, not this reference directory. -->

## Quick reference

### Merge requests

```bash
glab mr create --title "Fix" --description "Closes #123"
glab mr list --reviewer=@me
glab mr checkout 123
glab mr approve 123
glab mr note resolve 3107030349
glab mr merge 123 --remove-source-branch
```

### Issues

```bash
glab issue create --title "Bug" --label bug
glab issue list --assignee=@me --all
glab issue view 123
glab issue close 123
```

### CI/CD

```bash
glab ci status
glab ci view
glab ci list --ref main
glab ci trace
glab ci retry <job-id|job-name>
glab ci lint
```

### Outside a repo

```bash
glab mr list -R owner/repo
glab issue list -R owner/repo
glab api projects/owner%2Frepo
```

## High-value patterns

### API-first issue update

```bash
glab api --method PUT projects/<namespace>%2F<project>/issues/123 \
  --raw-field description="$(cat /tmp/issue-description.md)"
```

### MR status and pipelines

```bash
# Inspect MR summary in terminal
glab mr view 123

# Inspect mergeability and pipeline fields via API
glab api "projects/<namespace>%2F<project>/merge_requests/123" \
  | jq '{state, merge_status, detailed_merge_status, pipeline, head_pipeline}'

# List pipelines for a ref when you need current CI state
glab ci list --ref my-branch
```

### Threaded reply

```bash
DISC_ID=$(glab api "projects/<namespace>%2F<project>/issues/123/discussions" | jq -r '.[0].id')
glab api --method POST "projects/<namespace>%2F<project>/issues/123/discussions/$DISC_ID/notes" \
  --field body="Reply text"
```

If the user gives a work item URL such as `/-/work_items/163#note_3612`, map it like this before replying:

```bash
# 1. Resolve the work item through the issues API.
glab api "projects/<namespace>%2F<project>/issues/163"

# 2. Find the discussion that contains note 3612.
DISC_ID=$(glab api "projects/<namespace>%2F<project>/issues/163/discussions" \
  | jq -r '.[] | select(any(.notes[]; .id == 3612)) | .id')

# 3. Reply in that discussion thread.
glab api --method POST "projects/<namespace>%2F<project>/issues/163/discussions/$DISC_ID/notes" \
  --field body="Reply text"
```

### Upload and reuse local attachments in issue / MR evidence

When acceptance evidence is a local screenshot or other file, do not paste a local `C:\...` path into an Issue/MR note. Other reviewers cannot resolve the sender's filesystem. Upload it to the GitLab project first, then use the API response's canonical `full_path` in the note or MR description.

Preferred flow:

```bash
# 1. Upload the local file as multipart form data.
upload_json=$(glab api --method POST "projects/<project-id>/uploads" \
  --form "file=@<absolute-path>/acceptance.webp")

# 2. Build the canonical GitLab URL from full_path; do not hand-build /uploads/...
asset_path=$(printf '%s' "$upload_json" | jq -r '.full_path')
asset_url="https://<gitlab-host>${asset_path}"

# 3. Add or update the note with the remote Markdown image.
glab api --method POST "projects/<project-id>/issues/<iid>/notes" \
  --raw-field "body=验收附件：![acceptance](${asset_url})"
```

Rules:

- Prefer the returned `full_path` (normally `/-/project/<id>/uploads/...`) over the shorter `url` (`/uploads/...`) when constructing a reusable absolute link. If the API returns `markdown`, inspect it before using it; do not silently replace a canonical project-scoped path with a root `/uploads/...` path.
- Verify the upload response contains `id`, `full_path`, and the expected filename before editing the Issue/MR. For an existing workflow-generated acceptance note, preserve its hidden workflow marker when replacing the body.
- Verify the note body after writing with the notes API and confirm it contains the canonical remote URL, not a local path or a `file://` URI.
- A private GitLab project may return `302 -> /users/sign_in` to unauthenticated `curl` or a browser. That is an access/session result, not proof that the upload is corrupt. Verify the binary through an authenticated `glab api` request; if non-members must view it, use a separately accessible artifact/storage location rather than assuming project uploads are public.
- For image evidence, validate the local file type and dimensions before upload. WebP is suitable for screenshots when the target GitLab/browser session renders it; otherwise retain a PNG fallback and verify the rendered note in an authenticated browser session.

### Download attachments from issue / note threads

When an issue note or discussion note contains `/uploads/...` links and the files must enter the repository, do not rely on the UI URL with plain `curl`. On self-hosted GitLab that often returns an HTML login page instead of the binary file.

Preferred flow:

```bash
# 1. Read the note body and extract the upload paths you need.
glab api "projects/<project-id>/issues/<iid>/notes/<note_id>"

# 2. Download the binary through the uploads API, not the UI path.
glab api "projects/<project-id>/uploads/<secret>/<filename>" > "docs/<Tender>/attachment/<flattened-name>"

# 3. Verify the file type before wiring references.
file "docs/<Tender>/attachment/<flattened-name>"
```

Rules:

- Land repo-bound evidence in the target tender's `attachment/` directory before updating正文 or appendix references.
- Flatten the filename to the repo's attachment naming scheme; do not keep issue-thread URLs in draft text.
- After download, verify the artifact is really a PDF/image/document and not HTML.
- If the attachment came from a note URL like `.../issues/40#note_6105`, use the note API first to recover the exact `/uploads/<secret>/<filename>` path.

### Work item conversion

Use GraphQL `workItemConvert` when REST cannot change the work item type. See `references/rest_api_commands.md` for mutation examples.

### Moving issues between projects

Before moving, confirm the source is a movable issue:

```bash
glab api "projects/<namespace>%2F<project>/issues/<iid>" | jq '{iid, issue_type, type, web_url}'
```

If GitLab rejects the move with `Moving 'Task' is not supported.`, treat it as a manual migration:

```bash
# 1. Read the source issue / work item and notes.
glab api "projects/<src>/issues/<iid>"
glab api "projects/<src>/issues/<iid>/notes?per_page=100"

# 2. Recreate it in the target project as a normal issue.
glab issue create -R <target-owner>/<target-repo> \
  --title "..." \
  --description "$(cat /tmp/body.md)"

# 3. Reapply state explicitly if the source was closed.
glab issue close <new-iid> -R <target-owner>/<target-repo>
```

Rules:

- Do not assume child tasks under a moved parent can also be moved.
- Preserve the original work item URL in the recreated issue body.
- Summarize important discussion when recreating manually.
- Re-check the target project after migration; parent moves can auto-create or auto-link child items.

## Core workflows

### Create and merge an MR

```bash
git push -u origin feature-branch
glab mr create --title "Add feature" --description "Implements X"
glab mr approve 123
glab mr merge 123 --remove-source-branch
```

### Review an MR

```bash
glab mr view 123
glab mr diff 123
```

Posting comments, approving, checking out a branch, retrying CI, merging, and deleting branches are separate actions; execute only the actions covered by the request.

### Monitor or wait for CI

```bash
glab ci view
glab ci trace
glab ci retry <job-id|job-name>
```

If local helper scripts are present, use:

```bash
./scripts/glab-mr-await.sh 123 --timeout 600
./scripts/glab-pipeline-watch.sh --timeout 300
```

## Helper scripts

If this skill includes local scripts, prefer them for repeatable watch/wait flows:

- `scripts/glab-mr-await.sh` — wait for MR approval and successful pipeline
- `scripts/glab-pipeline-watch.sh` — monitor pipelines with CI-friendly exit codes

Environment variables commonly used by scripts:
- `TIMEOUT`
- `INTERVAL`

## Self-hosted GitLab

```bash
export GITLAB_HOST=gitlab.example.org
glab mr list -R group/project
```

## Troubleshooting

Common examples:

- `command not found: glab` → install `glab`
- `command not found: jq` → install `jq`
- `401 Unauthorized` → verify `GITLAB_TOKEN` or `glab auth login`
- `404 Project Not Found` → verify project path and permissions
- `not a git repository` → use `-R owner/repo`
- `Unknown flag` → use the documented pattern first; inspect exact subcommand help once only if the error remains
- `HTTP 415` on `glab api --input` → retry with `--field` or `--raw-field`

For detailed recovery steps, read `references/troubleshooting.md`.

## Best practices

1. Let the first task-specific command verify auth; run separate auth checks only after auth/host errors or explicit user request.
2. Prefer API-first automation for repeatability.
3. Use minimal token scopes.
4. Prefer structured output for scripts.
5. Validate rendered issue/MR descriptions after multiline updates.
6. Keep `-R owner/repo` explicit when outside a repository.
7. Use helper scripts for CI polling when available.
