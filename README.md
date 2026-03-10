# my-agent-skills

Public repository of custom Agent Skills.

## Structure

- `skills/<skill-name>/` — one skill per directory
- each skill contains a required `SKILL.md`
- optional resources: `scripts/`, `references/`, `assets/`

## Current skills

### `wechat-article-extractor`

Extract title, author, publish time, description, cover image, and HTML content from WeChat Official Account article links (`mp.weixin.qq.com`).

Current design goals:
- keep the skill narrow and easy to maintain
- prefer modern, minimal dependencies
- optimize for the common case: fetch an article, extract readable content, summarize it

## Conventions

- Keep runtime checks and smoke tests in `tests/`, not inside skill directories

- Keep each skill focused on one job
- Put trigger conditions and workflow in `SKILL.md`
- Avoid committing `node_modules`, caches, or temporary outputs
- Prefer standard library and small dependency sets over legacy packages
