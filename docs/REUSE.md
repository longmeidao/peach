# 复用清单

这是 Codex 与 Claude 共用的实现查找表。新增、恢复或重写代码前必须按
`.claude/skills/peach-reuse-first/SKILL.md` 先查本文件、当前树、Git 历史和成熟外部实现。

## 复用决策门槛

- 先用真实输入做无写入 POC，再决定“直接依赖、固定来源实现、保留自研”三者之一。
- 采用项要记录固定版本、许可证、首个消费者和 Peach 保留的领域边界；候选依赖不得空转。
- 保留自研要记录被拒绝的候选和不可替代约束，不能只写“特殊需求”。
- 外部项目不适合作为运行时依赖，但其公开数据模型或算法明显更成熟时，固定 revision 后作为参考
  实现；许可证不允许派生或来源不稳定时只作行为证据，不复制代码。

## Peach 必须自研的领域逻辑

以下属于产品行为，继续由 Peach 实现：

- 女优、厂牌、创作者、标签的规范身份、别名和来源；
- profile 行为、稍后看、播放列表、口味和推荐排序；
- 本地、115、PikPak、Stash、在线来源的绑定和回退策略；
- 计费来源授权、隐私分类和候选复核导入；
- 私有获取来源、出处引用和发现关键词；
- 创作者级视觉采样语义；
- 推理 Provider 与 Agent Provider 的能力契约；
- 任务归属、进度、取消、成本和证据规则。

## 必须复用的成熟实现

| 能力 | 复用实现 | Peach 负责 |
|---|---|---|
| HTTP | 默认复用全项目共用的 `httpx.Client`/transport；FANBOX 公开 `post.info` 按固定证据复用 `curl_cffi==0.16.2` | 来源策略、DTO、脱敏、站点限定、大小上限；不求解机器人质询 |
| RSS/Atom | `feedparser` | 有界抓取、快照、复核、导入 |
| 追更来源接口 | FANBOX 公开帖子 API（详情只使用用户自己的可选 Cookie 与 Firefox 传输特征）、kemono 系公开 JSON API（`Accept: text/css`，站点自述的抓取路径）、rule34.xxx 官方 dapi（需账号 API key）、Paheal 标签/详情页、Gofile contents API（需 Premium 账号 API token）、f95zone `latest_data.php`、线程页与站内 masked XHR | 连接器边界、凭据隔离、多媒体顺序、文件站目标校验、变体与跨站重复判定、候选复核与批准后的 online asset 投影 |
| HTML 适配器 | Beautiful Soup 或 selectolax | 来源专用选择器和来源记录 |
| 位图 | Pillow | 头像/Logo 质量和来源策略 |
| 搜索 | SQLite FTS5 | 索引字段、排序、profile 感知筛选 |
| 女优姓名对照 | `li-peifeng/Jav-Actors-Mapping` 的固定 revision，仅作私有输入（仓库未声明许可证，不随 Peach 分发） | 精确匹配、冲突复核、别名、来源与真实 ledger 写入 |
| 女优头像候选 | Gfriends 的 GitHub raw 索引与单张媒体（只作外部 Provider，不克隆图库） | 名字链、质量档位、格式/尺寸/SHA-256 门槛、候选缓存、provenance、健康统计和人工复核 |
| 厂牌 Logo 候选 | 厂牌官网确认的社交 handle → unavatar URL 解析 → 平台 CDN 单图 | handle 归属、内容缓存、方形归一、精确/感知哈希、provenance、健康统计与变化复核 |
| JAV 元数据查询 | Javinizer-Go v1.5.1 单来源 JSON CLI（MIT） | 只发送规范番号；Peach 管 source profile、逐字段优先级、原始证据、健康统计、候选复核与批准后的 ledger 投影 |
| FC2 跨号证据 | 已缓存的 fc2cmadb 评论收获 + Peach ledger 媒体事实 | 稳定 pair、合集/分片保护、hash/时长/尺寸佐证、库外 evidence、健康统计和人工复核；不依赖 FC2-Leak-Detector/JavSP |
| 媒体探测/转码 | Peach 管理的 FFmpeg/ffprobe | 任务策略和 Media Engine 编排 |
| HTML5/HLS/DASH 播放 | Video.js 8.23.9 + 内置 VHS（Apache-2.0，本地固定版本） | 流方案、授权、稳定时长、回退顺序和统计面板 |
| 分卷文件命名 | [Plex 官方命名](https://support.plex.tv/articles/naming-and-organizing-your-movie-media-files/)的 `cd/disc/disk/dvd/part/pt + 数字` 与 [Kodi 官方 File Stacking](https://kodi.wiki/view/File_stacking)只作行为证据；运行时复用当前树的 `part_marker`，不新增扫描器依赖 | 兼容馆藏已有的裸数字和 A–H 后缀；仅连续、唯一标记自动合卡，保留每个 asset 和播放会话，不拼接或改写媒体 |
| 照片灯箱轮播 | Swiper 14.1.0（MIT，本地固定版本，按需 `<script>` 注入）的 Thumbs / Keyboard / Zoom 模块 | 图集来源与顺序、缩略图缓存与计费口径、瀑布流本身（CSS `column-count`，不经过 Swiper） |
| 导航排序 | 浏览器原生 HTML Drag and Drop | 桌面鼠标直接拖动、落点提示、上下移动按钮作为键盘与触屏回退、`localStorage` 持久化；不为单列排序引入额外运行时依赖 |
| 图标 | 固定版本的本地 Lucide 子集；Health Icons 24 px outline（CC0）用于领域图标 | 标签、状态和交互设计 |
| 资源文本中间省略 | Vercel Geist `MiddleTruncate` 行为契约 + 浏览器原生 `ResizeObserver`、`Intl.Segmenter`、Canvas 测量 | 文件名、路径、URL、ID 等资源标识用 `data-middle-truncate`；标题、说明、人名、标签等语义文本保留末尾省略；页面源测试登记全部末尾省略选择器，新增截断未先分类会失败 |
| 定时轮询 | APScheduler 3.11.3（MIT，固定稳定版；3.x `BackgroundScheduler` / interval trigger） | 只在 ledger writer 启动、持久频率、首次延迟、单实例、手动/自动互斥、运行状态与来源错误汇总 |
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
6. Web UI 组件优先复用 `web/js/ui-components.js` 和 `.claude/skills/peach-web-ui/SKILL.md` 的语义矩阵。Peach 不引入 Geist React 运行时，只复用已锁定证据中的 Note／Progress／Switch／Tooltip／Collapse／Menu／Fieldset／Scroller／Empty State／Search Input／Spinner／Loading Dots 与 Dialog motion 语义、ARIA 和版式层级；整页异步重绘复用导航代际隔离，没有消费者的 Vercel 后台筛选器不照搬。

## 2026-08-28 自研实现审计

本轮覆盖追更来源、浏览器历史、批处理锁、MP4 索引、证书、迁移、网络监听、流媒体、同步与更新。
以下是候选判断，不等于依赖已经进入生产；替换仍须按上面的同批闭环执行。

| 当前能力 | 判断 | 已验证证据与 Peach 边界 |
|---|---|---|
| `taste_history.py` 自写 Chrome/Firefox/Zen/Safari SQLite 解析 | **已替换为 `browserexport==0.4.4`** | Python 3.14 依赖解析通过；审计 POC 在本机 7 个 Chrome/Firefox/Zen profile 上与 Peach 逐库计数完全一致，macOS 的 Safari／Zen／Firefox／Chrome 路径发现有独立测试。首个消费者是 `/taste` 的本机读取与导出导入；Peach 保留 SQLite backup、Takeout、私有原始存储、域名分析和 candidate 生成，并在 Windows 自己关闭只读连接以避开依赖的文件句柄滞留。跨主机同步不由该依赖提供，仍须显式导出、传输和按来源去重合并。 |
| `jobs.PidFileLock` | **优先替换为 `portalocker==4.3.0` 的 `PidFileLock`** | Python 3.14 解析通过，现成覆盖 PID 写入、锁持有者、原子替换、陈旧文件与释放清理。Peach 只保留任务归属和错误文案映射。 |
| Rule34Video 媒体页解析 | **部分替换为 `yt-dlp==2026.8.19`** | 对真实视频 4533145 无写入提取成功，取得 4 个格式、31 个标签、缩略图与时间。Peach 仍负责作者分页、合集/超多 model 排除、来源分组和跨站去重。 |
| Rule34.xxx / Paheal 高清封面 | **固定参考 gallery-dl `86047cf67a12bdb6ff1085774f8ad9fc347e8da9`，运行时复用现有 FFmpeg** | gallery-dl（GPL-2.0）只作协议行为证据，不引入或复制为运行时：booru URL 明确支持 `sample_url`/`preview_url`/`file_url` 回退，Paheal 抽取器只取得原始 `file_url`。真实 POC 中 Rule34.xxx 历史 preview 为 250×141、同哈希 sample 为 1920×1080；Paheal 页面只有低清 poster/og:image，原视频可生成 1280×720 JPEG。视频缩略图工具 ffmpegthumbnailer 默认取 10% 位置，Peach 不再引入 GPL 运行时；直接复用 FFmpeg `blackframe` 导出的 `lavfi.blackframe.pblack`，在开头 30 秒选第一张黑色像素低于 98% 的帧，并用版本化缓存键淘汰旧黑帧。Peach 继续负责 URL 白名单、同源代理、按需双并发抽帧、缓存与低清失败回退，不新增依赖、不改 ledger。 |
| FANBOX 正文解析 | **已采用 PixivUtil2 `v20251112` / `e537e96` 的公开正文模型** | Peach 的独立规范化 DTO 已覆盖 image/text/file/article/video/entry、`fileMap`、`embedMap`、`urlEmbedMap` 和旧 HTML 正文，并保留正文顺序、稳定去重、可播放媒体与文件页边界；BSD-2-Clause 依据写在实现头部。PixivUtil2 是完整下载器而非可嵌入解析库，因此不引入整套依赖；传输继续固定 `curl_cffi==0.16.2`。真实公开帖 12228983 只读 POC 得到 article、6 图和 Gofile `OS2Qz9`。 |
| `mp4index.py` 有界 MP4 关键帧索引 | **保留自研** | PyAV 需要 demux，`pymp4` 依赖旧 Construct，Bento4 是额外二进制；都不能证明在云盘文件上保留“只读 moov/stss/stts、避免整片流量”的约束。 |
| `certs.py` 固定项目 CA 与短期叶证书 | **保留自研 policy，继续调用 OpenSSL** | mkcert 会接管本机 CA 安装/私钥，不能保持跨设备固定项目 CA；cryptography 只替换证书编码且增加原生依赖，不能删除 Peach 的 Apple 398 天与 CA 生命周期策略。 |
| `migrations.py` SQLite 迁移 | **保留自研** | Alembic 会引入 SQLAlchemy/Mako/greenlet；现有范围只需顺序 SQL、校验和、备份与 PyInstaller 资源定位，没有 ORM 消费者。 |
| Gofile API | **保留直接 HTTP** | 官方没有维护中的 Python SDK；社区 wrapper 只是薄封装，不能绕过 Premium `contents` 权限，也不能减少 Peach 的 Bearer 隔离与媒体规范化。 |
| `netwatch.py`、streaming/segments、sync、versioning/Windows update | **保留现有边界** | 分别是无 PyObjC 的系统通知、FFmpeg/Starlette 上的会话策略、单 writer ledger 规则和 Git/PyInstaller 更新契约；通用替代会保留同量 policy 或扩大依赖。 |

FANBOX 与浏览器历史替换已完成；PID 锁和 Rule34Video 依次进入替换实施。其余保留项在约束改变或候选实现更新时
重新跑 POC，不因本表结论永久豁免外部检索。
