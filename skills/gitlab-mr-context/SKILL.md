---
name: gitlab-mr-context
description: Gather GitLab issue, merge request, pipeline, comment, and self-hosted GitLab context with reliable `glab api` commands. Use for MR review, review-to-fix, issue triage, GitLab comments, labels, time tracking, merge readiness, or self-hosted GitLab admin checks.
argument-hint: "[project] [iid]"
---

# GitLab MR Context

Use `glab api` as the stable path, especially on self-hosted GitLab.

## Defaults

- For Apex GitLab, set:

```bash
export GITLAB_HOST=gitlab.apexdata.com.cn
```

- URL-encode projects: `ty/tyclaw` -> `ty%2Ftyclaw`.
- Prefer `jq` over parsing human output.
- For long Markdown, write a temp file and pass `--raw-field body="$(cat file)"` or `--raw-field description="$(cat file)"`.

## Read Context

```bash
project='ty%2Ftyclaw'
iid='<iid>'
glab api "projects/$project/merge_requests/$iid" | jq '{iid,title,state,source_branch,target_branch,merge_status,sha,web_url}'
glab api "projects/$project/merge_requests/$iid/changes" | jq -r '.changes[].new_path'
glab api "projects/$project/merge_requests/$iid/pipelines" | jq '.[0] | {id,status,sha,web_url}'
glab api "projects/$project/merge_requests/$iid/notes?per_page=100" | jq 'map({id,author:.author.username,body})'
```

For issues:

```bash
glab api "projects/$project/issues/$iid" | jq '{iid,title,state,labels,web_url}'
glab api "projects/$project/issues/$iid/notes?per_page=100" | jq 'map({id,author:.author.username,body})'
```

## Merge Readiness

Report these, then stop unless the user asked you to merge:

- MR state and source SHA
- pipeline status
- unresolved discussions if available
- changed files
- linked issue state/labels
- exact validation already run or missing

## Rules

- Do not trust stale issue bodies over newer comments.
- Avoid `Closes #...` unless auto-close is intended.
- After merge, verify the MR and issue state instead of assuming labels changed.
