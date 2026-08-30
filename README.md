# Peach

Peach（蜜桃）是单用户、本地优先的个人媒体系统。它统一索引本地磁盘、CloudDrive 和在线关注来源，提供搜索、播放、资料页、播放列表、复核与追更，并把观看行为和人工决定保存到本地 SQLite ledger。

Peach 适合在 Windows 与 macOS 两台个人设备上运行。当前运行状态、待办和验证结果见 [`docs/STATUS.md`](docs/STATUS.md)；开发约束从 [`AGENTS.md`](AGENTS.md) 开始读。

## 核心能力

- 按作品、女优、厂牌、创作者、系列和标签浏览馆藏。
- 播放本地与网盘媒体；不兼容容器生成可删除的转码缓存，不改写原文件。
- 保存稍后看、喜欢理由、观看状态、自动 Mix 和持久播放列表。
- 通过 `/review` 复核外部元数据、身份、图片和媒体失败候选。
- 从 Kemono 系、Rule34Video、Rule34.xxx 和 F95zone 发现更新；SimpCity 的机器人验证不会被绕过。
- 在 Windows writer 与 macOS reader 之间显式复制 ledger；发生分叉时转只读，不自动合并。

## 数据边界

Ledger 是资产、身份、行为和复核决定的真相源。Stash、CloudDrive、在线站点和 AI 都是适配器或候选来源，不能直接改写真相字段。

| 内容 | 位置或规则 |
| --- | --- |
| 数据库 | `peach-data/database/ledger.db` |
| 媒体路径 | Ledger 始终保存 Windows 盘符；macOS 在读取时转换 |
| 凭据 | `peach-data/secrets/`，不进入 Git、日志或 API 返回 |
| 派生图片 | 可删除重建；Windows → macOS 单向同步 |
| 真实写入 | 只允许当前 writer；迁移和不可逆操作必须先备份并取得授权 |
| 测试 | 只使用临时 SQLite 和临时媒体 |

两台机器各有本地 ledger 工作副本，共享目录只作传输点。服务启动不会自动复制；「同步 Ledger」和「接管 Ledger 写入」是显式操作。详细设计见 [`ADR-0017`](docs/adr/0017-dual-host-local-runtime-and-sync-boundaries.md)。

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

## 开发

Windows 初始化并运行测试：

```powershell
cd C:\Users\longm\Desktop\peach\peach-app
& py -3.14 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -e .
& .\scripts\test.ps1
```

macOS 初始化并运行测试：

```bash
cd ~/Desktop/lmd.gg/peach/peach-app
python3.14 -m venv .venv
./.venv/bin/python -m pip install -e ".[macos]"
./scripts/test.sh
```

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
Python 3.12/3.14 正式测试。前端依赖更新后，先安装锁定包：

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
| `/junk-files` | 垃圾文件分类与判断 |
| `/trash` | 回收站 |
| `/stats` | 统计、网盘资源同步与孤立缓存清理 |
| `/taste` | 口味画像与浏览记录管理 |

`/healthz` 提供无副作用健康状态，`/api/sources` 提供来源可达性。其他 API 契约以实现和测试为准，不在 README 维护容易漂移的端点全集。

在网盘或本地资源目录手动删除文件后，进入「管理 → 统计 → 资源同步」先扫描差异。扫描在后台运行并逐来源显示进度，离开页面不会中断；Peach 只核对已挂载来源，暂时不可读的目录会跳过而不是判成删除。缺失条目先进入回收站，可恢复的账本元数据不会立即丢失。确认同步时会再次核对候选项，并清理不再被正常馆藏使用的截图、海报、图片缩略图、封面和播放缓存；候选 CSV、来源证据、女优头像和厂牌 Logo 不作缓存删除。

媒体包里夹带的推广视频、广告图片、网址快捷方式和其它文件进入「管理 → 垃圾文件」（`/junk-files`）。页面按视频、图片、压缩包、音频、网址和其它文件分类；每项都可移入回收站，也可标记为「不是垃圾」并在「已排除」中撤销。Peach 按文件名、推广目录及各类型可用的时长／体积证据列候选，不自动永久删除。

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
- [`docs/STATUS.md`](docs/STATUS.md)：当前运行态、验证结果和下一步。
- [`docs/HANDOFF.md`](docs/HANDOFF.md)：跨任务长期有效的事实与工作约定。
- [`docs/REUSE.md`](docs/REUSE.md)：新增或替换实现前的复用清单。
- [`docs/adr/`](docs/adr/)：架构决定、原因和取舍。
