# my-agent-skills

Private skill repo for custom Agent Skills.

## Layout

- `skills/<skill-name>/` — one skill per directory
- each skill should contain `SKILL.md`
- optional: `scripts/`, `assets/`, `refs/`, `package.json`

## Conventions

- Keep each skill focused on one job
- Put trigger conditions and workflow in `SKILL.md`
- Do not commit `node_modules`, caches, or temp outputs
- Prefer minimal dependencies
- Add a tiny test script when practical

## Current skills

- `wechat-article-extractor-min` — extract WeChat Official Account article metadata and content from `mp.weixin.qq.com` links
