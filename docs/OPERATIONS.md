# 运行、部署与数据安全的操作细节

本文件是 `docs/HANDOFF.md` 里「运行与部署」「数据安全」两条边界的展开。判据仍然写在 HANDOFF，
这里只放执行时要照着做的细节：命令、顺序、失败表现和踩过的坑。改动运行入口、同步通道、证书或
删除边界之前先读对应小节；当前运行态的端口、版本与迁移号在 `docs/STATUS.md`。

## 首次运行与设置文件

- 配置完成之后，Windows 和有 TLS 的 macOS 托盘由 HTTP 导航进程与 HTTPS 业务进程组成；HTTP 的 `/healthz` 仅证明导航进程存活。业务入口 `/healthz?ready=1` 检查配置、页面、数据库查询和迁移校验和，不就绪返回 503；不带参数仍只探活。还没配置的机器上托盘只起一条引导服务，见下面的首次设置几条。
- wheel 将 `web`、`migrations`、`resources` 装入 `peach/_resources`。`scripts/smoke_wheel.py` 在仓库外使用安装 wheel 的解释器运行；CI 消费任务只下载制品，不检出源码。测试只使用临时数据根。
- 设置文件固定是 `<数据根>/config.toml`。数据根按三步找：环境变量 `PEACH_DATA_ROOT`、
  项目根同级（含上溯四层，覆盖主检出、`peach-worktrees/<任务>` 和打包后的 `dist/Peach/_internal`）
  的 `peach-data/`、都没有就是「未配置」。优先级是环境变量 > 设置文件 > 内建默认。
- 全新机器只跑 `peach init`。不带参数且 stdin 是终端时进问答（题目、默认值与落盘逻辑在
  `src/peach/onboarding.py`，托盘设置页复用同一组函数）：问数据根、一个已存在的本地媒体
  目录、监听范围（仅本机／局域网）、端口、局域网名字，每题回车取默认，连续三次无效即退出且
  不写任何文件。然后建齐 `database`／`generated`／`sources`／`state`／`secrets`／`logs`／
  `tools`／`review` 八个目录、把账本迁到最新 schema、生成本机 CA 与访问口令、写出设置文件，问一句
  「现在扫描 <目录>？」（默认是）调 `peach.scan.scan_location` 登记文件，最后打印下一步与
  扫描摘要。写出的 `[media.locations]` 只有 `local`：Windows 上直接是那个目录、
  `[media.mounts]` 为空；macOS 上声明根是 `R:\media`、目录写进 `[media.mounts] local`。
  复制、writer 镜像、SMB 一律不问，保持关闭或留空。建目录、迁库、生成 CA 与口令、写设置文件
  这一整段在 `onboarding.apply()`，CLI 与设置页调的是同一个函数，只在打印方式上不同。
- 不进终端的那条路是托盘首启的引导服务。`peach-tray` 启动时新鲜读一次设置文件，判据在
  `tray.needs_setup()`：**没有 `config.toml` 且没有账本**才算需要设置。刻意不用
  `PeachConfig.configured`——托盘的单实例锁一启动就在数据根下建出 `state/`，而数据根的发现
  只看目录在不在，只用 `configured` 的话一次失败的启动就足以让下一次误判成已配置；反过来
  还没生成过 `config.toml` 的老部署账本是在的，不能被拖进首次设置。
- 需要设置时托盘不构建正常规格（全新机器上 `build_service_specs()` 会因为缺 TLS 材料抛
  `FileNotFoundError`），改起一条 `peach serve --setup --host 127.0.0.1 --port <设置里的端口，
  默认 8900> --no-mdns --no-ledger-sync`，然后把浏览器打开到 `http://127.0.0.1:<端口>/`。
  这条服务没有 TLS、口令强制置空（安全边界就是那个绑定地址），首页是首次运行表单，提交端点
  是 `POST /setup`：应用已配置回 404、非回环调用方回 403、设置文件已存在回 409。
- 切换由 `tray.SetupGate` 做，Windows 托盘与 macOS 菜单栏共用。它挂在健康轮询里（Windows 10 秒、
  macOS 5 秒），每轮新鲜 `settings_file.load_config()`：不再需要设置且 TLS 材料齐了，就停掉引导
  服务、按新数据根构建正常规格（`build_service_specs(tls_dir=..., mdns_hostname=...)`）并启动，
  托盘进程本身不重启。TLS 还没齐（例如这台机器没有 openssl）就原地等下一轮，不会拿一组缺文件
  的规格去启动。mDNS 名同样由这里传进规格：明文口的 `--redirect-origin` 必须是表单刚写下的
  `<mdns_name>.local`，而 `peach.config.MDNS_HOSTNAME` 是托盘 import 期就定型的旧值。
- 首扫不跑在引导服务里——那个进程在切换的那一刻就被停掉了。表单勾了「现在扫描」只写一个
  一次性标记 `<数据根>/state/first-scan.request`（内容是来源 ID），托盘切换完成后读走并删除它，
  用子进程跑 `peach scan <来源>`，输出落在 `<数据根>/logs/tray-scan.out.log`。标记只消费一次。
- 给了任何参数、加了 `--no-input`、或 stdin 不是终端，`peach init` 走非交互路径：按内建默认
  与 `--data-root`／`--host`／`--port`／`--mdns-name`／`--mount local=/mnt/media` 直接生成，
  写出的文件带 `local`／`115`／`pikpak` 三个示例声明根。已有账本不会被重建，它会提示改用
  `--from-existing`。
- `peach scan <来源ID> [根目录]` 把一个目录的文件元数据 upsert 进账本，只新增行与刷新
  `size`／`mtime`／`last_seen`，不改真相字段、不删行。根目录省略时取该来源在
  `[media.locations]` 的声明根，本机目录按 `[media.mounts]` 取；给了目录则必须落在声明根
  （macOS 上是挂载点）之内，否则拒绝——写进去的行否则翻译不回本机路径。
  `scripts/ledger.py scan` 是同一实现的薄委托。
- 已经在跑的机器用 `peach init --from-existing`：只写设置文件，不建库、不动 `peach-data/`
  下任何现有文件。它把当前实际生效的配置原样落盘，猜不出来的坐标（局域网 writer 地址、
  SMB 主机与账号）留空并逐条打印出来，用 `--writer-origin`／`--smb-host`／`--smb-user`
  等参数在同一条命令里给全，不要事后手改再忘了另一台。
- 设置文件已存在时 `init` 一律拒绝并返回 3，`--force` 才覆盖。覆盖前自己留一份副本：
  它是唯一记着本机坐标的文件。
- 设置文件语法错误时 `serve`／`migrate`／`status` 直接拒绝运行并报出文件路径和出错行，
  不会退回内建默认跑出一个假状态；`peach init --force` 仍然可用，是唯一的自救入口。
- 没有设置文件也不会崩：`peach serve` 照常起，`/healthz` 报 `configured=false`，页面提示
  先跑 `peach init`。
- `[media.mounts]` 的键是 `asset.location`（`[media.locations]` 声明过的来源 ID），
  值是该来源的**声明根在本机的落点**：声明 `local = 'R:\media'` 而挂载 `local =
  '/Volumes/RESOURCES/media'` 时，账本里的 `R:\media\x` 读作 `/Volumes/RESOURCES/media/x`。
  Windows 上整表为空是正常的，盘符本身就是挂载点。没挂的来源整体按脱盘处理，不报错；
  打错来源 ID 或写成盘符键都会被设置层直接拒绝，不会静悄悄变成「全部脱盘」。
  临时诊断用 `PEACH_MEDIA_MOUNTS=local=/mnt/res,115=/mnt/115` 覆盖（旧的
  `PEACH_DRIVE_MAP` 已删除，键空间不同，别再用）。
- 第一阶段写下的 `[media] R = '...'` 是盘符键，第二阶段起是硬错误：`serve` 会拒绝启动
  并直接给出改写成 `[media.mounts]` 的提示。用 `init --from-existing --force` 重写时注意
  它落盘的是**内建默认加环境变量**，不继承那个读不出来的旧文件——命令会先把这件事打印
  出来，旧文件里自定义过的 mDNS 名、writer 地址和 SMB 坐标要在同一条命令里重新给一遍。
- `replication.enabled` 决定这台机器做不做单写者复制，默认 `false`。关闭时不建同步
  观察器、不探测也不挂载 SMB、托盘不出两个 Ledger 菜单项、追更凭据不往共享副本写，
  `/healthz` 的 `ledger_sync` 是 `disabled`（不是 `writer`），写接口全开——没有第二台
  机器就没有「读者」，服务按独立写者跑。开启时上面这些逐项生效。
  `--from-existing` 写 `true`、全新 `init` 写 `false`。
- 不跑 `--from-existing` 就会掉回内建默认，两台机器上会变的至少有：mDNS 名、macOS 的
  来源挂载表、reader 的 writer 地址与代理、SMB 主机与账号、**复制开关**（默认关）。
  数据根、账本路径、Windows 盘符和监听端口不变。

### 把两台机器切到设置文件（ADR-0023 第 2、3 阶段）

先 Windows（写者）后 macOS（读者）：写者的坐标是读者填 `--writer-origin` 的依据。

Windows（PowerShell，项目根）：

```powershell
Copy-Item ..\peach-data\config.toml ..\peach-data\config.toml.bak
& .\.venv\Scripts\peach.exe init --from-existing --force
Get-Content ..\peach-data\config.toml
python scripts\restart_windows_tray.py
```

核对四点：`[media]` 下只有 `locations` 和 `mounts` 两个子表（没有 `R = ...` 这类盘符键）；
`[media.mounts]` 为空；`[replication] enabled = true`；重启后 `/healthz` 的 `ledger_sync`
仍是 `writer`（不是 `disabled`），托盘菜单里两个 Ledger 项都在。

macOS（读者，项目根）：

```bash
cp ../peach-data/config.toml ../peach-data/config.toml.bak 2>/dev/null
./.venv/bin/peach init --from-existing --force \
  --mount local=/Volumes/RESOURCES/media \
  --writer-origin https://<writer>.local --smb-host <writer>.local --smb-user <钥匙串账号>
launchctl kickstart -k gui/$(id -u)/io.github.longmeidao.peach.tray
```

核对：随便打开一个本地媒体资产能播（挂载表生效）、`/healthz` 报 `ledger_sync: reader`、
菜单栏里「同步 Ledger」还在。单机用户跳过 `--mount` 之外的所有参数，并让
`replication.enabled` 保持 `false`。

回退：把 `config.toml.bak` 改回 `config.toml` 再重启即可——设置文件是唯一改动面，
账本、媒体和凭据都没有被这次切换碰过。第 2 阶段不重写任何账本行，所以没有数据可回滚。

## 桌面入口与发布

- Windows 日常入口是当前用户 Startup 里唯一的 `Peach.lnk`，指向项目内的 `dist\Peach\Peach.exe`。
- macOS 日常入口是 LaunchAgent `io.github.longmeidao.peach.tray`，由 `python scripts/install_macos_agent.py`（`install`／`status`／`uninstall`）管理；`.app` 外壳的 bundle ID 是 `io.github.longmeidao.peach.app`，80/443 的转发落在 pf anchor `io.github.longmeidao.peach`。三个标识都取自 `src/peach/appid.py`，`setup_macos_port80.sh` 里那份 shell 字面量由 `tests/test_tray.py` 钉住一致。
- 标识变更在 Mac 上生效要跑一遍下面这串，遗留的 LaunchAgent 与 pf anchor 由 `install` 自己清掉：

```bash
launchctl bootout gui/$(id -u)/gg.lmd.peach.tray || true
python scripts/install_macos_agent.py install
sudo sh scripts/setup_macos_port80.sh install
python scripts/install_macos_agent.py status
launchctl print gui/$(id -u)/io.github.longmeidao.peach.tray | grep -E '^\s+pid'
launchctl print gui/$(id -u)/gg.lmd.peach.tray            # 期望「Could not find service」
sudo pfctl -a io.github.longmeidao.peach -s nat
curl -s --noproxy '*' -o /dev/null -w '%{http_code}\n' http://peach.local/healthz
curl -s --noproxy '*' -o /dev/null -w '%{http_code}\n' https://peach.local/healthz
```

  验收四项：菜单栏只出现一个 Peach 图标且 `status` 报「已加载」；`launchctl print` 的 pid 就是那个菜单栏进程；`pfctl -s nat` 列出 80 → 8900、443 → 8443 两条 rdr；两条 `/healthz` 都回 200。`peach.local` 换成本机 `[server].mdns_name` 的值。
- 发布入口是 `scripts/build_windows.ps1`：先用 `scripts/generate_brand_assets.py` 生成方形 Logo 与多尺寸 `.ico`，再构建单一 `dist/Peach/Peach.exe`；无参数运行托盘，`serve`／`migrate` 运行 CLI。桌面快捷方式由 `scripts/create_desktop_shortcut.ps1` 创建，自启动只由 `scripts/manage_tray_startup.ps1` 管理。
- 对外测试包由 `.github/workflows/release.yml` 承担：`build_windows.ps1 -Standalone` 用 PyInstaller onedir 生成完整 Windows 程序目录，压缩后由不检出源码的消费任务运行 `scripts/smoke_desktop.py`。`v<__version__>` tag 与版本不一致会失败，通过制品验收才创建 GitHub 预发布并附 SHA256；`workflow_dispatch` 只生成和验收 artifact。macOS 独立包另列待办，源码菜单栏构建入口仍为 `build_macos_app.py`。
- 刷新源码运行态不要用 Computer Use 点托盘：`python scripts/restart_windows_tray.py` 按精确 EXE 路径找到 pystray 隐藏窗口、发送正常停止消息、等托盘自行关闭子服务，再静默启动并核对新托盘重新拥有两个服务；找不到唯一窗口或退出超时就拒绝，绝不强杀后另启。
- `dist/Peach/Peach.exe` 是本机打包入口而不是可移动的独立发行版：托盘只打包了自己，服务进程仍由项目 venv 的 `peach.exe` 承担，`_peach_executable()` 从 exe 位置逐级向上找 `.venv\Scripts\peach.exe`，所以不要按「单文件绿色版」对外描述。
- 更新与打包的产物自带清退：托盘每次启动只保留最近 2 份 `dist/Peach/Peach.pre-source-sync-*.exe` 备份，并删掉 `<数据根>/state/source-sync-build/` 里不属于待应用记录的暂存构建（`WindowsUpdateInstaller.sweep_artifacts`）；`build_windows.ps1` 成功后删掉 PyInstaller 工作目录 `build/windows/app`。自动边界只认这两个命名：`Peach.exe` 本体、手工放进 `dist/` 的目录、`build/release-*`、`attic/` 都不碰，手工构建的残留自己删。
- PyInstaller 的资源直接位于 `sys._MEIPASS`，没有源码树的 `src/` 层；打包后的 `migrate`、Web 与品牌资源必须从这里解析，不能对 `config.py` 固定取 `parents[2]`。
- 创建 Win32 窗口前必须启用 Per-Monitor V2 DPI；正常动作不弹模态 MessageBox，更新检查在后台线程执行并用 pystray 原生非模态通知反馈。
- 菜单栏与托盘状态行逐个点名每个服务，例如 `HTTP 正常 · HTTPS 异常（状态码 503）`，异常附最近一次失败原因，不要改回只报「未运行」。

## 两个「同步」与 Ledger 写入角色

- 「同步开发进度」走 GitHub，「同步 Ledger」走 SMB 共享，不能合并成一个按钮：任一方不可达都不该拖住另一方。HTTP/HTTPS 服务只观察角色，不自动复制。
- 手动同步先用 `sync.resolve()` 只读判定这次会不会真的复制。`offline` 不是结论：macOS 重启后 SMB 共享不会自己挂回来，托盘按 `SHARED_SMB_HOST`／`SHARED_SMB_SHARE`／`SHARED_SMB_USER` 补挂一次再重判，真挂不上才回话。
- 补挂走 `osascript` 的 `mount volume`，并且必须先查一次钥匙串：没有对应记录时 NetFS 不报错，而是弹认证框一直等，一次后台点击既卡到超时又在用户面前推出密码框。钥匙串记录按主机名存，同一台机器的 IP 和 mDNS 名是两条不同记录。
- 补挂后仍是 `offline`，以及 `conflict`／`in-sync`，一律直接回话并且不停服务；确定会复制时才停止自己创建的服务，用 SQLite backup API 与原子替换复制，最后恢复服务。
- 「接管 Ledger 写入」只在共享盘不可达时短路：共享源在 macOS smbfs 上必须以 immutable 已关闭快照读取，共享目标不能由 SQLite 直接打开事务连接，健康端口不归本托盘时拒绝接管。
- 生成产物走 Syncthing 单向同步，和账本、和 Git 是三条互不兜底的通道：Windows send-only、Mac receive-only，五个文件夹 `snapshots`／`posters`／`avatars`／`logos`／`covers`，Mac 侧根目录在 `peach-data/artifacts/`（不要把指向它的符号链接设成同步目录），Trash Can 版本保留 30 天。
- `.stignore` 不跨设备同步，两端每个目录各放一份；方向是固定的，在 Mac 上生成的图片不会回到 Windows。

## 版本、更新与自我重启

- `src/peach/__init__.py::__version__` 是版本唯一来源，采用 pre-1.0 SemVer；Git commit 是构建标识，`vX.Y.Z` tag 是发布点，推到 GitHub 即触发 Release 工作流（见「桌面入口与发布」）。
- 「检查更新」只 fetch 和比较；「同步开发进度」只做 `merge --ff-only`，不 stash、不 rebase、不 `--force`——并行工作树和主检出共用同一个对象库与 reflog，任何改写历史的「顺手解决」都会把别的分支一起拖下去。工作区脏或两边分叉时原样报出来交给人。
- 快进动到 `tray.py`／`menubar.py`／`versioning.py`／`certs.py`／`netwatch.py`／`config.py`／`pyproject.toml` 时只重启子服务追不上，托盘要靠 `launchctl kickstart -k` 重启自己，顺序必须先 `stop_owned()` 再 kickstart，且前提是 launchd 报的 pid 等于自己的 pid。

## 网络、证书与 mDNS

- 托盘管理 HTTP `0.0.0.0:80` 和当前路由选出的 LAN IPv4 上的 HTTPS 443，显式参数、`PEACH_LAN_ADDRESS`、`lan_ipv4()` 依次覆盖；服务日志写入本机 `peach-data/logs`。
- 托盘起的服务全是非回环绑定，所以这台机器必须有访问口令，否则 `peach serve` 直接退出、托盘把那条服务显示成未运行。`peach token` 打印 `<数据根>/secrets/auth-token`（没有就现生成），`peach token --rotate` 换一个。换完要重启服务——进程只在启动时读一次——已登录的设备也要重新登录。
- 设备第一次访问跳登录页，把口令贴进去换成一年期的 HttpOnly cookie。reader 取 writer 的复核结果时发的是自己的口令，所以两台机器要用同一份 `auth-token`，复制过去即可。
- `peach serve` 按平台发布固定 mDNS 主机名，不在源码钉家庭 IP，仍保留 `Zeroconf()` 全合格网卡监听；mDNS 验收必须包含单元测试、运行态 health、DNS-SD、主机名解析和真实 LAN 客户端。
- 双机广播分工固定：macOS 是 `peach.local`，Windows 是 `peach-writer.local`，默认值收敛到 `peach.config.MDNS_NAME`，`PEACH_MDNS_NAME` 只做临时覆盖。服务可以同时跑，但两边同时写入会很快冲突转只读。
- `.local` 使用本地 CA，不使用 Let's Encrypt。证书与私钥保存在本机 `peach-data/secrets`；TLS 私钥禁用 ACL 继承，只允许实际服务身份、SYSTEM 和 Administrators。macOS/iOS 只安装并信任 `peach-local-ca.crt`，不分发任何私钥。
- 两台机器各有独立的本机 CA（secrets 按设计不共享）：iPhone/iPad 必须信任「当前正在服务的那台」的 CA，换机器服务后要装对应的 `peach-local-ca.crt` 并开完全信任，指纹用 `openssl x509 -noout -fingerprint` 核对。
- 对本机服务的 HTTP 探测必须 `trust_env=False`：代理客户端会设置系统级 HTTP 代理，httpx 默认经 `urllib.getproxies()` 读它，探测 `127.0.0.1` 的请求被送进代理并由代理回 503，服务活着却被判「未运行」。修复在 `peach.tray.ServiceManager.healthy`，`test_health_check_never_goes_through_a_proxy` 守门，新写的健康检查同样适用。
- macOS 系统代理的例外列表必须包含 `*.local`、`localhost`、`127.0.0.1` 和本机局域网网段：代理核心解析不了 mDNS 名字，浏览器打开 `.local` 会被代理回 503（终端直连正常）。用 `networksetup -setproxybypassdomains` 设置、`scutil --proxy` 的 `ExceptionsList` 复查；代理客户端重设系统代理后这一列表可能被清掉。
- FastAPI 是唯一 Web server，不得恢复平行 `http.server` 或动态 legacy loader；口令通过 `/login` POST 换成 HttpOnly cookie，`?t=` 只做一次性场合，它会把口令留在访问日志和浏览历史里。
- 切换服务前检查 80、443、8900 端口和实际进程归属。9999 已移出这份清单：服务运行期不再连接 Stash（ADR-0021）。

## 媒体解析与转码

- FFmpeg/ffprobe 依次从显式环境变量、本机 `peach-data/tools/ffmpeg/bin`、`PATH` 解析，不回退到 Stash 私有目录。
- 115/PikPak 播放依赖 CloudDrive 的 `B:`／`A:`，盘符对 Windows token 的可见性不同，最终以 Peach 对已知作品的 `/stream` 实测为准。
- 浏览器不支持的 AVI、MKV 等容器由 `TranscodeService` 缓存为兼容 MP4 并通过同一 Range 端点提供，永不改写原媒体；缓存未命中时先用同一会话内可取消、最长 20 秒的 ffprobe 探测。
- 转码优先保留码流：H.264 `yuv420p`／`yuvj420p` 保留视频，AAC 直接复制，其他音频只转 AAC；需要视频转码的 Windows 输入优先 `scale_cuda` + NVENC，两条都失败才回退 `libx264 veryfast`，macOS 不试 CUDA。探测与每次尝试都受 2 槽并发闸门、1 小时总时限和 stream session 取消保护。
- 长任务只停止自己拥有且命令行匹配的 Python/FFmpeg 进程树，禁止全机终止 FFmpeg。

## 资源同步与删除边界

- 网盘目录由人在 CloudDrive 外部整理后，必须经「管理 → 资源同步」显式对账，不做后台静默删除：只核对已挂载来源，离线来源整源跳过，单个目录不可读时保留账本行并回报。
- 真实账本规模下逐文件或同步 HTTP 请求实测 5 分钟仍不返回，所以全库扫描必须使用后台作业并逐来源回报进度，同一目录只枚举一次，目录元数据并发固定为 8；应用不得重跑全库或盲信旧结果。
- 资源同步只清理无正常馆藏引用的 snapshots、posters、photo-thumbs、transcodes、stream-segments、按 asset 生成的头像和共享番号封面；候选 CSV、provider evidence、实体头像与 Logo 不在自动清理边界。源文件缺失的 asset 先进回收站，清空回收站才永久删除账本行。
- 可重建缓存的删除边界由当前数据库路径拥有：生产库只可清理同一 `peach-data` 下的缓存，临时库只可清理其临时目录子树，边界外一律跳过。一次漏配曾在清空回收站的测试里删掉真实 JAV 封面。
- 「垃圾文件」覆盖 `local`／`115`／`pikpak` 全部物理 asset 类型，推广名、目录与创作者位证据跨类型共用，视频另加时长、体积和同番号长版证据，Windows `.url` 直接进入人工判断，在线 URL 排除。
- 垃圾文件候选只可移入回收站；「不是垃圾」按 asset 写入可撤销的 `junk_file` 复核决定并留在「已排除」视图，不扩大成域名或来源白名单。

## 迁移、备份与运维脚本

- 真实迁移前依次执行 SQLite 备份、asset/tag 计数、`PRAGMA integrity_check`、迁移版本检查、服务 smoke test；已应用与待应用迁移以 `docs/STATUS.md` 和实际 `migrate status` 为准。
- 已应用的迁移文件不得修改，任何后续变更必须新增版本：`0007` 曾在应用后被改写格式导致校验和漂移，只能用迁移前备份重放、逐条比对差异为 0 后才校正 `schema_migration`。
- 导入运维脚本不得触发文件、网络或数据库副作用；`scrape_codes.py` 默认写可续跑复核 CSV，`clean_names.py` 先预览，`--apply` 必须同时给出 `--backup <路径>`，备份落盘后当场校验完整性（`peach.scripting.open_for_write`）。
- 文件名只按 ledger 已确认的番号规范化，不从名称重新猜番号；大小写单改走同目录临时名，去广告后撞名用 `(2)` 起的后缀保留两份媒体。
- `generated/cover-fetch-log.csv` 是来源、尺寸和结果证据，不随图片清理；图片丢失时用 `scripts/fetch_jav_covers.py --restore-successes` 按成功记录的原 URL 恢复并原子替换，失败保留为失败，不拿缩略图冒充封面。
- 封面候选必须限定在当前作品的主封面节点：作品页混有数百张关联作品、剧照和演员头像，禁止对整页图片 URL 逐张量尺寸。
- FC2CMADB 的文章存档只作官方商品页镜像证据：标题与保守翻译后的标签写候选 CSV 并与最新 JAV 元数据批次一起进入 `/review`，不自动写 ledger；封面把列表 `w276` 换成实测存在的 `w1200`，再走 `fetch_jav_covers.py --fc2-only` 的解码、宽度、磁盘和原子落盘门槛，失败留逐条日志。
- 批准官方标签时必须用 `(asset_id, tag)` 冲突更新来源与置信度：`asset_tag` 的唯一约束会让 `INSERT OR IGNORE` 保留旧来源，导致值已存在却不显示「官方」。

## 前端与验证口径

- 数据库元数据不得插值到 inline JavaScript 事件属性：真实厂牌名里的撇号曾直接造成 Firefox 语法错误。
- 前端 API 包装必须先检查 HTTP 状态再返回 JSON：冲突只读时写端点返回 `409` 和错误 JSON，当成普通成功对象会清空选择并重载，用户只看到条目原样回来。批量处置和详情反馈必须保留当前选择并显示失败原因。
- 验证分开报告：静态/单元/API、桌面浏览器、390×844 手机、生产服务是否已重启。
