---
name: opencli
description: 使用 OpenCLI 读取依赖 Chrome 登录态或前端渲染的网页，以及已支持的站点渠道命令。用户指定 OpenCLI 或需要浏览器会话时使用；普通公开网页优先直接读取工具。不用于通用 UI 自动化或发帖、评论、发送消息等写操作。
---

# OpenCLI Web Channels

1. 有站点专用命令时优先使用，如 `weixin download`、`youtube transcript`；否则用 `opencli web read --url "<url>"`。
2. 区分文本与 URL 参数：`doubao ask` 接收问题文本；`--url` 只接收用户提供或从已读页面可靠取得的真实 HTTP(S) 地址。禁止传入 HTML、占位字符串、`data:`、`javascript:`、`about:blank` 或猜测的详情页链接。
3. 输出按任务需要选择 `md`、`json`、`csv` 等格式和条数。命令、输出路径、参数及错误处理见 [web-read-commands.md](references/web-read-commands.md)，按所需章节读取。
4. 运行依赖 Chrome、Browser Bridge 扩展和 `opencli`。首次任务调用即可验证可用性；遇到桥接故障再执行 `opencli doctor`，缺少登录态时说明所需用户操作。
5. 读取后核对页面标题、正文及验证页/错误页状态，并给出来源。桌面操作或复杂交互改用当前环境的 Browser / Computer Use 工具。
