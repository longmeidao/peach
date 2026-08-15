# 复用清单

这是 Codex 与 Claude 共用的实现查找表。新增或恢复代码前必须先查本文件。

## Peach 必须自研的领域逻辑

以下属于产品行为，继续由 Peach 实现：

- 女优、厂牌、创作者、标签的规范身份、别名和来源；
- profile 行为、稍后看、口味和推荐排序；
- 本地、115、PikPak、Stash、在线来源的绑定和回退策略；
- 计费来源授权、隐私分类和候选复核导入；
- 私有获取来源、出处引用和发现关键词；
- 创作者级视觉采样语义；
- 推理 Provider 与 Agent Provider 的能力契约；
- 任务归属、进度、取消、成本和证据规则。

## 必须复用的成熟实现

| 能力 | 复用实现 | Peach 负责 |
|---|---|---|
| HTTP | 全项目共用的 `httpx.Client`/transport | 来源策略、DTO、脱敏 |
| RSS/Atom | `feedparser` | 有界抓取、快照、复核、导入 |
| HTML 适配器 | Beautiful Soup 或 selectolax | 来源专用选择器和来源记录 |
| 位图 | Pillow | 头像/Logo 质量和来源策略 |
| 搜索 | SQLite FTS5 | 索引字段、排序、profile 感知筛选 |
| 媒体探测/转码 | Peach 管理的 FFmpeg/ffprobe | 任务策略和 Media Engine 编排 |
| HLS/DASH 播放 | hls.js 或 Shaka Player | 流方案、授权、回退顺序 |
| 图标 | 固定版本的本地 Lucide 子集；Health Icons 24 px outline（CC0）用于领域图标 | 标签、状态和交互设计 |
| 定时轮询 | 持久追更配置落地后使用 APScheduler | 任务定义和安全策略 |
| 本地文件事件 | watchdog + 定期对账 | 媒体身份和漏报修复 |
| 过渡期元数据/媒体 | Stash GraphQL、CommunityScrapers、Stash 任务系统 | 适配、对账、退出门槛 |
| 局域网发现 | Python zeroconf | 服务生命周期和真实客户端验收 |
| Windows 托盘 | pystray 0.19.5（LGPLv3）、Pillow、Win32 Per-Monitor V2 DPI | Peach 服务归属、后台更新检查、菜单动作、品牌图标 |
| 智能体用量/配额 | Provider 官方配额接口；T3 Code/CodexBar 提供本地历史 | 任务路由、脱敏、过期快照标记 |
| 视频出处/片尾证据 | 现有 FFmpeg 抽帧 + 经复核的 OCR/视觉适配器 | 首尾采样策略、来源、不完整版候选 |
| 参考产品行为 | 当前线上交互 + 有版本的公开 DOM/CSS/JS；取不到源码时用精确截图测量 | 证据登记、无障碍、Peach 差异、回归检查 |

依赖的第一个消费者及其隔离测试必须在同一改动落地，否则不引入依赖。

## 已删除旧实现与当前继任者

| 已删除/旧名称 | 当前实现 | 规则 |
|---|---|---|
| `rm-web.py` / `rm-web.html` | `src/peach/api.py`、`src/peach/web_contract.py`、`web/index.html` | 不得恢复旧 HTTP server |
| `rm-javlookup.py` | `scripts/scrape_codes.py` | 扩展来源适配器，不再分叉刮削器 |
| `rm-probe.py` | `scripts/probe.py` | 可复用策略移入 `src/peach`，保留续跑语义 |
| `rm-sheets.py` | `scripts/sheets.py` | 共用 FFmpeg/任务原语，不再新建抽帧管线 |
| `rm-ledger.py` | `scripts/ledger.py` + repository/migrations | 新产品读取进入 repository，不放回旧 CLI |
| `rm-status.py` | `scripts/status.py` | 状态命令只读 |
| `rm-suggest.py` | `scripts/suggest.py` | 排序逻辑逐步移到应用端口后 |
| `rm-trafficwatch.py` | `scripts/traffic_watch.py` | 只停止任务拥有的进程树 |
| `rm-sha1.py` | `scripts/sync_sha1_115.py` | 复用 Provider 哈希，不盲目重算网盘媒体 |

## 当前替换队列

已完成：共享 Media/Job/HTTP 边界、feedparser、Pillow、Beautiful Soup、FTS5、可安全导入的批处理脚本和按任务范围终止进程。

1. 浏览器使用 Stash 转码前，先增加 Media Engine 流方案 API 和成熟 HLS/DASH 播放器。
2. 编写新来源适配器前，先配置并评估 Stash 元数据 Provider。
3. 将剩余 status/suggest/ledger 应用逻辑移到 repository/application 端口，再删除旧 CLI 表面。
4. Peach 不做 token/成本日志扫描器，也不绑定 T3 Code 私有 RPC；使用其界面、CodexBar 和官方实时配额入口。
5. “模仿/参考/对齐”不等于允许凭记忆近似。先取得并登记可复现证据；否则标记 `未取得`，不得作为忠实复刻发布。
