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

| 能力 | 说明 |
| --- | --- |
| 浏览与搜索 | 按作品、女优、厂牌、创作者、系列和标签查找视频与图集；搜索栏边打边补出馆藏里的身份与作品；没有署名人的作品归为「未归属」一类 |
| 播放与收藏 | 播放本地和挂载网盘媒体，保存稍后看、观看状态、Mix 与播放列表；离开详情可缩成角落小窗继续播 |
| 扫描与补全 | 扫描文件夹，识别已有 NFO 和本地海报，采集缺失资料，经「复核资料」确认后写入馆藏 |
| 关注与追更 | 登记官方或归档来源，显式检查更新，在站内查看和保存内容 |
| 复核与整理 | 核对外部候选与身份判断，处理重复文件、垃圾文件、脱盘条目和回收站 |
| 口味与记录 | 查看口味画像，导入浏览记录，管理喜欢理由 |

媒体来源可以只用本地磁盘，也可以接 CloudDrive 挂出的 115 与 PikPak：先在 CloudDrive 登录并挂载，再把文件夹交给 Peach 索引。缓存和读取长度怎么填见 [CloudDrive 配置与调优](docs/CLOUDDRIVE.md)。

关注来源包括 FANBOX、Patreon、SubscribeStar，以及 Kemono、Pawchive、Coomer、Rule34 系列、F95zone 与 SimpCity（需要你自己的登录 cookie）。来源可用性受站点和使用者权限限制；采集边界与支持情况见 [来源采集](docs/SOURCING.md)。

界面偏好保存在当前浏览器，在右上角「设置」里改：默认排序、JAV 封面用官方封面还是预览图、打开详情是否自动播放，以及把图像模糊降饱和、关掉悬停预览的「SFW 模式」。

界面采用 Board 风格。设置里的「增加对比度」关闭导航玻璃的透明与折射。数量和时间支持范围内自定义，可关闭的功能使用开关控制。

侧栏顶部选择媒体库，底部切换明暗主题并打开设置。配置中可设置媒体库名称和图标，同名文件夹归入一库；库选择限定作品列表与筛选项。网盘默认显示本机提供的网盘图标。

登录页勾选「保持登录」时，使用此浏览器安全设置里的保持时间（1–365 天，默认 30 天）。不勾选时使用最长 12 小时的浏览器会话。

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
`%LOCALAPPDATA%\Peach\peach-data`，与程序目录分开。

右上角「设置 →『这台电脑』→ 更新与维护」比对 GitHub 上的最新测试版，独立包可以在页面里下载并安装，失败时恢复旧版；
也可以退出托盘后手动完整解压新版，保留数据目录。同一处提供卸载，可选是否一并删除 Peach 数据，原始媒体保留。

同一处的「自动更新」可按每 6 小时、每天或每周检查新版本，默认关闭。独立测试包可自动下载，下载完成后确认重启安装；源码运行支持自动检查。

FFmpeg 与 ffprobe 需另装；缺少它们时可浏览和播放浏览器兼容格式，转码、探测与缩略图不可用。
测试包未签名；下载校验、配置与问题反馈见 [Windows 测试版](docs/TESTING_DESKTOP.md)。

### 源码运行

需要 Git、[uv](https://docs.astral.sh/uv/getting-started/installation/) **0.12.13** 和 **Python 3.12 或更高**。下面示例使用 3.14，uv 可自动下载缺失的 Python；CI 覆盖 3.12 与 3.14。
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
首次设置的访问密码为可选项：留空时，能连接到 Peach 的设备可直接访问。配置页可设置、修改或关闭密码，安全设置可调整保持登录时间。已有部署保留当前登录要求。本机 CA 生成需要 OpenSSL。
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
| 查看每个版本的变化 | [变更日志](CHANGELOG.md) |
| 查看开放需求 | [产品待办](docs/PRODUCT_BACKLOG.md) |
| 修改与维护项目 | [工作契约](AGENTS.md) · [前端开发](docs/FRONTEND.md) · [复用清单](docs/REUSE.md) |
| 了解长期约定与架构 | [交接说明](docs/HANDOFF.md) · [架构决策](docs/adr/) |

README 描述当前主线能力；已安装版本与验证结果以项目状态为准，发行制品以 Releases 为准。
文档迭代方式见 [README 维护](docs/README_MAINTENANCE.md)。

## 许可证

[AGPL-3.0-or-later](LICENSE) · Copyright (C) 2026 longmeidao。

固定的第三方前端文件保留上游许可证与来源记录，见 [web/vendor](web/vendor/)。
FFmpeg 不随仓库或制品分发，使用者需自行安装并遵守其许可证。
