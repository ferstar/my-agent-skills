---
name: wechat-article-extractor
description: Extract title, metadata, and HTML content from WeChat Official Account article links (mp.weixin.qq.com). Use when the user sends a公众号文章链接 and wants the article parsed, read, or summarized. Prefer this minimal local skill over broad WeChat toolkits when the task is just fetch-and-extract.
---

# WeChat Article Extractor Min

Use `scripts/extract.js` to fetch and parse a WeChat article URL.

## Workflow

1. Call the extractor with the article URL.
2. If it returns `done: true`, use `data.msg_title`, `data.msg_desc`, `data.msg_content`, `data.msg_author`, and `data.msg_publish_time_str`.
3. Convert HTML content to plain text before summarizing if the user wants a readable summary.
4. If it returns `done: false`, surface the Chinese error message directly and suggest a fallback (screenshots, pasted text, or another link) when helpful.

## Minimal usage

```javascript
const { extract } = require('./scripts/extract.js');
const result = await extract('https://mp.weixin.qq.com/s?...');
```

## Notes

- Supports direct `mp.weixin.qq.com` links and some Sogou WeChat result pages.
- Returns HTML in `data.msg_content`; strip tags for summaries.
- Common failure modes are rate limiting, expired links, deleted content, blocked content, or unsupported URLs.
- Keep this skill narrow: extraction first, summarization second.
