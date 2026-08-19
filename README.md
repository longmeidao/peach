# Peach

Peach（蜜桃）是一个单用户、本地优先的个人媒体系统：统一索引本地/网盘/在线资产，记录真实消费反馈，并逐步提供搜索、推荐和追更。

当前界面以作品、女优、厂牌、创作者和系列实体为导航：名字进入带简介、别名和渠道链接的资料页，内容标签才直接叠加筛选：首页默认排除竖屏视频，竖屏入口保留全量竖屏集合并可直接进入指定视频的沉浸模式。「稍后看」和「喜欢/为什么喜欢」使用独立 profile 数据，不和「看过/不喜欢」混用；用户原始偏好说明是本机真相，AI 以后只能提出可审核的归一化候选。

顶栏齿轮打开设置：自动换一批默认每 5 分钟执行一次，只在首页空闲态生效；还可调整每批作品数、默认排序、悬停放大延时、快进/快退秒数、搜索记录条数和相关推荐数量。体验设置保存在当前浏览器，搜索历史写入 ledger 并在访问端之间同步。视频环境光是播放器的默认视觉效果，不再暴露成技术开关。详情页的闪光图标用于标记「寻找高清、无水印或完整版」，该状态写入 ledger，但不会删除当前文件。

## 边界

Peach 在 Windows 和 macOS 两台机器上各有一份可独立运行的环境，账本里的路径始终使用
Windows 口径，本机挂载点由 `src/peach/platform.py` 在读取时翻译。

| 角色 | Windows | macOS |
|---|---|---|
| 项目代码 | `R:\peach-app` | `~/Desktop/lmd.gg/peach/peach-app` |
| 运行数据 | `R:\peach-data` | `~/Desktop/lmd.gg/peach/peach-data` |
| 并行 worktree | `R:\peach-worktrees` | `~/Desktop/lmd.gg/peach/peach-worktrees` |
| 本地媒体 | `R:\media` | `/Volumes/RESOURCES/media` |
| 115（账本写 `B:\`） | `B:\` | `~/Desktop/IMSL/115` |
| PikPak（账本写 `A:\`） | `A:\` | `~/Desktop/IMSL/Pikpak` |

- 真相数据库：`peach-data/database/ledger.db`
- Stash：过渡期可替换 adapter，不是真相源

账本共三份：硬盘上那份是权威副本，两台机器各持一份本地工作副本。详见下文「账本复制」。

盘符映射的默认值按平台给，可用 `PEACH_DRIVE_MAP=R=/Volumes/RESOURCES,B=/mnt/115` 覆盖；
数据目录用 `PEACH_DATA_ROOT` 覆盖。CloudDrive 在两个平台的挂载方式完全不同——Windows
是盘符，macOS 是 macFUSE 挂载点——所以这层映射是必需的，不是可选优化。

写回账本的索引脚本仍然只在 Windows 上运行，账本因此保持单一路径口径；macOS 侧只读不写
`asset.path`。

项目仓库不保存媒体、数据库、凭据、快照、封面或运行日志。

### 账本复制

三份副本：硬盘 `\<共享\>/database/ledger.db` 是权威副本，Windows 和 macOS 各持一份本地
工作副本。**这不是多主实时同步**——SQLite 没有安全的自动三方合并，两台机器各自写过之后，
没有任何规则能把「看过 / 喜欢 / 标签」这类断言合成一份而不丢东西。实际做的是单写者复制：

- 启动时比对世代：硬盘更新就拉取，本地更新就保留；**两边都动过就拒绝自动合并**，服务照常
  起但转只读（写入端点返回 `409`），由人选一边。
- 运行中每 60 秒回写硬盘，所以同一时刻只有一台在写。回写前重新判定，别人抢先推过就转冲突，
  绝不覆盖。
- 硬盘不在时本地照常读写，插回来再回写。这就是脱盘模式的账本侧。

世代号只表示血缘先后，不表示时间：时钟在两台机器上不可靠，exFAT 的本地时间戳只有 2 秒精度。
血缘记在库文件旁边的 `ledger.db.sync.json` 里，不进 Git，也不需要改表结构。

复制一律走 SQLite 的 backup API，不复制文件：账本是 WAL 模式，直接拷 `.db` 会漏掉 `-wal`
里已提交但未 checkpoint 的事务，拷完还可能和目标残留的 `-wal` 拼成一个已经损坏的库。

共享副本位置由 `PEACH_SHARED_DATA_ROOT` 覆盖。**本地副本和共享副本是同一条路径时复制自动停用**，
所以尚未把数据迁到本机盘的机器行为完全不变。当前状态看 `/healthz` 的 `ledger_sync` 字段。

```bash
# 不参与复制（例如临时起一个只读实例）
./.venv/bin/peach serve --port 8900 --no-ledger-sync
```

冲突的解法是选一边，不是合并：把要保留的那份复制成另一份，或删掉一侧的 `.sync.json` 让它
重新播种。历史备份仍然只留在硬盘的 `database/` 与 `archive/`。

### 脱盘模式

脱盘是**来源级**的，不是全局开关：外置盘拔掉只影响 `local` 的 2.5k 条资产，115/PikPak
的 78k 条云端资产照常可播；CloudDrive 掉线时反过来也一样。

`GET /api/sources` 无副作用地报告每个来源的可达性，判据是「能否列出挂载点的第一个条目」——
目录存在还不够，CloudDrive 掉线后挂载点目录仍在，读一个条目才会报 `Device not configured`。
前端据此把脱盘来源的筛选置灰（数量仍然显示：脱的是盘不是账本），详情页换成「脱盘模式」
面板而不是挂一个必然失败的播放器。媒体层对应抛 `MediaOffline`，HTTP 侧回 503 加
`X-Peach-Offline: 1`，和「单个文件缺失」的 404 分开。

`R:\peach-data` 使用固定分层：`database` 保存真相库，`generated` 保存可再生成的视觉资产，`sources` 保存原始分析输入，`state` 保存人工维护状态，`secrets` 保存本机凭据材料，`logs` 保存运行记录，`archive` 保存历史备份，`inbox` 是临时下载落地区，`tools` 保存不进入 Git 的本机运行时工具。

详情播放器固定使用本地自托管 Video.js 8.23.9：本地 MP4/WebM/Ogg 走标准 HTTP Range；115/PikPak 的已知时长原生 MP4 通过 `stream-plan` 改走 6 秒 HLS 临时片段，跳转时只生成目标时间附近的片段。两者都显示账本中的稳定总时长、±10 秒控制和播放统计；AVI 等不兼容容器首次播放时由 Peach 管理的 FFmpeg 生成 `generated/transcodes` 下的 H.264/AAC MP4 缓存。缓存可删除重建，原媒体永不改写。

## 结构

```text
peach-app/
├─ src/peach/        FastAPI、Media Engine、迁移和 Provider 边界
├─ web/index.html    当前无构建步骤的前端
├─ migrations/       有版本和校验和的 SQLite 迁移
├─ scripts/          仍在使用的运维/索引命令
├─ tests/            全隔离测试
├─ docs/             架构、状态、交接和 ADR
├─ AGENTS.md         Codex/Claude 共用工作契约
└─ CLAUDE.md         Claude 自动导入 AGENTS.md
```

## 开发

Windows：

```powershell
cd R:\peach-app
& py -3.14 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -e .
& .\scripts\test.ps1
& .\.venv\Scripts\peach.exe migrate status
& .\.venv\Scripts\peach.exe serve --port 8900
```

macOS：

```bash
cd ~/Desktop/lmd.gg/peach/peach-app
python3.14 -m venv .venv
./.venv/bin/python -m pip install -e .
./scripts/test.sh
./.venv/bin/peach migrate status
./.venv/bin/peach serve --port 8900
```

macOS 侧的 FFmpeg 走 PATH（`brew install ffmpeg`）：`peach-data/tools/ffmpeg` 里是
Windows 的 `.exe` 和 `.dll`，`FFmpegResolver` 按平台找不带后缀的 `ffmpeg` 因而自动跳过它。

主目录和独立 worktree 统一只使用同一个测试入口——Windows 是 `scripts/test.ps1`，
macOS/Linux 是 `scripts/test.sh`，两者契约相同：从 Git common directory 定位主目录的
`.venv`，强制加载当前 worktree 的 `src` 并核对 `peach.__file__`，因此 worktree 不需要
也不应复制 `.venv`。仓库不使用 pytest。

macOS 日常运行走菜单栏项，而不是留一个终端窗口：

```bash
./.venv/bin/python scripts/make_macos_icon.py        # 圆角 .icns，只需一次
./.venv/bin/python scripts/install_macos_agent.py install
```

**菜单栏项没有跨平台的轮子。** pystray 名义上支持 darwin，但它的后端漏了三件事：
`setActivationPolicy_(Accessory)`、`NSImage.setSize_(18,18)`（菜单栏按 18pt 画，直接塞
64px 位图会被裁掉）和 `setTemplate_`（不设就不会跟着浅色/深色菜单栏反色）。补齐等于
把它那层薄封装重写一遍，所以 macOS 直接用 AppKit（`src/peach/menubar.py`），Windows
继续用 pystray。判据不靠猜：`item.button().window().frame()` 能直接读出状态项落在屏幕
的哪个位置。

**不能用 .app 外壳直接跑它。** macOS 26 上主可执行文件是 exec 跳板（shell 脚本、C
launcher 都算）时状态项注册不上：进程活着、`NSStatusItem` 也建出来了，但按钮窗口永远
是 `(0,0,34,0)`——高度 0、从来没被布局。Apple 受理为 FB21015611，没有绕过办法。同一份
代码由 launchd 直接拉起时实测 `(858, 949, 34, 33)`，正常落在菜单栏内。所以自启走
LaunchAgent；`dist/Peach.app` 只作双击入口，它做的事只是 `launchctl kickstart`。

服务起在非特权的 `8900`：80/443 在 macOS 上要 root，而本机 CA 的 TLS 材料是给 Windows
生产实例签的。想让 `http://peach.local/` 不带端口也能开，把 80 交给内核转发，而不是让
整个服务提权：

```bash
sh scripts/setup_macos_port80.sh check          # 先验证，不需要 root
sudo sh scripts/setup_macos_port80.sh install
```

它同时转 80 → 8900 和 443 → 8443；HTTPS 用的还是 `peach-data/secrets/tls` 里那套本机
CA 证书（`CN=peach.local`，有效期到 2027-09）。

两个 pf 上踩过的坑：

- **`rdr-anchor` 必须落在 translation 段。** pf 要求规则严格按 options → normalization
  → queueing → translation → filtering 排列，追加到 `/etc/pf.conf` 末尾会落在
  `anchor "com.apple/*"`（filtering）之后并报 `Rules must be in order`。脚本因此插在
  最后一条 `rdr-anchor`/`nat-anchor` 之后，并且**先在临时文件上 `pfctl -n -f` 验证过
  才动系统文件**——`/etc/pf.conf` 写坏了，开机时整个包过滤都加载不起来。
- **转发目标必须是网卡地址，不能是 `127.0.0.1`。** 转到回环地址时，外部设备（手机）的回包
  源地址是回环地址、路由不回去，连不上；本机直连高位端口也会被 lo0 上残留的 rdr 状态反向
  翻译回 `:80`，TCP 连得上但 HTTP 永远收不到响应。脚本写成 `(en0)` 让 pf 动态取网卡当前
  地址，换网络或换 DHCP 地址都不用重装；服务监听的是 `0.0.0.0`，收得到。
- **高位端口另外用 `no rdr` 排除一次。** translation 规则是第一条命中就生效（和 filter 的
  最后一条命中相反），所以例外必须写在转发规则前面。

跨两台机器开发时换行口径由 `.gitattributes` 的 `* text=auto eol=lf` 固定。不要依赖各自的
`core.autocrlf`：2026-08 之前 Windows 侧把 105 个文件整体改写成 CRLF，`git status` 长期显示
117 个文件被修改、16000 行增删，而真正有实质改动的只有 1 个。

`serve` 默认只监听 `127.0.0.1:8900`。公网、反代、HTTPS 和认证属于后续部署阶段，不在开发命令中隐式开启。

Windows 日常运行使用登录后托盘，而不是保留命令行窗口或注册系统服务。托盘在启动时声明
Per-Monitor V2 DPI，单击打开 `https://peach.local/`；右键可查看状态、重启服务、打开日志、
查看版本/更新通道和退出。更新检查在后台运行并使用非模态系统通知；退出只结束
托盘自己启动的 Peach 进程：

```powershell
& .\scripts\manage_tray_startup.ps1 -Action Install
& .\.venv\Scripts\pythonw.exe -m peach.tray
```

检查或移除当前用户自启动：

```powershell
& .\scripts\manage_tray_startup.ps1 -Action Status
& .\scripts\manage_tray_startup.ps1 -Action Uninstall
```

托盘默认固定发布 `192.168.50.162`，避免虚拟网卡误选；地址变化时为启动进程设置
`PEACH_LAN_ADDRESS`。它同时启动 HTTP `:80` 和本地 CA HTTPS `:443`，因此安装前必须先按
下文生成 TLS 材料。

版本唯一来源是 `src/peach/__init__.py` 的 `__version__`，构建元数据由 setuptools 动态读取。
托盘同时显示包版本、分支、提交、工作树状态和更新通道；没有 `origin` 时只报告本地开发版。
即使发现远端提交也不会自动覆盖并行工作树。

需要本机 TLS 时同时提供证书和私钥；二者应放在 `R:\peach-data\secrets`，不要提交 Git：

```powershell
& .\.venv\Scripts\peach.exe serve --host 0.0.0.0 --port 443 `
  --mdns-address 192.168.50.162 `
  --ssl-certfile R:\peach-data\secrets\tls\peach.crt `
  --ssl-keyfile R:\peach-data\secrets\tls\peach.key
```

证书必须包含实际访问名（例如 `peach.local`）并被客户端信任；启用 TLS 时 mDNS 自动发布 HTTPS。

本机局域网不使用 Let's Encrypt。项目提供可重复执行的本地 CA + 服务器证书生成脚本；默认只写
`R:\peach-data\secrets\tls`，`-TrustCurrentUser` 只把 CA 加入当前 Windows 用户的信任库：

```powershell
& .\scripts\setup_local_tls.ps1 -Address 192.168.50.162 -TrustCurrentUser
```

每台访问设备都必须单独信任 `peach-local-ca.crt`，只需安装一次，证书续签仍可沿用同一 CA：

- macOS：把 CA 拖入「钥匙串访问」的「登录」或「系统」钥匙串，双击后在「信任」中将 SSL
  设为始终信任。Apple 官方步骤：<https://support.apple.com/guide/keychain-access/kyca11871/mac>。
- iPhone/iPad：先安装 CA 描述文件，再进入「设置 → 通用 → 关于本机 → 证书信任设置」，
  为该根证书开启完全信任。Apple 官方步骤：<https://support.apple.com/en-us/102390>。
- 只传 `peach-local-ca.crt`。绝不传 `peach-local-ca.key`、`peach.key` 或整个 `tls` 目录。

如果不愿在设备上安装本地 CA，继续使用 `http://peach.local`。浏览器无法在不信任 CA 的
前提下把自签 HTTPS 变成无警告连接；Let's Encrypt 也不会签发 `.local`。

当前运行态与下一任务只看 [`docs/STATUS.md`](docs/STATUS.md)；跨 Codex/Claude 的固定接手方式只看 [`docs/HANDOFF.md`](docs/HANDOFF.md)。

## URL 路由

浏览器页面：

| URL | 用途 |
|---|---|
| `/` | 首页 |
| `/item/{id}` | 作品详情 |
| `/performers` | 全部女优 |
| `/performers/{name}` | 女优资料页 |
| `/creators` | 全部创作者 |
| `/creators/{name}` | 创作者资料页 |
| `/studios/{name}` | 厂牌资料页 |
| `/series/{name}` | 系列资料页 |
| `/tags` | 标签管理，支持字母表与标签云 |
| `/stats` | 统计 |
| `/immerse` | 沉浸模式 |
| `/trash` | 回收站 |
| `/mix/{seed_id}/{item_id}` | 自动 Mix 播放器与右侧队列 |

公共状态和媒体：

| URL | 用途 |
|---|---|
| `/healthz` | 无副作用健康状态，含 `ledger_sync` |
| `/api/sources` | 各来源挂载可达性，脱盘模式的唯一判据 |
| `/api/stream-plan?id={asset_id}` | 为远端原生 MP4 选择 HLS 或标准 Range |
| `/favicon.svg` | Peach 图标 |
| `/stream?id={asset_id}` | 原片或兼容转码的 Range 流 |
| `/stream/hls/{asset_id}/index.m3u8` | 远端按时间定位的 HLS VOD 清单 |
| `/thumb?id={asset_id}` | 缩略图 |
| `/poster?id={asset_id}&c={0..8}` | 海报/接触表格子 |
| `/avatar?id={asset_id}` | 作品代表头像 |
| `/logo?studio={name}` | 厂牌 Logo |
| `/entity-image?kind={kind}&id={entity_id}` | 规范实体头像/Logo |

只读 API：`GET /api/items`、`/api/item`、`/api/entity`、`/api/index`、`/api/stats`、
`/api/tops`、`/api/ads`、`/api/related`、`/api/facets`、`/api/providers`、`/api/sources`、
`/api/providers/opencode-go/models`、`/api/search-history`。

写入 API：`POST /api/activity`、`/api/play`、`/api/feedback`、`/api/watch-later`、
`/api/preference`、`/api/item-tag`、`/api/batch`、`/api/trash/empty`。标签隐藏只写本地 profile 覆盖，不销毁
原始来源断言；搜索历史通过 `POST /api/search-history` 共享写入账本；媒体先进入回收站，只有显式清空回收站才永久删除。除上述明确端点外，`/api/*` 返回 404。公共页面不再使用
`/entity/{kind}/{name}`；内部 JSON 的 `/api/entity` 只是兼容契约，不暴露数据库路由结构。

并行代码任务不共享编辑目录。由协调者在主目录创建独立 worktree：

```powershell
& .\.venv\Scripts\python.exe scripts\agent_worktree.py create --agent claude --task metadata-batch
```

工作者在返回目录提交后运行 `ready`；协调者审核并运行 `integrate`。脚本会拒绝脏工作树、无提交分支和双方都修改过同一文件的自动合并。禁止 `git add .` / `git add -A`，只暂存任务明确拥有的文件。
准备新增、恢复或替换实现前，必须查 [`docs/REUSE.md`](docs/REUSE.md)，避免按旧文件名重复造轮子。

## 批处理安全边界

`scripts/scrape_codes.py` 默认只把番号发送到已声明的元数据源并写复核 CSV；只有 `--apply` 才写 ledger。`scripts/clean_names.py` 默认只生成改名计划；`--apply` 会先备份 SQLite，并在数据库更新失败时把文件名回滚。两者导入模块时均无副作用，测试不得使用真实路径。

历史创作者投影使用逐项只读审计，不再把目录名直接当身份：

```powershell
& .\.venv\Scripts\python.exe scripts\audit_creator_attributions.py `
  --output R:\peach-data\review\creator-attribution-items.csv `
  --summary R:\peach-data\review\creator-attribution-summary.csv
```

自动纠正必须有水印、番号、发行元数据或用户确认；只有目录同名的记录继续留在复核队列。

`/api/providers` 是无副作用 capability health；`/api/providers/opencode-go/models` 只在显式访问时拉取 OpenCode Go 的公开模型清单，不发送推理请求或读取本机 CLI 凭据。

在线追更从 `FeedAdapter` 的 RSS/Atom 候选发现开始：只有显式调用才联网，支持条件请求和有界读取，当前不会自动写 ledger。
