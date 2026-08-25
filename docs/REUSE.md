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
| 追更来源接口 | kemono 系公开 JSON API（`Accept: text/css`，站点自述的抓取路径）、rule34.xxx 官方 dapi（需账号 API key）、f95zone `latest_data.php` 与线程页 | 连接器边界、凭据隔离、变体与跨站重复判定、候选复核与批准后的 online asset 投影 |
| HTML 适配器 | Beautiful Soup 或 selectolax | 来源专用选择器和来源记录 |
| 位图 | Pillow | 头像/Logo 质量和来源策略 |
| 搜索 | SQLite FTS5 | 索引字段、排序、profile 感知筛选 |
| 女优姓名对照 | `li-peifeng/Jav-Actors-Mapping` 的固定 revision，仅作私有输入（仓库未声明许可证，不随 Peach 分发） | 精确匹配、冲突复核、别名、来源与真实 ledger 写入 |
| 女优头像候选 | Gfriends 的 GitHub raw 索引与单张媒体（只作外部 Provider，不克隆图库） | 名字链、质量档位、格式/尺寸/SHA-256 门槛、候选缓存、provenance、健康统计和人工复核 |
| JAV 元数据查询 | Javinizer-Go v1.5.1 单来源 JSON CLI（MIT） | 只发送规范番号；Peach 管 source profile、逐字段优先级、原始证据、健康统计、候选复核与批准后的 ledger 投影 |
| FC2 跨号证据 | 已缓存的 fc2cmadb 评论收获 + Peach ledger 媒体事实 | 稳定 pair、合集/分片保护、hash/时长/尺寸佐证、库外 evidence、健康统计和人工复核；不依赖 FC2-Leak-Detector/JavSP |
| 媒体探测/转码 | Peach 管理的 FFmpeg/ffprobe | 任务策略和 Media Engine 编排 |
| HTML5/HLS/DASH 播放 | Video.js 8.23.9 + 内置 VHS（Apache-2.0，本地固定版本） | 流方案、授权、稳定时长、回退顺序和统计面板 |
| 照片灯箱轮播 | Swiper 14.1.0（MIT，本地固定版本，按需 `<script>` 注入）的 Thumbs / Keyboard / Zoom 模块 | 图集来源与顺序、缩略图缓存与计费口径、瀑布流本身（CSS `column-count`，不经过 Swiper） |
| 图标 | 固定版本的本地 Lucide 子集；Health Icons 24 px outline（CC0）用于领域图标 | 标签、状态和交互设计 |
| 定时轮询 | 持久追更配置落地后使用 APScheduler | 任务定义和安全策略 |
| 本地文件事件 | watchdog + 定期对账 | 媒体身份和漏报修复 |
| 过渡期元数据/媒体 | Stash GraphQL、CommunityScrapers、Stash 任务系统 | 适配、对账、退出门槛 |
| 局域网发现 | Python zeroconf | 服务生命周期和真实客户端验收 |
| 生成产物跨机同步 | Syncthing 2.1.x，Windows send-only → Mac receive-only | 目录划分、忽略规则、方向固定与「Mac 不发布正式产物」的边界 |
| Windows 托盘 | pystray 0.19.5（LGPLv3）、Pillow、Win32 Per-Monitor V2 DPI | Peach 服务归属、后台更新检查、菜单动作、品牌图标 |
| 智能体用量/配额 | Provider 官方配额接口；T3 Code/CodexBar 提供本地历史 | 任务路由、脱敏、过期快照标记 |
| 视频出处/片尾证据 | 现有 FFmpeg 抽帧 + Windows.Media.Ocr WinRT Provider（Windows PowerShell 5.1 固定适配器） | 有界首尾采样、缓存、来源/Full version 分类、健康统计与人工复核 |
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
| `import_performer_portraits.py`（原 `agent/claude/performer-portraits`） | `scripts/audit_performer_portraits.py` + `scripts/localize_performer_names.py` | 一次性导入已执行完并记在 STATUS；后继只产 CSV，不写头像文件 |
| `normalize_code_suffix.py`（原 `agent/claude/code-suffix`） | `web_contract.is_jav_code` + `scripts/audit_code_creators.py` | 226 条后缀已落库；形态判据收敛成一份实现 |
| `dedupe_performer_creator.py`（原 `agent/claude/dedupe-identity`） | `scripts/merge_duplicate_identities.py` | 后继的判据已扩到跨 kind、同 kind 与真子集三轮，旧脚本判据更窄 |

## 当前替换队列

已完成：共享 Media/Job/HTTP 边界、feedparser、Pillow、Beautiful Soup、FTS5、可安全导入的批处理脚本和按任务范围终止进程。

1. Video.js 已接管详情播放；`MediaEngine.stream_plan` 已让 115/PikPak 原生 MP4 使用 HLS 临时短片段，仍需补自适应码率、多路清单和生产验收。CloudDrive 的虚拟盘固定块预取仍属于来源层成本。
2. Javinizer-Go 已接管番号元数据查询适配；来源扩展只加入 Peach policy 白名单/profile 与健康统计，优先启用其现有 scraper，不在 Peach 分叉站点解析器。
3. 将剩余 status/suggest/ledger 应用逻辑移到 repository/application 端口，再删除旧 CLI 表面。
4. Peach 不做 token/成本日志扫描器，也不绑定 T3 Code 私有 RPC；使用其界面、CodexBar 和官方实时配额入口。
5. 「模仿/参考/对齐」不等于允许凭记忆近似。先取得并登记可复现证据；否则标记 `未取得`，不得作为忠实复刻发布。2026-08-17 的 YouTube 详情与 Shorts 动作栏参考已登记在 `docs/HANDOFF.md`，Peach 只复用可测量的层级、尺寸和状态语义。
