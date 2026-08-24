# Peach

Peach（蜜桃）是一个单用户、本地优先的个人媒体系统：统一索引本地/网盘/在线资产，记录真实消费反馈，并逐步提供搜索、推荐和追更。

当前界面以作品、女优、厂牌、创作者和系列实体为导航：名字进入带简介、别名和渠道链接的资料页，内容标签才直接叠加筛选：首页默认排除竖屏视频，竖屏入口保留全量竖屏集合并可直接进入指定视频的沉浸模式。「稍后看」和「喜欢/为什么喜欢」使用独立 profile 数据，不和「看过/不喜欢」混用；用户原始偏好说明是本机真相，AI 以后只能提出可审核的归一化候选。

顶栏齿轮打开设置：「换一批」决定排序多久换一次，默认**每次刷新**，另有 5/10/30 分钟、每天和「从不（只手动）」。选分钟数的含义是**后台每 N 分钟换一次排序、下次刷新时体现**——页面不会在你看着的时候自己重排。首页网格和顶部三层（艺人头像/厂牌/标签）共用同一个种子，所以整屏一起换。还可调整每批作品数、默认排序、悬停放大延时、快进/快退秒数、搜索记录条数和相关推荐数量。体验设置保存在当前浏览器，搜索历史写入 ledger 并在访问端之间同步。视频环境光是播放器的默认视觉效果，不再暴露成技术开关。详情页的闪光图标用于标记「寻找高清、无水印或完整版」，该状态写入 ledger，但不会删除当前文件。

## 边界

双机本机化已完成：Windows 和 macOS 各自在内置盘持有一份可独立运行的代码、数据、虚拟环境和
worktree，外置盘只提供媒体资源。账本里的媒体路径始终使用 Windows 口径，本机挂载点由
`src/peach/platform.py` 在读取时翻译。完整取舍与迁移门槛见
[`ADR-0017`](docs/adr/0017-dual-host-local-runtime-and-sync-boundaries.md)。

| 角色 | Windows 当前 | macOS 当前 |
|---|---|---|
| 项目代码 | `C:\Users\longm\Desktop\peach\peach-app` | `~/Desktop/lmd.gg/peach/peach-app` |
| 运行数据 | `C:\Users\longm\Desktop\peach\peach-data` | `~/Desktop/lmd.gg/peach/peach-data` |
| 并行 worktree | `C:\Users\longm\Desktop\peach\peach-worktrees` | `~/Desktop/lmd.gg/peach/peach-worktrees` |
| 本地媒体 | `R:\media` | `/Volumes/RESOURCES/media` |
| 115（账本写 `B:\`） | `B:\` | `~/Desktop/IMSL/115` |
| PikPak（账本写 `A:\`） | `A:\` | `~/Desktop/IMSL/Pikpak` |

- 真相数据库：`peach-data/database/ledger.db`
- Stash：过渡期可替换 adapter，不是真相源

两台机器各持一份本地账本工作副本；专用共享副本只承担单写者同步传输，不再放在外置资源盘。
GitHub 不保存或同步账本。详见下文「账本复制」。

盘符映射的默认值按平台给，可用 `PEACH_DRIVE_MAP=R=/Volumes/RESOURCES,B=/mnt/115` 覆盖；
数据目录用 `PEACH_DATA_ROOT` 覆盖。CloudDrive 在两个平台的挂载方式完全不同——Windows
是盘符，macOS 是 macFUSE 挂载点——所以这层映射是必需的，不是可选优化。

写回账本的索引脚本仍然只在 Windows 上运行，账本因此保持单一路径口径；macOS 侧只读不写
`asset.path`。

项目仓库不保存媒体、数据库、凭据、快照、封面或运行日志，也不保存 `.venv`、构建产物和
worktree 目录。跨机器继续任务时 push 分支，在另一台按分支重建 worktree。

### macOS 的 mDNS 必须交给系统的 mDNSResponder

`peach serve` 从终端起时 `peach.local` 一切正常，改由 LaunchAgent 起之后就再也没人应答
——同一个二进制、同一台机器、同样的参数。原因是「本地网络」隐私门按进程判：终端起的进程
继承终端已获授权的身份，launchd 起的作业是另一个主体，而且**没有弹窗可点**，自己发的多播
被静默丢弃。zeroconf 自认为注册成功，`/healthz` 也照报 `peach.local`，实际一个包都发不出去。
在系统设置里给 Python 放行也没用——那个条目对应的不是这个主体。

所以 macOS 改用 `dns-sd -P` 请系统那个本来就在跑、本来就有权限的 mDNSResponder 代发
（`DnsSdPublisher`）；Windows 继续用进程内的 zeroconf。一台机器本来也不该跑两套 mDNS 响应器。

**可达性不能由服务进程自证**：它发不出多播，探自己必然收不到回应，会把好的判成不可达。
运行时只报「注册还在生效」，真要验用 `scripts/check_mdns.py`——那个从终端跑，有权限。

双机固定使用两个名字：macOS 使用 `peach.local`，Windows 使用 `peach-win.local`；两个默认值已收敛在
`src/peach/config.py`，`PEACH_MDNS_NAME` 只用于临时测试覆盖。
服务本身可以同时跑，但 `ledger.db.sync.json` 的 `device` 只指定一台写入端；另一台的写入
端点返回 `409`，只能浏览。切换写入端必须使用托盘的「接管 Ledger 写入」。

### 账本复制

目标仍是三份副本：Windows 和 macOS 各持一份本地工作副本，Windows 内置盘上的专用 SMB
同步目录持有共享副本。共享副本只是同步传输点，不是 Peach 直接运行的数据库。**这不是多主
实时同步**——SQLite 没有安全的自动三方合并，两台机器各自写过之后，
没有任何规则能把「看过 / 喜欢 / 标签」这类断言合成一份而不丢东西。实际做的是单写者复制：

- 服务启动只观察世代与写入端，绝不自动 pull/push，也没有定时同步线程。
- `ledger.db.sync.json` 的 `device` 是唯一写入端；非写入端的写入请求返回 `409`。
- 「同步 Ledger」是唯一复制入口；「接管 Ledger 写入」只有在本地/共享完全一致时才切换写入端。
- **两边都动过就拒绝自动合并**，由人选一边。
- 共享目录不可达时本地照常运行，恢复连接后再同步；媒体外置盘是否插入与账本同步无关。
- macOS 菜单栏和 Windows 托盘都有「同步 Ledger」：它只停止当前托盘拥有的 HTTP/HTTPS，
  完成一次安全推送或拉取后再恢复服务；发现端口由别的进程占用时拒绝接管。

世代号只表示血缘先后，不表示时间：时钟在两台机器上不可靠。
血缘记在库文件旁边的 `ledger.db.sync.json` 里，不进 Git，也不需要改表结构。

复制一律走 SQLite 的 backup API，不复制文件：账本是 WAL 模式，直接拷 `.db` 会漏掉 `-wal`
里已提交但未 checkpoint 的事务，拷完还可能和目标残留的 `-wal` 拼成一个已经损坏的库。

共享副本位置由 `PEACH_SHARED_DATA_ROOT` 覆盖；Windows 默认为
`C:\Users\longm\Desktop\peach\peach-sync`，macOS 默认为 `/Volumes/peach-sync`。当前同步状态看
`/healthz` 的 `ledger_sync` 字段（`writer` / `reader` / `conflict`），也可用托盘菜单手动同步；这仍是冲突即只读的单写者复制，
不是 SQLite 多主。

浏览服务始终使用 `--no-ledger-sync`；该参数只禁止复制，不绕过 marker 写入端闸门。

冲突的解法是选一边，不是合并：把要保留的那份复制成另一份，或删掉一侧的 `.sync.json` 让它
重新播种。复制必须经过 SQLite backup API。

### 脱盘模式

脱盘是**来源级**的，不是全局开关：外置盘拔掉只影响 `local` 的 2.5k 条资产，115/PikPak
的 78k 条云端资产照常可播；CloudDrive 掉线时反过来也一样。

`GET /api/sources` 无副作用地报告每个来源的可达性，判据是「能否列出挂载点的第一个条目」——
目录存在还不够，CloudDrive 掉线后挂载点目录仍在，读一个条目才会报 `Device not configured`。
前端据此把脱盘来源的筛选置灰（数量仍然显示：脱的是盘不是账本），详情页换成「脱盘模式」
面板而不是挂一个必然失败的播放器。媒体层对应抛 `MediaOffline`，HTTP 侧回 503 加
`X-Peach-Offline: 1`，和「单个文件缺失」的 404 分开。

每台机器的 `peach-data` 使用固定分层：`database` 保存真相库，`generated` 保存派生资产，
`sources` 保存原始分析输入，`state` 保存人工维护状态，`secrets` 保存本机凭据材料，`logs` 保存
运行记录，`archive` 保存历史备份，`inbox` 是临时下载落地区，`tools` 保存本机运行时工具。
这个目录不整体同步；跨机器需要的 durable artifacts 要先从缓存与本机状态中拆出来，再做选择性
文件同步。

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
cd C:\Users\longm\Desktop\peach\peach-app
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

菜单中的「同步 Ledger」会先安全停止本菜单栏项创建的服务，再同步和恢复，不需要退出应用。

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

它同时转 80 → 8900 和 443 → 8443；HTTPS 用的还是 `peach-data/secrets/tls` 里那套本机 CA。

服务器证书的 SAN 必须覆盖实际会被访问到的每个名字。原来只有
`DNS:peach.local, IP:192.168.50.162`——那个 IP 是 Windows 那台的，于是本机用
`https://127.0.0.1:8443` 做健康检查会主机名不匹配，手机也只能用名字、不能用局域网 IP。
`scripts/setup_local_tls.sh` **用现有 CA 重签叶子证书**并补上
`DNS:localhost, IP:127.0.0.1, IP:<本机局域网地址>`；CA 不动，所以 Mac 钥匙串和 iPhone 上
已经装过的信任继续有效，不用重装。

**有效期必须 ≤ 398 天**（脚本用 397，和 `setup_local_tls.ps1` 一致）。Apple 从 2020-09
起拒绝有效期更长的 TLS 服务器证书，iOS 上即使根证书已被完全信任也照样报「不受信任」，
而且报错信息完全看不出是有效期的问题。CA 本身不受这条限制。

SAN 里的局域网 IP 会随 DHCP 变化失效，**但不需要人去管，也不靠轮询**：菜单栏项订阅系统的
`com.apple.system.config.network_change` Darwin 通知（`src/peach/netwatch.py`，走
`notify_register_file_descriptor`，阻塞在一个 fd 上，没有定时器）。换 Wi-Fi、DHCP 换地址、
插拔网线的那一刻就触发，随即比对证书：没覆盖当前地址（或还有 30 天到期）就用同一个 CA
重签叶子证书，只重启 HTTPS 那个服务（`src/peach/certs.py`）。CA 全程不动，设备上的信任
不受影响。手动重签仍然可以：`sh scripts/setup_local_tls.sh`。

健康检查走回环而不是 `peach.local`：后者会先解析到局域网 IP，那条路径要穿过 pf 的转发
规则，连接慢到几秒甚至超时，于是服务在跑却被判成「未运行」。

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

### 两台机器怎么保持一致

- **代码**走私有 GitHub 仓库 `longmeidao/peach-app`（`origin`）。阶段性任务完成、测试全绿且无报错
  时直接推送；测试有失败，或改动涉及真实 ledger 写入、不可逆删除、生产入口、凭据时先确认。
  开工前跑一条命令看两边差了多少，别在旧代码上接着写：

  ```bash
  sh scripts/sync_status.sh      # 落后/领先几个提交、工作区脏不脏、账本同步状态
  ```

- **账本**走 `peach.sync` 的单写者复制（见上文「账本复制」），和代码是两条独立链路，
  `sync_status.sh` 会一并报告。
- **worktree** 不复制目录。需要在另一台继续的分支先 push，再由另一台从该分支重建 worktree。
- **运行数据** 不整体进入 GitHub或通用同步。账本只走 `peach.sync`；凭据、日志、锁、工具、临时
  文件和可重建缓存留在本机；图片资产、原始证据和复核产物完成目录拆分后再选择性同步。

跨两台机器开发时换行口径由 `.gitattributes` 的 `* text=auto eol=lf` 固定。不要依赖各自的
`core.autocrlf`：2026-08 之前 Windows 侧把 105 个文件整体改写成 CRLF，`git status` 长期显示
117 个文件被修改、16000 行增删，而真正有实质改动的只有 1 个。

`serve` 默认只监听 `127.0.0.1:8900`。公网、反代、HTTPS 和认证属于后续部署阶段，不在开发命令中隐式开启。

Windows 日常运行使用登录后托盘，而不是保留命令行窗口或注册系统服务。托盘在启动时声明
Per-Monitor V2 DPI，单击打开 `https://peach-win.local/`；右键可同步 Ledger、查看状态、重启服务、打开日志、
查看版本/更新通道和退出。同步与更新检查都在后台运行并使用非模态系统通知；退出只结束
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

需要本机 TLS 时同时提供证书和私钥；二者应放在本机 `peach-data\secrets`，不要提交 Git：

```powershell
& .\.venv\Scripts\peach.exe serve --host 0.0.0.0 --port 443 `
  --mdns-address 192.168.50.162 `
  --ssl-certfile C:\Users\longm\Desktop\peach\peach-data\secrets\tls\peach.crt `
  --ssl-keyfile C:\Users\longm\Desktop\peach\peach-data\secrets\tls\peach.key
```

证书必须包含实际访问名（Windows 为 `peach-win.local`）并被客户端信任；启用 TLS 时 mDNS 自动发布 HTTPS。

本机局域网不使用 Let's Encrypt。项目提供可重复执行的本地 CA + 服务器证书生成脚本；默认只写
`C:\Users\longm\Desktop\peach\peach-data\secrets\tls`，`-TrustCurrentUser` 只把 CA 加入当前 Windows 用户的信任库：

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
| `/login` | 口令登录；通过 POST 设置 HttpOnly cookie，不把口令放进 URL |
| `/` | 首页 |
| `/item/{id}` | 作品详情 |
| `/performers` | 全部女优 |
| `/performers/{name}` | 女优资料页 |
| `/creators` | 全部创作者 |
| `/creators/{name}` | 创作者资料页；有图片时带「照片」标签，`?media=photos&set={图集 id}` 可直接分享到某个图集 |
| `/studios/{name}` | 厂牌资料页 |
| `/series/{name}` | 系列资料页 |
| `/tags` | 标签管理，支持字母表与标签云 |
| `/stats` | 统计 |
| `/immerse` | 沉浸模式 |
| `/quality-goals` | 已标记寻找高清、无水印或完整版的作品 |
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
| `/photo?id={asset_id}` | 图片原图，灯箱看大图用 |
| `/photo-thumb?id={asset_id}` | 图片缩略图，服务端缓存一次，瀑布流只读这条 |

配置了 `--token` 时，直接打开页面会跳到 `/login`。旧 `?t=` 入口只保留兼容，会立即设置
cookie 并重定向到不含口令的干净 URL；新设备不要再复制带口令的链接。

只读 API：`GET /api/items`、`/api/item`、`/api/entity`、`/api/photos`、`/api/photo-set`、
`/api/index`、`/api/stats`、
`/api/tops`、`/api/ads`、`/api/related`、`/api/facets`、`/api/providers`、`/api/sources`、
`/api/providers/opencode-go/models`、`/api/search-history`。图集按目录聚合：`/api/photos`
给某个实体名下的图集列表，`/api/photo-set` 给一个图集里的图片，两者都只发图集 id 和目录名，
不发真实路径。

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

`scripts/scrape_codes.py` 只把规范化番号交给固定版本 Javinizer-Go，逐来源保存原始 JSON，并为演员、厂牌、系列、发行日期和内容标签生成字段候选；官方/官方镜像标签来源优先。它没有整批 `--apply`，只有 `/review` 中明确选中某个来源值并批准才写 ledger。`scripts/clean_names.py` 默认只生成改名计划；`--apply` 会先备份 SQLite，并在数据库更新失败时把文件名回滚。两者导入模块时均无副作用，测试不得使用真实路径。

来源策略必须显式选择，默认行为保持 `baseline=r18dev`；`--sources` 是兼容入口，不能和 `--profile` 同时使用。`fc2` profile 只处理 FC2，其他 profile 默认排除 FC2。每批都会生成 source health CSV：

```powershell
# 默认 baseline；候选、错误和健康报告都写到显式复核目录
& .\.venv\Scripts\python.exe scripts\scrape_codes.py --db .\review\ledger.db --out .\review\metadata-field-candidates.csv --health .\review\metadata-source-health.csv

# 显式选择类别；不会自动批准或写回 ledger
& .\.venv\Scripts\python.exe scripts\scrape_codes.py --db .\review\ledger.db --profile censored --out .\review\censored-candidates.csv
& .\.venv\Scripts\python.exe scripts\scrape_codes.py --db .\review\ledger.db --profile uncensored --out .\review\uncensored-candidates.csv
& .\.venv\Scripts\python.exe scripts\scrape_codes.py --db .\review\ledger.db --profile fc2 --out .\review\fc2-candidates.csv
```

历史创作者投影使用逐项只读审计，不再把目录名直接当身份：

```powershell
& .\.venv\Scripts\python.exe scripts\audit_creator_attributions.py `
  --output C:\Users\longm\Desktop\peach\peach-data\review\creator-attribution-items.csv `
  --summary C:\Users\longm\Desktop\peach\peach-data\review\creator-attribution-summary.csv
```

自动纠正必须有水印、番号、发行元数据或用户确认；只有目录同名的记录继续留在复核队列。

`/api/providers` 是无副作用 capability health；`/api/providers/opencode-go/models` 只在显式访问时拉取 OpenCode Go 的公开模型清单，不发送推理请求或读取本机 CLI 凭据。

在线追更从 `FeedAdapter` 的 RSS/Atom 候选发现开始：只有显式调用才联网，支持条件请求和有界读取，当前不会自动写 ledger。
