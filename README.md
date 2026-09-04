# Peach

Peach is a single-user, local-first personal media system: it indexes media you already own —
local disks, mounted cloud drives, online subscriptions — and serves search, playback, profile
pages, playlists and manual review from one FastAPI process backed by a local SQLite ledger.
It is built for one person self-hosting on their own machines over a LAN, not for teams or public
deployment. Status: pre-1.0. Windows and macOS are first-class; on Linux only the Python service
and the CLI are supported, without tray or mount integration. A full English version is in
[`README.en.md`](README.en.md).

Peach（蜜桃）是单用户、本地优先的个人媒体系统。它统一索引本地磁盘、CloudDrive 和在线关注来源，提供搜索、播放、资料页、播放列表、复核与追更，并把观看行为和人工决定保存到本地 SQLite ledger。

Peach 适合在 Windows 与 macOS 两台个人设备上运行。当前运行状态与验证结果见 [`docs/STATUS.md`](docs/STATUS.md)，待办见 [`docs/PRODUCT_BACKLOG.md`](docs/PRODUCT_BACKLOG.md)；开发约束从 [`AGENTS.md`](AGENTS.md) 开始读。

## 核心能力

- 按作品、女优、厂牌、创作者、系列和标签浏览馆藏。
- 播放本地与网盘媒体；不兼容容器生成可删除的转码缓存，不改写原文件。
- 保存稍后看、喜欢理由、观看状态、自动 Mix 和持久播放列表。
- 通过 `/review` 复核外部元数据、身份、图片和媒体失败候选。
- 从 FANBOX、SubscribeStar、Patreon 官方渠道，Kemono/Pawchive/Coomer 归档站，Rule34Video、Rule34.xxx、Rule34 Paheal 和 F95zone 发现更新；SimpCity 的机器人验证不会被绕过。
- 在 Windows writer 与 macOS reader 之间显式复制 ledger；发生分叉时转只读，不自动合并。

## 数据边界

Ledger 是资产、身份、行为和复核决定的真相源。CloudDrive、在线站点和 AI 都是适配器或候选来源，不能直接改写真相字段。

| 内容 | 位置或规则 |
| --- | --- |
| 数据库 | `peach-data/database/ledger.db` |
| 媒体路径 | Ledger 始终保存 Windows 盘符；macOS 在读取时转换 |
| 凭据 | `peach-data/secrets/`，不进入 Git、日志或 API 返回 |
| 派生图片 | 可删除重建；Windows → macOS 单向同步 |
| 真实写入 | 只允许当前 writer；迁移和不可逆操作必须先备份并取得授权 |
| 测试 | 只使用临时 SQLite 和临时媒体 |

两台机器各有本地 ledger 工作副本，共享目录只作传输点。服务启动不会自动复制；「同步 Ledger」和「接管 Ledger 写入」是显式操作。详细设计见 [`ADR-0017`](docs/adr/0017-dual-host-local-runtime-and-sync-boundaries.md)。

## 范围与免责声明

- 仓库只有代码、文档和固定的前端依赖。它不包含任何媒体、封面、缩略图或元数据，也不附带任何
  站点的数据副本；它索引的是运行它的人自己已有的库。
- 连接器只访问使用者自己有权访问的来源，凭据由使用者自己提供。Peach 不绕过机器人验证、付费墙
  或任何访问控制：遇到这类拦截时它报告「未取得」并停在那里。
- 从外部来源取回的标题、图片和说明，内容与版权属于各站点及其创作者。Peach 把它们当候选保存，
  并保留来源与置信度，供使用者自己核对。

## 目录

```text
peach-app/
├─ src/peach/        FastAPI、媒体、ledger、迁移和 Provider
├─ web/              无构建步骤的前端
├─ migrations/       带版本和校验和的 SQLite 迁移
├─ scripts/          构建、检查和批处理入口
├─ tests/            隔离测试
├─ docs/             状态、架构、复用决策和 ADR
├─ AGENTS.md         Codex 与 Claude 共用入口
└─ CLAUDE.md         Claude 导入入口
```

仓库不保存媒体、数据库、凭据、日志、`.venv`、构建产物或 worktree。

## 安装

三步，不需要事先准备任何目录或配置文件。在仓库根目录执行：

```powershell
& py -3.14 -m venv .venv                            # macOS: python3.14 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -e .    # macOS: ./.venv/bin/python -m pip install -e ".[macos]"
& .\.venv\Scripts\peach.exe init                    # macOS: ./.venv/bin/peach init
```

`peach init` 建数据根、把账本迁到最新 schema、生成本机 CA，并写出 `<数据根>/config.toml`。
默认数据根是仓库同级的 `peach-data/`，`--data-root` 可改，环境变量 `PEACH_DATA_ROOT` 覆盖它。
之后 `peach serve` 就能起服务；监听地址、端口、媒体盘符映射和复制开关都在那个设置文件里改，
逐项说明见 [`docs/OPERATIONS.md`](docs/OPERATIONS.md)。

没有设置文件也能启动：`/healthz` 报 `configured=false`，页面提示先跑 `peach init`。

## 开发

初始化虚拟环境后运行测试，Windows 用 `& .\scripts\test.ps1`，macOS/Linux 用 `./scripts/test.sh`。
每个平台只有一个正式测试入口。脚本会定位主项目的虚拟环境、强制加载当前 worktree 的 `src`，并核对实际导入路径。仓库使用标准库 `unittest`，不使用 pytest。

开发时按功能域运行必要测试，例如 Windows 用 `& .\scripts\test.ps1 -Scope follow`，
macOS/Linux 用 `./scripts/test.sh follow`。可选域为 `follow`、`catalog`、`media`、`sync`、
`metadata`、`tooling`；不传参数仍跑 `full`。跨多个域、修改迁移/共享测试设施/依赖、准备发布或
改动影响面较大时必须跑全量，单一局部功能不再反复跑无关测试。

## 依赖维护

Python 运行时与可选工具全部在 `pyproject.toml` 精确固定版本；前端自托管包由
`package.json`、`package-lock.json` 和 `web/vendor/` 共同固定。可选依赖不进入默认运行环境：

| extra | 消费者 |
| --- | --- |
| `build` | PyInstaller 打包 |
| `macos` | AppKit 菜单栏 |
| `vision` | 头像、封面的人脸取景脚本 |
| `maintenance-115` | 115 SHA-1 对账脚本 |

GitHub Dependabot 每周检查 Python、npm 和 GitHub Actions；每个更新 PR 都运行 Windows/macOS、
Python 3.14 正式测试。前端依赖更新后，先安装锁定包：

```powershell
npm ci --ignore-scripts
```

再从锁定包重建自托管文件和来源哈希：

```powershell
npm run vendor:web
```

最后确认仓库里的固定文件与清单一致：

```powershell
npm run check:vendor
```

这套 Node 工具只用于维护固定前端文件，Peach 页面仍没有运行时构建步骤，也不依赖 CDN。

检查迁移状态并启动本地开发服务：

```powershell
& .\.venv\Scripts\peach.exe migrate status
& .\.venv\Scripts\peach.exe serve --port 8900
```

生产托盘、macOS 菜单栏、本地 CA、mDNS 和 ledger 复制的当前入口与限制见 [`docs/STATUS.md`](docs/STATUS.md) 和 [`docs/HANDOFF.md`](docs/HANDOFF.md)。README 不复制易过期的 IP、版本、端口归属或证书状态。

## 主要页面

| 路由 | 用途 |
| --- | --- |
| `/` | 首页 |
| `/item/{id}` | 作品详情 |
| `/performers` | 女优索引 |
| `/performers/{name}` | 女优资料 |
| `/creators/{name}` | 创作者资料与图集 |
| `/tags` | 标签管理 |
| `/immerse` | 沉浸模式 |
| `/playlists` | 播放列表 |
| `/follow` | 关注观看 |
| `/follow-manage` | 关注管理与凭据状态 |
| `/review` | 人工复核 |
| `/data-cleanup` | 数据清理总览：垃圾文件、重复文件与空文件夹 |
| `/junk-files` | 垃圾文件分类与判断 |
| `/trash` | 回收站 |
| `/stats` | 统计、网盘资源同步与孤立缓存清理 |
| `/taste` | 口味画像与浏览记录管理 |

`/healthz` 提供无副作用健康状态，`/api/sources` 提供来源可达性。其他 API 契约以实现和测试为准，不在 README 维护容易漂移的端点全集。

在网盘或本地资源目录手动删除文件后，进入「管理 → 统计 → 资源同步」先扫描差异。扫描在后台运行并逐来源显示进度，离开页面不会中断；Peach 只核对已挂载来源，暂时不可读的目录会跳过而不是判成删除。缺失条目先进入回收站，可恢复的账本元数据不会立即丢失。确认同步时会再次核对候选项，并清理不再被正常馆藏使用的截图、海报、图片缩略图、封面和播放缓存；候选 CSV、来源证据、女优头像和厂牌 Logo 不作缓存删除。

媒体包里夹带的推广视频、广告图片、网址快捷方式和其它文件进入「管理 → 数据清理」（`/data-cleanup`）。垃圾文件页按视频、图片、压缩包、音频、网址和其它文件分类；每项都可打开网盘所在位置、移入回收站，也可标记为「不是垃圾」并在「已排除」中撤销。重复文件与垃圾文件共用这个管理入口，空文件夹也从其中的独立 Fieldset 显式清理。顶栏多选支持批量执行当前视图可用的判断或回收操作。Peach 按文件名、推广目录及各类型可用的时长／体积证据列候选，不自动永久删除；从回收站永久删除物理文件后，只会继续删除同一来源根以内随之变空的父目录，来源根本身不会删除。

## 关注与候选

关注管理支持粘贴链接、名称或 ID，也可直接登记 FANBOX、Patreon 和 SubscribeStar 的
官方创作者页。每个渠道的复选框决定它是否参与检查更新；联网只发生在显式查找和检查更新时，
关闭的渠道也不会出现在关注观看页，重新启用后恢复显示。服务启动、健康检查和普通浏览不会联网。
F95zone 站内索引没有命中名称时，结果区会给出对应的 Google 查询入口；Google 结果只供人核对真实线程链接，不会自动登记来源。

Rule34.xxx 标签身份不区分大小写。跨站来源按规范作者归组，F95 标题中的 `Collection(s)` 不属于作者名。
官方主页同时给出唯一作者名与平台账号时，Peach 自动学习该平台别名；已有人工作决定时不覆盖。
只有名称相似而没有官方身份链的情况仍只产生建议，用户确认后才合并；别名可随时移除。作者头像优先从已验证的
官方 FANBOX/Pixiv 页面取得，归档站只作回退。连接器设计与证据见
[`ADR-0019`](docs/adr/0019-site-follow-connectors-and-variant-grouping.md)。

抓到的更新保持 `new` 或 `seen` 候选状态。只有显式保存或在 `/review` 批准后，数据才进入对应 ledger 真相或在线资产。

## 文档入口

- [`AGENTS.md`](AGENTS.md)：每次改动都必须遵守的边界和技能索引。
- [`docs/STATUS.md`](docs/STATUS.md)：当前运行态与验证结果。
- [`docs/PRODUCT_BACKLOG.md`](docs/PRODUCT_BACKLOG.md)：开放需求与待执行的操作。
- [`docs/HANDOFF.md`](docs/HANDOFF.md)：跨任务长期有效的事实与工作约定。
- [`docs/REUSE.md`](docs/REUSE.md)：新增或替换实现前的复用清单。
- [`docs/adr/`](docs/adr/)：架构决定、原因和取舍。

## 许可证

Peach 以 AGPL-3.0-or-later 发布，全文见 [`LICENSE`](LICENSE)。它的实际含义：修改后分发，或修改后作为网络服务
提供给他人，都必须以同一许可证公开源码。

Copyright (C) 2026 longmeidao

固定在仓库里的第三方前端文件各自保留上游许可证，文件与来源哈希在
[`web/vendor/`](web/vendor/)。FFmpeg 不随仓库或构建产物分发，由使用者自行安装并遵守其许可证。
