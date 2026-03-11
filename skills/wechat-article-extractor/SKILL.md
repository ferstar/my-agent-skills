---
name: wechat-article-extractor
description: Extract title, metadata, and article HTML from WeChat Official Account links (`mp.weixin.qq.com`). Use when the user sends a 公众号文章链接 and wants the article parsed, read, summarized, converted to plain text, or inspected for title, author, publish date, and content.
---

# WeChat Article Extractor

Use `scripts/extract.js` to fetch and parse a WeChat article URL.

## Setup

Install dependencies in the skill directory when needed:

```bash
npm install
```

Skip reinstalling if dependencies are already present and the extractor runs successfully.

## Workflow

1. Run the extractor with the article URL.
2. If it returns `done: true`, use fields such as `data.msg_title`, `data.msg_desc`, `data.msg_content`, `data.msg_author`, and `data.msg_publish_time_str`.
3. Extract first, then summarize or transform.
4. Strip HTML tags from `data.msg_content` before quoting or summarizing in plain text.
5. If it returns `done: false`, surface the Chinese error message directly.
6. When extraction fails because of rate limits, expired links, deleted content, blocked content, or unsupported URLs, suggest a fallback like screenshots, pasted text, or a fresh link.

## Command pattern

```bash
node scripts/extract.js '<wechat-article-url>'
```

## Notes

- Supports direct `mp.weixin.qq.com` links and some Sogou WeChat result pages.
- Prefer this skill over broad WeChat toolkits when the task is specifically article fetch-and-extract.
- Preserve article metadata before rewriting or summarizing.
