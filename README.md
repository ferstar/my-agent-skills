# my-agent-skills

Public repository of custom Agent Skills.

## Structure

- `skills/<skill-name>/` — one skill per directory
- each skill contains a required `SKILL.md`
- optional resources: `scripts/`, `references/`, `assets/`
- repository-level smoke tests live in `tests/`

## Current skills

### `wechat-article-extractor`

Extract title, author, publish time, description, cover image, and HTML content from WeChat Official Account article links (`mp.weixin.qq.com`).

Design goals:
- keep the skill narrow and easy to maintain
- prefer modern, minimal dependencies
- optimize for the common case: fetch an article, extract readable content, summarize it
- protect behavior with smoke tests during refactors

### `glab`

GitLab CLI skill for issues, merge requests, CI/CD, API operations, threaded discussion replies, and work item conversion or hierarchy updates.

Design goals:
- keep `SKILL.md` as a routing layer
- move detail into `references/`
- prefer `glab api` for repeatable automation

## Conventions

- Keep each skill focused on one job
- Put trigger conditions and workflow in `SKILL.md`
- Keep runtime checks and smoke tests in `tests/`, not inside skill directories
- Avoid committing `node_modules`, caches, or temporary outputs
- Prefer standard library and small dependency sets over legacy packages
- Run every new or imported skill through `skill-creator` conventions before treating it as done
