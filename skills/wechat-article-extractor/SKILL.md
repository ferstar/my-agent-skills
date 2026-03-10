---
name: wechat-article-extractor
description: Extract title, metadata, and HTML content from WeChat Official Account article links (`mp.weixin.qq.com`). Use when the user sends a公众号文章链接 and wants the article parsed, read, summarized, or converted to plain text. Trigger on requests about 微信公众号文章提取、公众号链接解析、WeChat article extraction, or when a workflow needs article title/author/date/content from a WeChat link.
---

# WeChat Article Extractor

Use `scripts/extract.js` to fetch and parse a WeChat article URL.

## Setup

Install dependencies once before first use:

```bash
npm install
```

## Workflow

1. Call the extractor with the article URL.
2. If it returns `done: true`, use `data.msg_title`, `data.msg_desc`, `data.msg_content`, `data.msg_author`, and `data.msg_publish_time_str`.
3. Strip HTML tags from `data.msg_content` before summarizing or quoting the article in plain text.
4. If it returns `done: false`, return the Chinese error message directly.
5. When extraction fails because of rate limits, expired links, deleted content, blocked content, or unsupported URLs, suggest a fallback such as screenshots, pasted text, or another link.

## Notes

- Supports direct `mp.weixin.qq.com` links and some Sogou WeChat result pages.
- Keeps scope narrow: extract first, summarize second.
- Prefer this skill over broad WeChat toolkits when the task is just fetch-and-extract.
