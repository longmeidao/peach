<p align="center">
  <img src="resources/peach-logo.png" alt="Peach 蜜桃" width="96">
</p>

<h1 align="center">Peach · 蜜桃</h1>

<p align="center">把散落在磁盘、网盘和关注来源里的媒体，整理成自己的馆藏。</p>

<p align="center">
  <a href="https://github.com/longmeidao/peach/releases">下载 Windows 测试版</a> ·
  <a href="#快速开始">快速开始</a> ·
  <a href="#文档">文档</a> ·
  <a href="README.en.md">English</a>
</p>

<p align="center">
  <a href="https://github.com/longmeidao/peach/actions/workflows/test.yml"><img src="https://img.shields.io/github/actions/workflow/status/longmeidao/peach/test.yml?branch=master&amp;label=tests&amp;style=flat" alt="测试状态"></a>
  <a href="https://github.com/longmeidao/peach/releases"><img src="https://img.shields.io/github/v/release/longmeidao/peach?include_prereleases&amp;label=release&amp;style=flat" alt="发行版本"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-AGPL--3.0--or--later-blue?style=flat" alt="AGPL-3.0-or-later"></a>
</p>

Peach 是单用户、本地优先的个人媒体系统。在自己的电脑上搜索、播放、整理已有媒体，也能从手机浏览器经局域网访问。馆藏、观看记录和人工复核决定保存在本机 SQLite ledger。

> **18+** 面向成年人的成人内容馆藏。仓库不含媒体与站点数据；文档中的演示素材仅限 SFW。连接器需要使用者拥有访问权限，不绕过付费墙、机器人验证或其他访问控制。

## 能做什么

本机“配置”提供 Peach 代理、开机自启及静默选项。采集来源选择“Peach 代理”或“直接连接”；扫描与采集统一在“数据管理”。“设置 → 浏览”选择默认排序与方向。独立 Windows 包可在配置页卸载，选择是否删除 Peach 数据；原始媒体保留。源码安装显示手动移除说明。

| 能力 | 使用方式 |
| --- | --- |
| 浏览与搜索 | 按作品、女优、厂牌、创作者、系列和标签查找视频与图集；没有署名人的作品归为「未归属」一类，可在卡片和详情页点开 |
| 播放与收藏 | 播放本地和挂载网盘媒体，保存稍后看、观看状态、Mix 与播放列表 |
| 关注与追更 | 登记官方或归档来源，显式检查更新，在站内查看和保存内容 |
| 复核与整理 | 核对外部候选，处理重复文件、垃圾文件、脱盘条目和回收站 |
| 口味与记录 | 查看口味画像，管理浏览记录和喜欢理由 |

CloudDrive · 115 与 CloudDrive · PikPak 按本机文件夹接入；先在 CloudDrive 登录并挂载，再交给 Peach 索引。也可以只使用本地磁盘。

托盘管理的服务可在本机通过「管理 → 配置」调整媒体来源；使用局域网域名打开也能进入。首启页和配置页检测缺失依赖时提供下载链接，挂载驱动提示按操作系统显示。

在「配置」或「数据管理」点击「扫描并补全资料」，可统一扫描文件夹、识别已有 NFO 和本地海报，并采集缺失资料。首页在处理期间提供进度入口，配置页显示当前阶段。支持同名 NFO、单影片目录的 `movie.nfo` 和单集 NFO；资料保留原始出处，在「复核资料」确认后写入馆藏。已有本地标签会保留，目录中有多部影片时不会共用 `movie.nfo`。
「管理 → 配置 → 检查更新」显示当前版本与 GitHub 最新测试版。独立 Windows 包可直接下载并准备更新，进度实时显示；完成后选择「立即重启」或「稍后」，程序自动安装，失败时恢复旧版本。

复核名称前提供勾选框，支持 Shift 连选，按候选数量、来源或字段分组。筛选项随复核类别更新，可选择具体分类并全选当前分类；批量操作只处理当前可见的所选项目。多来源候选可统一选择共同来源，点击通过后才会采用；失败项保留选择和错误提示，可重试。身份候选提供来源资料、本地作品样本和文件位置入口，可打开全部作品核对；通过后登记身份判断。

首次设置可选择进入浏览器历史记录导入指南；完成导入后指南隐藏，点击「跳过」会在当前浏览器记住选择，折叠仍保留指南。需要补充记录时使用「口味」页的读取或导入按钮。设置中的「SFW 模式」会模糊、降低饱和度并压暗图片和视频，停止悬停预览，文字保持可见。数据管理中的「网盘与本地数据库」仅在配置网盘后显示；空文件夹清理也支持本地磁盘。

关注来源包括 FANBOX、Patreon、SubscribeStar，以及 Kemono、Pawchive、Coomer、Rule34 系列与 F95zone。来源可用性受站点和使用者权限限制；采集边界与支持情况见 [来源采集](docs/SOURCING.md)。

右上角设置可控制打开本地作品和关注视频详情时是否自动播放。

首页包含尚无缩略图的视频；搜索推荐仅来自当前馆藏。空馆藏保留头像、厂牌与标签布局，并提供添加内容与来源的入口。

人物头像和厂牌标识在大图、紧凑模式中允许适度放大；明显过小的图片居中，周围用同图模糊补底。小于 64 px 的展示区域保持普通图标样式。

设置中的「JAV 默认封面」可选官方封面或预览图，适用于首页、接着看、Mix、作品卡片和播放队列；缺图时使用另一种封面。「JAV 封面默认大小」可选大图或小图，两种大小都使用所选封面。偏好保存在当前浏览器。

## 快速开始

Peach 处于 **pre-1.0** 阶段，界面目前只有中文。

| 平台 | 当前使用方式 |
| --- | --- |
| Windows | 独立测试包，或源码运行 |
| macOS | 源码运行；独立桌面包仍在开发 |
| Linux | 不在支持范围，未测试 |

### Windows 测试包

1. 从 [GitHub Releases](https://github.com/longmeidao/peach/releases) 下载 `Peach-<版本>-windows-x64.zip`，完整解压。
2. 双击 `Peach.exe`，在首次设置页选择已有媒体文件夹并提交。
3. 打开馆藏浏览；媒体文件夹与服务配置可从页面设置或托盘进入。

测试包只在本机访问，不需要 Python、Git、Node 或 OpenSSL。数据保存在
`%LOCALAPPDATA%\Peach\peach-data`，与程序目录分开。更新时先退出托盘，再完整解压新版，保留数据目录。

FFmpeg 与 ffprobe 需另装；缺少它们时可浏览和播放浏览器兼容格式，转码、探测与缩略图不可用。
测试包未签名；下载校验、配置与问题反馈见 [Windows 测试版](docs/TESTING_DESKTOP.md)。

### 源码运行

需要 Git、[uv](https://docs.astral.sh/uv/getting-started/installation/) **0.12.10** 和 **Python 3.12 或更高**。下面示例使用 3.14，uv 可自动下载缺失的 Python；CI 覆盖 3.12 与 3.14。
普通运行不需要 Node；修改前端需要 Node 24 或更高。

先克隆仓库并进入目录：

```shell
git clone https://github.com/longmeidao/peach.git peach-app
cd peach-app
```

Windows：在 PowerShell 创建环境、安装并启动首次设置：

```powershell
uv sync --locked --python 3.14
& .\.venv\Scripts\peach-tray.exe
```

macOS：在终端创建环境、安装菜单栏依赖并启动首次设置：

```shell
uv sync --locked --python 3.14 --extra macos
./.venv/bin/peach-tray
```

首次设置页会配置媒体文件夹、访问范围和端口。也可使用 `peach init` 的终端问答，再用 `peach serve` 启动服务；可执行文件位于上述虚拟环境目录。

源码部署默认使用仓库同级的 `peach-data/`；自定义位置需设置 `PEACH_DATA_ROOT`。
首次设置的访问密码为可选项：留空时，能连接到 Peach 的设备可直接访问。配置页可设置、修改或关闭密码，登录页可选择保持登录时间。已有部署保留当前登录要求。本机 CA 生成需要 OpenSSL。
配置、HTTPS、CloudDrive 挂载与非交互初始化详见 [运行与配置](docs/OPERATIONS.md)。

## 数据属于自己

- 媒体保留在原目录；转码使用可删除的派生缓存，不改写原文件。
- SQLite ledger 保存馆藏、身份、观看行为和人工决定；外部元数据与 AI 断言保留来源与置信度，经复核才成为真相。
- 凭据保存在数据目录的 `secrets/`，不进入 Git、日志或 API 返回。迁移和不可逆操作必须先备份并取得授权。
- 每个部署只服务一个人，不面向团队或公开部署。
- 可选的多机复制默认关闭，目前验证形态是 Windows writer + macOS reader。两端各有本地 ledger，共享目录只传输；复制与接管为显式操作，分叉时只读，不自动合并。见 [复制边界](docs/adr/0017-dual-host-local-runtime-and-sync-boundaries.md)。

仓库不分发媒体、封面、缩略图、元数据或任何站点的数据副本。外部标题、图片与说明的内容及版权属于对应站点和创作者。

## 开发与贡献

后端是 FastAPI 模块化单体，SQLite ledger 是真相源。前端以 Vite + TypeScript + Preact island 逐页迁移；
`web/` 提供现有页面与已提交的构建产物，运行时由 Python 直接服务，不依赖 Node 或 CDN。

| 路径 | 内容 |
| --- | --- |
| `src/peach/` | API、媒体、ledger 与来源适配器 |
| `frontend/` | TypeScript、Preact island 与 Vite 构建 |
| `web/` | 页面、样式、自托管依赖与 `web/dist/` 产物 |
| `migrations/` | SQLite 版本迁移 |
| `scripts/`、`tests/` | 开发入口、维护脚本与隔离测试 |
| `docs/` | 使用说明、架构与项目状态 |

开始修改前阅读 [工作契约](AGENTS.md)。测试使用临时数据库与临时媒体；在隔离工作树运行正式入口。

Windows：运行与当前改动对应的检查：

```powershell
& .\scripts\test.ps1
```

macOS：运行与当前改动对应的检查：

```shell
./scripts/test.sh
```

默认 `auto` 按影响域选测；CI 分层与依赖维护见 [测试与依赖](docs/TESTING.md)。前端安装、构建、类型检查与产物提交见
[前端开发](docs/FRONTEND.md)。依赖以项目清单和锁文件为准，Dependabot 每周检查 Python、npm 与 GitHub Actions。

提交问题请附版本、操作步骤、预期与实际结果；不要附带真实账本、媒体、Cookie 或私钥。
安全问题按 [安全政策](SECURITY.md) 报告。

## 文档

| 要做什么 | 入口 |
| --- | --- |
| 下载、配置与反馈测试包 | [Windows 测试版](docs/TESTING_DESKTOP.md) |
| 配置媒体、局域网、HTTPS 与同步 | [运行与配置](docs/OPERATIONS.md) |
| 了解采集来源与证据边界 | [来源采集](docs/SOURCING.md) |
| 确认当前运行状态 | [项目状态](docs/STATUS.md) |
| 查看开放需求 | [产品待办](docs/PRODUCT_BACKLOG.md) |
| 修改与维护项目 | [工作契约](AGENTS.md) · [前端开发](docs/FRONTEND.md) · [复用清单](docs/REUSE.md) |
| 了解长期约定与架构 | [交接说明](docs/HANDOFF.md) · [架构决策](docs/adr/) |

README 描述当前主线能力；已安装版本与验证结果以项目状态为准，发行制品以 Releases 为准。
文档迭代方式见 [README 维护](docs/README_MAINTENANCE.md)。

## 许可证

[AGPL-3.0-or-later](LICENSE) · Copyright (C) 2026 longmeidao。

固定的第三方前端文件保留上游许可证与来源记录，见 [web/vendor](web/vendor/)。
FFmpeg 不随仓库或制品分发，使用者需自行安装并遵守其许可证。
