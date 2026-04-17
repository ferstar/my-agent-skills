# OpenCLI Web Channels Commands

这个参考文件只保留“网页渠道 + 网页读取”相关命令。

如果某个命令会修改站点状态，或者属于桌面 App 控制、页面探索、适配器生成，就不应通过这个 skill 使用。

## 前置条件

```bash
# 安装
npm install -g @jackwener/opencli

# 诊断浏览器桥接
opencli doctor
```

浏览器读取依赖：

1. Chrome 正在运行
2. 已登录目标网站
3. 已安装 Browser Bridge 扩展

## 参数类型先分清

在调用前，先确认这个命令需要的是哪种输入：

- 文本参数
  例如 `opencli doubao ask "香港攻略"`

- URL 参数
  例如 `opencli weixin download --url "https://mp.weixin.qq.com/s/xxx"`

不要把两者混用。

尤其是 URL 参数，禁止传这种值：

- `data:text/html,<html></html>`
- `about:blank`
- `javascript:...`
- 直接把 HTML 片段塞进 `--url`
- 没有来源依据的猜测链接

如果没有可靠 URL，就不要调用需要 `--url` 的命令。

再加一条硬规则：

- `--url` 只接受明确的 `http://` 或 `https://` 链接
- 不是 `http(s)` 的值，一律不要执行

也就是说：

- 允许：`https://mp.weixin.qq.com/s/xxx`
- 允许：`https://www.pudong.gov.cn/...`
- 禁止：`data:text/html,<html></html>`
- 禁止：`about:blank`
- 禁止：`<html>...</html>`
- 禁止：`www.example.com`

## 通用网页读取

```bash
opencli web read --url "https://example.com/article"
opencli web read --url "https://example.com/article" -f md
opencli web read --url "https://example.com/article" -f json
```

适合没有专用适配器的页面，或只想快速把页面内容转成 Markdown / JSON。

但要注意：`web read` 不是默认首选。
如果 OpenCLI 已经有站点/渠道专用命令，优先使用专用命令，`web read` 仅作为 fallback。

例如：

- 豆包提问，优先 `opencli doubao ask "香港攻略"`
- 微信文章导出，优先 `opencli weixin download --url "..."`
- 知乎问题读取，优先 `opencli zhihu question 34816524`
- 没有专用适配器的普通网页，才使用 `opencli web read`

一个常见错误是：

```bash
opencli web read --url "data:text/html,<html></html>"
```

这类调用通常说明参数拼错了。应该先回到上一步，确认：

1. 这次任务到底该用文本命令还是 URL 命令
2. 用户有没有给出真实网页链接
3. 这个链接是不是明确的 `http(s)` URL
4. 如果没有真实链接，是否应该改用专用命令而不是硬调 `web read`

### 参数拆解

```bash
opencli web read \
  --url "https://www.pudong.gov.cn/023004003/20251231/819733.html" \
  --output /tmp \
  --format yaml \
  --wait 30
```

这条命令适合“浏览器能打开，但普通抓取未必拿得到正文”的文章页。

- `--url`
  目标网页地址。尽量直接给详情页，不要给列表页。

- `--output /tmp`
  把导出结果写到 `/tmp`。适合临时检查；长期保留建议换成专门目录。
  终端摘要不是完整正文，正文通常会写到这个目录里的 Markdown 文件。

- `--format yaml`
  终端里输出 YAML，便于检查抓取字段是否完整。

- `--wait 30`
  页面加载后再额外等 30 秒，给脚本渲染和延迟内容注入留时间。
  如果结果仍然是 `failed — no content`，先检查是否进入了错误页或验证页，再决定是否继续加大等待时间。

### 什么时候显式加 `--wait`

优先用于这些页面：

- 首屏先出框架，正文晚一点才出现
- 有较重前端脚本或异步加载
- 政务站、媒体站、公告站等模板复杂页面
- 复用浏览器态后才能看到稳定内容的页面

### 输出判断

对 `yaml` / `table` 输出，重点看：

- `title` 是否正常
- `status` 是否不是 `failed — no content`
- `size` 是否明显大于空壳页面

### 正文在哪里

`web read` 的完整正文通常不在终端输出里，而是在 `--output` 指定目录下。

一个可验证的例子：

```bash
opencli web read --url "https://example.com" --output /tmp/opencli-web-read-check --format yaml
```

终端会输出摘要字段，但正文文件会落在类似下面的位置：

```text
/tmp/opencli-web-read-check/Example_Domain/Example_Domain.md
```

Windows 下可按同样思路理解：

```powershell
opencli web read --url "https://example.com" --output "C:\Temp\opencli-web-read-check" --format yaml
```

正文通常会落在：

```text
C:\Temp\opencli-web-read-check\Example_Domain\Example_Domain.md
```

所以如果任务是“读正文、摘录、总结、结构化提取”，正确顺序应该是：

1. 运行 `web read`
2. 看终端摘要确认是否成功
3. 进入 `--output` 目录定位生成的 `.md`
4. 基于磁盘上的正文文件继续处理

在 macOS 上，系统内部有时会把 `/tmp` 映射成 `/private/tmp`。
这属于同一个位置的系统实现细节；对说明和后续操作，优先沿用用户传入的 `--output` 路径即可。

Windows 也是同一个原则：优先沿用用户传入的原始路径，不要自动改写路径风格。

## 只读站点命令

### Doubao Web

这是网页渠道命令，不是桌面 App 控制。

```bash
opencli doubao status
opencli doubao new
opencli doubao ask "香港攻略"
opencli doubao send "香港自由行 3 天攻略，重点放在交通和亲子景点"
opencli doubao read
opencli doubao history
opencli doubao detail <conversation-id>
```

如果用户的目标是“借助豆包网页能力查资料、提问、读取回答”，优先用这一组命令，不要退化成 `web read` 去读豆包页面 DOM。

### Bilibili

```bash
opencli bilibili hot --limit 10
opencli bilibili search "rust"
opencli bilibili me
opencli bilibili favorite
opencli bilibili history --limit 20
opencli bilibili feed --limit 10
opencli bilibili user-videos --uid 12345
opencli bilibili subtitle --bvid BV1xxx
opencli bilibili dynamic --limit 10
opencli bilibili ranking --limit 10
opencli bilibili following --limit 20
```

### 知乎

```bash
opencli zhihu hot --limit 10
opencli zhihu search "AI"
opencli zhihu question 34816524
```

### 小红书

```bash
opencli xiaohongshu search "美食"
opencli xiaohongshu notifications
opencli xiaohongshu feed --limit 10
opencli xiaohongshu user xxx
opencli xiaohongshu creator-notes --limit 10
opencli xiaohongshu creator-note-detail --note-id xxx
opencli xiaohongshu creator-notes-summary
opencli xiaohongshu creator-profile
opencli xiaohongshu creator-stats
```

### 雪球

```bash
opencli xueqiu hot-stock --limit 10
opencli xueqiu stock --symbol SH600519
opencli xueqiu watchlist
opencli xueqiu feed
opencli xueqiu hot --limit 10
opencli xueqiu search "特斯拉"
opencli xueqiu earnings-date SH600519
opencli xueqiu fund-holdings
opencli xueqiu fund-snapshot
```

### Twitter / X

只保留读取类命令：

```bash
opencli twitter trending --limit 10
opencli twitter bookmarks --limit 20
opencli twitter search "AI"
opencli twitter profile elonmusk
opencli twitter timeline --limit 20
opencli twitter thread 1234567890
opencli twitter article 1891511252174299446
opencli twitter followers elonmusk
opencli twitter following elonmusk
opencli twitter notifications --limit 20
opencli twitter download elonmusk
```

### Reddit

```bash
opencli reddit hot --limit 10
opencli reddit hot --subreddit programming
opencli reddit frontpage --limit 10
opencli reddit popular --limit 10
opencli reddit search "AI" --sort top --time week
opencli reddit subreddit rust --sort top --time month
opencli reddit read --post-id 1abc123
opencli reddit user spez
opencli reddit user-posts spez
opencli reddit user-comments spez
opencli reddit saved --limit 10
opencli reddit upvoted --limit 10
```

### V2EX

```bash
opencli v2ex hot --limit 10
opencli v2ex latest --limit 10
opencli v2ex topic 1024
opencli v2ex me
opencli v2ex notifications --limit 10
opencli v2ex node python
opencli v2ex nodes --limit 30
opencli v2ex member username
opencli v2ex user username
opencli v2ex replies 1024
```

### Hacker News

```bash
opencli hackernews top --limit 10
opencli hackernews new --limit 10
opencli hackernews best --limit 10
opencli hackernews ask --limit 10
opencli hackernews show --limit 10
opencli hackernews jobs --limit 10
opencli hackernews search "rust"
opencli hackernews user dang
```

### YouTube

```bash
opencli youtube search "rust"
opencli youtube video "https://www.youtube.com/watch?v=xxx"
opencli youtube transcript "https://www.youtube.com/watch?v=xxx"
opencli youtube transcript "xxx" --lang zh-Hans --mode raw
```

### 微信公众号

```bash
opencli weixin download --url "https://mp.weixin.qq.com/s/xxx"
```

## 输出格式

```bash
opencli web read --url "https://example.com" -f md
opencli web read --url "https://example.com" -f json
opencli bilibili hot --limit 10 -f yaml
opencli reddit hot --limit 20 -f csv
```

支持的格式：`table`、`json`、`yaml`、`md`、`csv`。

## 明确排除

以下命令或能力不在这个 skill 的使用范围内：

- 桌面 App 控制：`cursor`、`chatgpt`、`doubao-app`
- 探索/录制/生成：`explore`、`record`、`generate`
- 写操作：`twitter post`、`twitter like`、`twitter reply`、`twitter follow`
- 写操作：`reddit comment`、`reddit upvote`、`reddit subscribe`
- 任何通用 UI 自动化、多步点击、表单提交
