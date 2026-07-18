---
name: tianbot-docs
description: 查询 Tianbot 官方文档并回答 ROS2GO、TOM、Tianracer、Tianrover、Tianbot mini、ROSECHO 等产品的使用、恢复、兼容性、升级、备份、规格和故障排查问题。仅在 Tianbot 产品问题上使用，并实时核对官方页面。
---

# Tianbot Docs 查询助手

当用户询问 Tianbot 系列产品相关问题时，通过抓取 docs.tianbot.com 官方文档来给出准确答案。

## 文档结构

docs.tianbot.com 的主要产品文档路径：

| 产品 | 文档路径 |
|------|---------|
| ROS2GO | `/ros2go/guide/` |
| ROS2GO 启动方法 | `/ros2go/guide/how-to-start` |
| ROS2GO 备份 | `/ros2go/guide/how-to-backup` |
| ROS2GO 升级 | `/ros2go/guide/how-to-update` |
| ROS2GO 恢复 | `/ros2go/guide/how-to-recover` |
| ROS2GO FAQ | `/ros2go/faq` |
| ROS2GO 兼容性 | `/ros2go/applicable/` |
| TOM 机器人 | `/tianbot/` |
| Tianrover | `/tianrover/` |
| Tianracer | `/tianracer/` |
| Tianbot mini | `/tianbot_mini/` |
| Robomaster TT | `/rmtt/` |
| ROSECHO | `/rosecho/` |
| ROS 基础 | `/basic/` |
| 仿真模拟 | `/simulation/` |

## 查询流程

1. **判断产品和问题类型**，选择最相关的文档路径
2. 用可用的网页工具打开对应官方页面：`https://docs.tianbot.com{路径}`
3. 从页面内容中提取准确答案
4. 如果第一个页面没有答案，尝试子页面或 FAQ
5. 引用来源 URL，方便用户核实

## 注意事项

- 文档内容可能随版本更新，始终以抓取到的最新页面为准
- 如果页面内容不完整，尝试抓取子页面
- 对于硬件兼容性问题，优先查 `/ros2go/applicable/`
- 对于启动失败问题，优先查 `/ros2go/guide/how-to-start#cannot-start`
- 不从本 skill 复述可能变化的账号、版本、容量或兼容性结论；每次从当前官方页面核对并附直接链接
