# 复用清单

## Board 界面与数值设置

- 作者别名管理复用逐字复制进 `frontend/src/react/boardui/` 的 BoardUI `Table`、关注列表共用的 `DataTableFrame`、`AuthorAvatar` 和既有别名 API；公开结构与固定资源见 `BOARD_UI.md`。待合并与已保存两张表都只有几行，排序、分页用不上，不接 `@tanstack/react-table`；合并范围是这一屏自己的勾选状态，所以表里的勾写 `slot={null}`，不走 React Aria Table 自己的行选择。扫描与采集那三种方式收在一颗主键加一个下拉里：触发键用 BoardUI `Button`，面板用已在用的 React Aria `Popover`，行的外观取注册表 `select` 条目带来的 `menu-styles.ts`，无新增依赖（见 `frontend/src/react/boardui/ORIGIN.md`）。

- 关注列表分页复用 `pagination.ts` 的页码范围与边界裁剪（React 与遗留层共用这一份纯函数）；默认视图按创作者组，表格按来源。表格视图新引入 `@tanstack/react-table` 8.21.3（MIT，https://github.com/TanStack/table ）：列定义、排序状态、行选择与分页交给它，行的身份是来源 ID（`getRowId`），排序与分页跑在全集上、页是最后一刀。归属与时机按 ADR-0031「前端基础库」，是这条待办点名要引入的那一个库，不是顺手加的。两种视图共用同一个来源 ID 集合，批量操作发的是整个集合而不是屏幕上这一页。官方分页与 Table 源码的固定哈希见 `BOARD_UI.md`。`frontend/test/react/follow-manage.test.tsx` 验了 25 位创作者、跨页跨视图勾选与批量写。

- 窄屏筛选框共用 `filterScrollState()`、现有滚动帧调度和原生 sticky；同一方向累计 8px 再切换吸顶，保留文档占位与键盘可达性，无新增依赖。

- 搜索玻璃复用 `glideEase()` 的采样弹簧；`web/js/search-morph.js` 只负责视口边界与轮廓关键帧，证据与差异见 `BOARD_UI.md`，无新增依赖。

- 横排滚到头的回弹由 `wireHorizontalScroller` 内的 `edgeBounce` 承载，头像排、厂牌排、新作排、筛选条共用。transitions.dev 的配方里没有这一条（2026-09-23 核对过全部 43 条）。越界位移借 UIScrollView 的橡皮筋公式 `(1 - 1/(x·c/d + 1))·d`，c = 0.55，与 use-gesture 的 `rubberband` 同一条（MIT，https://github.com/pmndrs/use-gesture ）。回弹走 `--spring-pane`。只抄了公式，不引依赖：use-gesture 管的是手势识别，而这几排的拖动与滚轮归属已经由 `wireHorizontalScroller` 判定。新作排的自动滚动是同一文件里的 `wireAutoScroll`，同样没有新增依赖。

- 浮层筛选由 `web/js/ui-components.js` 的 `mountFilterFrame()` 承载：首页与实体资料页共用视图、标签、读数、控件四个槽位。外框负责玻璃与吸顶，页面负责查询状态和事件；视频、照片与名册更新只替换底行。复用现有 Board 控件及原生 DOM，不新增依赖；身份与观看状态的组合沿用 `/api/items`。

- 组件映射、官方公开注册表证据与许可证见 [Board 界面](BOARD_UI.md)。`web/board.css` 共用正式页面结构，设置可关闭该视觉层；登录、首启与错误页共用 `web_entry.entry_page_style()`，登录页是首启 Auth Card 的单字段形态。
- `frontend/src/number-setting.ts` 共用带单位输入、可选 Switch、整数边界和锚定错误提示。关闭保留上次合法值，异步读取后切换也恢复实际值；业务保存仍由调用方负责。
- 筛选内层复用 `filterChipHtml`、`sortControlsHtml`、`collectionHeaderHtml`，首页、关注和资料页提供查询键及读数。横向行复用 `wireHorizontalScroller`，拖动、滚轮、渐隐与卸载清理归同一个生命周期。
- 选择范围与工具条复用 `frontend/src/selection.ts`；馆藏、关注与复核保持各自身份、可见顺序、默认选择及写入权限。批量失败项的保留由业务负责。
- React 设置分区复用 `frontend/src/react/settings/section.tsx`：`Section` 提供标题、卡片与表单外壳，`Footer`、`Note`、`ErrorText`、`FactList`、`Progress`、`Disclosure` 补齐 BoardUI 注册表没有的底栏、行内提示、读数、进度与折叠。`use-action.ts` 的 `useAction` 负责提交互斥、卸载取消与原位错误，`busyProps` 写忙态。密码字段校验与服务端回执仍归各分区，不自动重试写入。后台任务（口味读取、封面采集、amane 桥重建、关注检查与查找）共用 `frontend/src/react/background-job.ts` 的 `useBackgroundJob`。
- 增量列表复用 `wireLoadMore` 的请求锁、原位重试与卸载清理；页面注入读取、追加、代际判定和可用条件。首页页码在读取成功后推进，照片沿用随机种子，关注合并分组。显式页码继续使用 `pagination.ts`。
- 在图上框一块由 `frontend/src/crop-geometry.ts`（纯算术）加 `react/crop/crop-frame.tsx`（一张图、四块压暗、一个可拖可缩的框）承担，换头像与裁封面共用；坐标一律是源图像素、右下开区间，显示像素只在进出这一层时换算。不引 `react-image-crop` 那类库：要的就是一个能拖能缩的矩形，换到的只有把手样式，代价是一条新依赖和一套它自己的坐标约定。详情页仍是遗留壳，所以裁封面做成 island 从 `web/app.js` 挂（ADR-0031），交互不写两遍。
- 后台任务复用 `watchJob`、`followJobProgress` 默认面板及 `jobActivityHtml` 的真实计数／未知总量显示；关注、来源扫描、链接检查和扫描采集共用渲染。业务保留启动、终态回执和结果面板，不新增轮询循环。
- 图标按钮统一清除浏览器内边距并居中 SVG，不覆盖业务显隐。Remix Icon 由 `vendor_web_dependencies.mjs` 生成设置导航 symbol；随机按钮保留原有双路径动画。
- `frontend/src/react/taste/taste.ts` 使用 d3-sankey 0.12.3（BSD-3-Clause；类型包 0.12.5）计算来源网站到创作者线索的流向。布局依赖不读取浏览历史；Peach 提供去重聚合值并负责隐私边界。分发许可随 `web/vendor/d3-LICENSE.txt` 保留。

复核复用 Checkbox、Button、Badge、Select 与 `/api/review/decision`，默认勾选并沿用馆藏页 Shift 连选语义；支持跨组通过／拒绝与无歧义的共同来源选择。按候选数量、来源组合或字段分组，每项仅出现一次，切组保留选择；成功移出、失败保留，页面离开后停止后续提交。整页在 `frontend/src/react/review/`，一条队列一个 `queryKey`，判定后改缓存不重取；完成结果复用成功 Note。身份候选复用创作者页、作品详情与 revealSource 核对样本；来源图片和缺图占位共用 220px 预览区，加载失败保留占位。样本读取支持无缩略图作品，回收站不参与。

## 本机设置与卸载

- Peach 代理复用 HTTPX 的 `trust_env`、`proxy` 与本机 CredentialStore；来源只选择公共策略或直接连接，地址不回传。单一旧代理可继承，多个地址需明确选择。
- 自启复用项目 Windows WScript.Shell 快捷方式和 macOS LaunchAgent；[微软原生文档](https://learn.microsoft.com/en-us/troubleshoot/windows-client/admin-development/create-desktop-shortcut-with-wsh)支持 TargetPath、Arguments 与 Save。Windows 自带 COM，无新增依赖；pylnk3 无需引入。临时中文路径的真实快捷方式读、写、移除通过。
- 独立包卸载复用正常托盘退出和 Windows PowerShell 助手；计划限制程序标记、数据直属目录、媒体不重叠，助手拒绝目录链接。助手会退出仍从程序目录运行的进程并重试删除；完全卸载只把 `config.toml.<说明>-<日期>-<时刻>` 视为 Peach 写的设置备份，手工复制的 `config.toml.bak` 保留。临时程序、被占用文件、历史设置备份、数据、媒体与无关文件组成的真实输入验证只删除计划内容和整个解压程序目录。源码树仅提供手动卸载说明。
- 扫描与采集统一挂在数据管理；首页进度 Banner 跳转同一入口。默认排序与方向使用浏览偏好，显式 URL 优先。

目录页进度横幅与数据管理卡片共用 `frontend/src/react/library-processing/` 那一份读取，读同一个 `LIBRARY_PROCESSING_KEY`，轮询由 TanStack Query 合成一份；启动只提交一次，状态查询接续托盘首次处理。首页在完成后收起，失败跳转数据管理；数据管理持续读取阶段与真实计数。Geist Banner 取证与 Peach 差异见 `docs/reference-snapshots/vercel-geist-library-banner.md`。
## 独立测试包在线更新

- 自动更新设置复用 APScheduler 3.11.3（MIT，项目已有依赖，Python 3.12+ 与 Windows/macOS）、共享 HTTPX 发行查询、filelock 与原子 JSON 写入，安装继续走 `standalone_update`。按 [interval trigger](https://apscheduler.readthedocs.io/en/3.x/modules/triggers/interval.html) 每分钟检查是否到期；本机持久时间与文件锁协调多个服务，关闭、6/24/168 小时间隔与源码下载限制由 Peach 管理。默认关闭，下载仅准备安装，重启仍需确认；没有新增依赖或安装框架。设置保存在 state 目录的 `automatic-updates.json`。

- 版本与资产信息复用 GitHub Releases REST API，测试通道包含预发布版本；查询复用项目 HTTPX 0.28.1，下载用其流式读取，ZIP 解压使用 Python 3.12+ 标准库，互斥复用 FileLock。没有新增依赖。只读查询已对真实 Release 验过：只有发布记录里已上传的完整独立包才进入更新，查询不下载也不安装。
- Peach 维护安装策略与进度：下载校验后在程序同卷暂存，用户确认重启，复制出来的包内助手等待原托盘退出，再切换完整目录；失败保留或恢复旧目录。配置、数据库与媒体不作为更新包内容写入。
- 已核对 [Velopack Windows 文档](https://docs.velopack.io/packaging/operating-systems/windows) 和 [WinSparkle 文档](https://winsparkle.org/)：前者要求其安装目录与包格式，后者要求 appcast 并使用原生更新界面；现有 GitHub 产物为 PyInstaller ZIP，进度在 Web 显示，因此复用现有托盘进程与目录替换协议，未引入额外安装框架。
- Web 复用 Fieldset、Progress、confirmModal；状态由 `standalone-update.json` 保存。下载按字节计量，解压按文件数计量，替换使用阶段进度；服务重启期间保留等待状态，恢复连接后核对版本。
- 新版有待应用迁移时，重启安装复用 `migrate upgrade --yes`，先保存 SQLite 备份；迁移或启动失败时恢复数据库与程序。数据库备份位于用户数据根的 `state/update-backups/`。

JAV 默认封面（官方封面／预览图）与默认大小（大图／小图）独立保存，复用 localStorage、共享 Switch 和既有 `/cover`、`/poster` 接口，不新增依赖。`frontend/src/jav-artwork.ts` 负责作品身份、偏好恢复与缺图回退；首页、接着看、实体作品、详情推荐、Mix 静止与翻图、播放队列共用封面选择。小图保留所选来源，设置换图保留播放和滚动位置。

这是实现查找表。新增、恢复或重写代码前必须按
`.claude/skills/peach-reuse-first/SKILL.md` 先查本文件、当前树、Git 历史和成熟外部实现。

## 复用决策门槛

- Python 安装与构建复用 [uv](https://github.com/astral-sh/uv)（`pyproject.toml` 只设下限 `>=0.12.13`，工具版本不进依赖图）和官方 setup-uv 10.0.1，Astral 持续维护，许可证分别为 MIT/Apache-2.0 与 MIT。
  使用 uv 项目接口、`uv.lock` 和 `uv sync --locked`；Dependabot 使用官方 `uv` 生态维护锁文件。
  开发与构建在隔离工作树创建环境，生产 venv 不参与精确同步。直接依赖精确固定，传递依赖由锁文件复现；动态项目版本无需修改锁文件。
  测试数据库复用当前树与 Git 历史中的 `tests/support/ledger.py`，迁移生成模板后复制独立临时库；真实迁移测试仍执行迁移。重试测试复用已有 sleeper 注入点。
  Windows 临时库 POC：五次迁移 1.552 秒，五次模板复制 0.006 秒，完整 schema 一致。
  CI 复用 GitHub Actions 独立 runner 分片与现有 unittest 入口；Peach 仅维护影响域策略，不引入并发测试框架。验证记录与最小安装规则见 `TESTING.md`。

- 访问密码复用 Python 3.14 的 [hashlib.scrypt](https://docs.python.org/3.14/library/hashlib.html) 与 OpenSSL，浏览器会话复用 [ItsDangerous 2.2.0](https://itsdangerous.palletsprojects.com/en/stable/)（Pallets 维护、BSD-3-Clause、Python 3.8+、纯 Python、wheel 16 KB、无传递依赖）；本机原子配置写入复用 tempfile/os.replace，并将已有 filelock 3.32.4 纳入运行依赖。当前树和 Git 的认证入口已有内部口令、三种拒绝响应和本机配置守卫，继续复用。Starlette SessionMiddleware 采用统一时长并随响应更新会话，不满足每台设备选择固定截止时间的要求；直接使用同源签名库，由 Peach 维护可选密码、截止时间与撤销策略。临时文件 POC 的密码验证、签名验证和篡改拒绝通过，耗时 0.153 秒；真实凭据未读取。新增依赖不包含账户体系或数据库迁移。
- Cloudflare Quick Tunnel 复用官方 `cloudflared`（Apache-2.0）而不在 Peach 内实现隧道协议。源码环境只管理 PATH/环境变量中的进程；Windows 独立包旁路文件固定为 `2026.9.0`，资产、下载地址和 SHA-256 记录在 `scripts/cloudflared-windows.json`，由 `fetch_cloudflared.ps1` 与构建脚本双重校验。Quick Tunnel 的 URL 申请和边缘连接是两个阶段，Peach 使用官方 `--pidfile`（首次成功连接后才写入）作为就绪判据；未取得连接不向页面宣称可用。源码 HTTPS origin 使用项目 CA，独立包使用回环 HTTP，并由当前进程持有的随机 URL 参与写请求来源校验。

- README 交付检查复用系统 Git 的 `diff --no-renames -z` 和 `interpret-trailers --parse`，
  挂到既有 `agent_worktree.py ready/integrate`；Peach 只定义影响文件与双语声明 policy。
  本机 Git 2.55.0.windows.3（GPL-2.0，持续维护）与 Python 3.12+ 标准库，无新增依赖或运行时体积。
  已检索当前树与 Git 历史：已有 Python 下限文档测试及工作树门槛，没有 README 影响声明。
  官方依据为 https://git-scm.com/docs/git-interpret-trailers 和 https://git-scm.com/docs/githooks 。
  原生 hook 不会随 clone 自动安装，且无法判断文案语义，因此选项目共有交付入口，不加账户专属 hook。
  真实 Git 临时仓库回归覆盖缺声明、双语缺一、虚假 updated、暂存但未提交、重命名与无影响原因；
  不写真实 ledger，不改生产。维护流程见 HANDOFF「README 维护」。

- 配置访问判定复用 ASGI 连接的 `client` / `server` 地址与 Python 标准库 `ipaddress`，不新增依赖。
  本机连接匹配回环地址或服务端 IP；Host 只校验托盘配置的域名或绑定地址，不能用来证明调用方在本机。
  配置保存复用修订号校验、原子替换与 `SetupGate` 重载标记；托盘子服务通过 `PEACH_TRAY_MANAGED` 声明重载能力。
  安装检测复用标准库 `winreg`、`shutil.which` 和安装目录，媒体工具复用 `FFmpegResolver`；不把脱盘判为未安装。
  下载入口核验于 2026-09-06：[CloudDrive](https://www.clouddrive2.com/download.html)、[WinFsp](https://winfsp.dev/rel/)、
  [macFUSE](https://macfuse.github.io/)、[FFmpeg](https://ffmpeg.org/download.html)、[OpenSSL](https://openssl-library.org/source/)。

- 发行身份复用各来源解析器与 Seesaa 的原始 DTO；数字前缀等价属于 Peach 领域 policy，不新增依赖。
  真实 r18dev 快照中请求 `390JAC-040` 却返回 `JAC-040`／`118jac040`；Jackson 表中两者是不同商品行。
  查询回退不能承担身份确认；所有响应按原始查询检查，MGStage 官方详情路径可佐证展示编号别名。
  外部适配器负责取值，不采用其首条搜索命中作为 ledger 身份断言。

- Seesaa 作品表复用 HTTPX 0.28.1（BSD-3-Clause）、Beautiful Soup 4.15.0（MIT）及现有
  `HostLimiter`、番号规范化、字段候选和快照协议；不新增依赖，沿用 Python 3.12+ 与 Windows/macOS。
  2026-09-06 检查 Javinizer-Go `d9724f239d7e127afcb747fa8ce4358685912f50`（MIT）及 MetaTube
  `6a5e6128c725187aeaf921d48ed7d9cd9f30671b`（Apache-2.0）的来源目录，均无 Seesaa 适配器；
  两者分别于 2026-09-05、2026-07-12 有仓库更新。本站例外由 `peach.sources.seesaa` 承担 EUC-JP、
  作品表列映射、精确行身份与未知名单保护，套的是站点解析器契约；别的来源按 ADR-0044 归到自写解析器或 amane 桥。
  真实 Flower 页 HTTPX 取得 200／253975 字节，FKOS-007 解析出 10 位出演者；公开搜索亦可发现
  对应表格。`scrape_codes --profile seesaa` 是正式消费者，不另建刮削 CLI。详见 [来源采集](SOURCING.md#seesaa-wiki-作品证据)。

- 补女优别名后继（ADR-0055、0061、0064）复用 `minnano_av` 的检索与资料表解析、`sources.seesaa.WikiPages` 取页层、
  `sources.fc2cmadb` 的女优栏握手与解析、
  `HostLimiter`、`scraping_access` 冷却、`metadata_alias_resolve.is_planning_alias` 与
  `apply_alias_candidates.py` 的四种不写口径，撤回复用 `revert_auto_landing.py`。minnano-av 那一站没用
  `page_cache.Site`：它只返回正文、丢了跳转后的最终地址（复核产物要记她那一页的真实地址），限速器按实例
  各起一个，几十条后继接连跑等于没有间隔，还会把以 200 回来的机器人验证页当正文缓存下去。取页器
  `MinnanoPages` 另记最终地址、共用一个 `HostLimiter`、认出验证页不缓存并记冷却。
- 补女优资料后继（`performer_profile_followup`，ADR-0067）复用补别名后继的入口
  `minnano_profile_pages`、名字核对与 `MinnanoPages`（加 `source` 冷却键与 `max_age` 缓存期限，avwikidb
  也用它，传输换成 `SourceTransport`），排单复用 ADR-0053 的 `Attempts`（写成的记号保 30 天）。
  解析在 `minnano_av.profile` 与 `avwikidb`，读写在 `performer_profiles`；两站都读页面自带的结构，
  minnano-av 读资料表，avwikidb 读 JSON-LD。不采用的候选：`kanojo-db/scrapers` 的 Minna no AV
  爬虫与 `stashapp/CommunityScrapers` 的 Minnano-AV 规则都不是可安装的库，后者是 Stash 的 XPath 配置
  （Stash 适配器已关，ADR-0021）；站点入口与名字核对 Peach 已有一份，只补资料表逐格规整。

测试与集成复用 `test_runner.py`、`agent_worktree.py`；进程互斥采用开发依赖
`filelock==3.32.4` 的 `FileLock`（[官方用法](https://py-filelock.readthedocs.io/en/stable/tutorials.html)）。
跨进程占锁与释放由临时 Git 仓库回归验证；代码、环境和范围记录属于 Peach 的集成约束。
### 播放、身份与控件实证

- 2026-09-05 手工截图的 PNG 像素统计：页面 `#04060A`、框体 `#080A0D`、操作条 `#141619`、选中项 `#191B1E`。操作条复用 `--overlay-5`，骨架与最终控件共用灰阶。截图是静态证据，不登记为可重抓上游资源。
- [JavDB JBS-023](https://javdb.com/v/6gzM)：项目取页器取得 `風見あゆむ`，与 2026-09 之前经 Javinizer-Go 留下的快照一致。javdb 是有码与素人链社区那一档的成员；候选保留 community 来源性质，不自动写真相字段。
- 编码边界依据 [MDN 视频编码说明](https://developer.mozilla.org/en-US/docs/Web/Media/Guides/Formats/Video_codecs) 与 [ffprobe 流探测文档](https://ffmpeg.org/ffprobe.html)。复用当前 FFmpeg，无新增依赖；Peach 仅持有兼容格式判定与缓存策略。

CloudDrive 引导复用现有 `settings_file`、`platform.root_online`、`scan_location` 和 React
配置页；来源仍为 `local`、`115`、`pikpak`。外部挂载由已安装的 CloudDrive 负责，
[官方帮助](https://www.clouddrive2.com/help.html) 规定 Windows 使用盘符、macOS 使用目录挂载点。
CloudDrive 为外部应用，本项目不捆绑其二进制或依赖其管理 API，也不保存网盘凭据；因此不引入
非官方 CloudDrive SDK。路径处理复用 Python 标准库 `pathlib`、`os.scandir`、`tomllib`，
不新增依赖。最小实证使用盘符 `A:/`、`B:/` 与 macOS 挂载形状，验证配置往返、重叠拒绝和
读取目录失败的离线结果；Peach 保留表单、来源归属及扫描选择。

- 抓取入口的复用缺口与证据统一见 [抓取复用审计](SCRAPING_AUDIT.md) 和 [逐脚本 CSV](scraping-audit.csv)；
  跨用户安装、来源网络、Cookie GUI、最高可得画质与图像清单按 [ADR-0024](adr/0024-mark-manifest-not-bundled-bytes.md)。
  私有后缀判断采用 tldextract 5.3.2（BSD-3-Clause、Python ≥3.10、平台无关），使用随包 PSL、
  `suffix_list_urls=()`、`cache_dir=None`、`include_psl_private_domains=True`；106 kB wheel，依赖
  requests、requests-file、filelock、idna；日本二级后缀与 GitHub Pages／Blogspot 租户 POC 通过。
  Instaloader 4.15.3（MIT）匿名解析 Bambi／LINX 均为 ConnectionException；独立登录会话未取得，
  它和 browser_cookie3 均不进入正式依赖。HTTPX、curl_cffi、Pillow、amane 桥和现有候选缓存是正式基础；
  各脚本的请求节拍应复用 `scripting.RateLimiter`／`HostLimiter`，不为同一职责再装一套框架。

- 采集 GUI 复用 React island、CredentialStore、HTTPX、Pillow 和 BackgroundJob；
  `jav_cover_fetch` 同时服务界面与 CLI。Peach 保留域内凭据、来源路由、预算、冷却、番号身份与
  高清替换策略。Cookie 文本由标准库 SimpleCookie／MozillaCookieJar 解析；不导入 pickle。
  实施范围与跨平台缺口见 [来源采集](SOURCING.md)；POC 脱敏证据在本机 attic 的抓取复现目录。

- 删除失效链接与资源同步的执行阶段复用 `BackgroundJob.start_result` 保存终态回执；刷新只查状态，写入请求不自动重放，原有确认与检查结果过期门槛保持有效。
- 关注进度复用 Fieldset 与 Progress；完成时保留内容取数，按作者检查复用 `sources` 范围参数，报错作者复用现有身份解析。无新依赖；参考取证见 `reference-snapshots/vercel-geist-note-progress-switch-analytics.md`。

- 关注检查、来源查找和口味刷新复用 `jobs.BackgroundJob`，浏览器状态跟进放在 `frontend/src/jobs.ts`；不新增队列或调度依赖。HTTP 继续使用固定的 HTTPX 0.28.1（BSD-3-Clause）和 curl_cffi 0.16.2（MIT），支持现有 Python 3.12+ 与 Windows/macOS 打包。[HTTPX 原生重试](https://www.python-httpx.org/advanced/transports/)只覆盖连接失败，无法统一两个 transport 的读超时、临时 HTTP 状态与页面进度，因此由现有连接器负责 GET 重试策略。截图中的 TLS 握手超时作为隔离 transport 输入，验证第 5 次成功、耗尽、403 单次终止和 POST 不重放；不新增依赖体积。任务状态保存在服务进程，浏览器刷新后通过读接口恢复；服务重启不自动重放任务。

- 标签发布复用系统 Git、GitHub CLI 2.100.0（MIT）和 [Actions runs REST API](https://docs.github.com/en/rest/actions/workflow-runs)，不新增 Python 依赖；`release_tag.py` 只实现版本、主线归属、同提交最新 CI 与不可覆盖策略。Windows Python 3.14 使用提交 `45168dd` 的真实成功 Test 记录完成只读 POC；失败/运行中/其它分支与 master 并发推进用隔离测试拒绝。工作流仍复用既有 Release 制品验收，未引入发布服务。

- 独立 Windows 测试包复用 PyInstaller 6.22.2（GPL-2.0-or-later，带分发 bootloader 例外）的 [onedir 与自启动子进程](https://pyinstaller.org/en/stable/common-issues-and-pitfalls.html)；使用已有精确固定的 build 依赖。Python 3.14 / Windows x64 在清除开发工具 PATH、隔离数据目录下实测初始化、页面与 API。保留 Peach 的进程所有权、数据目录、配置和扫描策略；onefile 的托盘入口只用于既有源码部署，独立包采用完整目录以共享资源并避免重复解包。没有新增运行时依赖。

- 运行一致性复评：复用 `LedgerDatabase.write_transaction` 的提交边界和标准库 `OrderedDict`；HTTP 导航复用 FastAPI/Starlette，图片复验复用 `StaticFiles.is_not_modified` 与 `FileResponse` 的 ETag。列表使用 SQLite 的 IN/UNION 保留隐藏标签与多标签组合，不引入查询框架。
- 馆藏侧栏复用 `catalog_filter` 的列表条件，已保存在线卡片复用关注来源的标签与封面投影，详情复用 `openFollowDetail`、Video.js 和媒体队列。导航范围与标签计数位于 `frontend/src/sidebar.ts`；不新增依赖。截图所示 F95 合集的只读核对结果为无封面、无标签、无已解析媒体，详情按现有来源信息展示。
- wheel 资源复用 setuptools 84.0.0 的 `build_py.copy_tree`，资源位置遵循[官方包内数据建议](https://setuptools.pypa.io/en/stable/userguide/datafiles.html)。自定义钩子仅复制三个既有资源目录，因为源码、桌面构建和前端产物仍共用其维护位置；Windows 基础依赖全新安装及仓库外 API 冒烟已验证。

- 先用真实输入做无写入 POC，再决定「直接依赖、固定来源实现、保留自研」三者之一。
- 采用项要记录固定版本、许可证、首个消费者和 Peach 保留的领域边界；候选依赖不得空转。
- 保留自研要记录被拒绝的候选和不可替代约束，不能只写「特殊需求」。
- 外部项目不适合作为运行时依赖，但其公开数据模型或算法明显更成熟时，固定 revision 后作为参考
  实现；许可证不允许派生或来源不稳定时只作行为证据，不复制代码。

## Peach 必须自研的领域逻辑

以下属于产品行为，继续由 Peach 实现：

- 女优、厂牌、创作者、标签的规范身份、别名和来源；
- profile 行为、稍后看、播放列表、口味和推荐排序；
- 本地、115、PikPak、Stash、在线来源的绑定和回退策略；
- 计费来源授权、隐私分类和候选复核导入；
- 物理资源垃圾候选的跨类型证据、人工复核和回收站语义；空目录清理复用 Python 标准库自底向上的 `os.walk` 与只删空目录的 `Path.rmdir`，Peach 只负责在线来源、根目录保护和 CloudDrive 并发消失边界；
- 私有获取来源、出处引用和发现关键词；
- 创作者级视觉采样语义；
- 推理 Provider 与 Agent Provider 的能力契约；
- 任务归属、进度、取消、成本和证据规则。

下面这些是基础设施而不是产品行为，所以单独记下被拒绝的候选和不可替代约束，避免再从「这看起来该有现成库」开始。

| 自研实现 | 被拒绝的候选 | 不可替代约束 |
|---|---|---|
| `mp4index.py` 有界 MP4 关键帧索引 | PyAV、`pymp4`、Bento4 | PyAV 需要 demux，`pymp4` 依赖旧 Construct，Bento4 是额外二进制；都不能证明在云盘文件上保留「只读 moov/stss/stts、避免整片流量」的约束。 |
| `mp4repair.py` 重建缺失的 `ctts`，新头存成边车 | `ffmpeg -c copy` 重封装、`untrunc`、Bento4 `mp4edit` | ffmpeg 的 h264 解复用器拿不回显示顺序（实测重封装后仍有 986/2015 帧倒着走），`untrunc` 修的是截断不是缺表，`mp4edit` 只会原地重写整个文件，而网盘上的片子改一个字节就是几 GB 重传。约束是「原文件一个字节不动、播放时拼出合规 MP4」。 |
| `certs.py` 固定项目 CA 与短期叶证书（编码继续调用 OpenSSL） | mkcert、cryptography | mkcert 会接管本机 CA 安装/私钥，不能保持跨设备固定项目 CA；cryptography 只替换证书编码且增加原生依赖，不能删除 Peach 的 Apple 398 天与 CA 生命周期策略。 |
| `migrations.py` SQLite 迁移 | Alembic | Alembic 会引入 SQLAlchemy/Mako/greenlet；现有范围只需顺序 SQL、校验和、备份与 PyInstaller 资源定位，没有 ORM 消费者。 |
| Gofile API 直接 HTTP | 社区 wrapper | 官方没有维护中的 Python SDK；社区 wrapper 只是薄封装，不能绕过 Premium `contents` 权限，也不能减少 Peach 的 Bearer 隔离与媒体规范化。 |
| `netwatch.py`、streaming/segments、sync、versioning/Windows update | 通用替代实现 | 分别是无 PyObjC 的系统通知、FFmpeg/Starlette 上的会话策略、单 writer ledger 规则和 Git/PyInstaller 更新契约；通用替代会保留同量 policy 或扩大依赖。 |

保留自研不是永久豁免：约束改变或候选实现更新时重新跑 POC，不因本表结论跳过外部检索。

## 已定型的产品行为

每条是一次验收留下的判据，一条一句。改这些行为是产品决定，照着再实现一遍是
重复劳动，动手前先确认这里没有写过。README、`docs/HANDOFF.md`、`docs/OPERATIONS.md`
和 ADR 已经写下的不在这里重复，出处用 `git log -S` 查。

- 本地浏览器支持 MP4/WebM/Ogg，其余容器由 `TranscodeService` 按六秒片段缓存成 H.264/AAC MP4，永不改写原媒体；ffprobe 判定可直接复制的流不重编码，其余在 Windows 走 CUDA/NVDEC；29999、30005 实片首段及跳播解码通过。
- 远端 MP4 默认走标准 Range，显式开启的 HLS 使用关键帧对齐片段并在失败时回退 Range。
- 页面共用 SPA、JSON 与 gzip/ETag；侧栏随当前视频集合，已保存在线作品复用关注详情。
- Logo、侧栏「首页」和沉浸模式关闭统一清除分类、搜索与 JAV 筛选，首页默认稳定随机、换批才换种子，再点当前排序回到随机。
- 高亮、竖屏密度、索引骨架已验桌面/390×844，HTTPS 生效；手机命中区 44 px。
- 主题三选一（跟随系统／浅色／深色），只存本机，首帧前由内联脚本写进 `<html>` 的 `data-theme`。
- 同番号的分卷派生（A/B、1/2、CD/Disc/DVD/Part/Vol、「首卷裸名 + 后续卷 `-2`/`-3`」）折叠成一张卡并按时长排除完整版；首页、搜索、资料页网格与版次队列、角标计数共用同一套判定。卷号后面还挂着尾缀时先剥掉组内共有的那一段再认，判据是「组内每个文件名都带、且从分隔符起头」而不是版次词表：按词表拆的话 `1080p` 会被读成 `10` 加 `80p`，同一部片的两个清晰度就成了两卷。
- 分卷卡与版次卡（有码／中字／无码）都不翻卡，悬浮走分段视频预览：各卷、各版次共用同一个番号的封套，翻过去前后两张几乎一样，看着像图卡住了。封面上只有一个计数（「N 卷」或「N 个版本」），叠层封面格垫 `--page`，纸边线条不从模糊衬底的半透明边透进来。分卷详情标题带卷号，因为同一部片各卷的标题、女优、厂牌逐字相同，不写卷号就看不出换了哪一卷。
- 合集翻图复用 `wireStackFlip`：逐张解码后才显示，失败帧不入队，悬停代际隔离异步结果，退出清理计时器。馆藏与关注详情共用原生 `dialog#stage`，浮窗不参与列表排版，关闭保留关注列表 DOM；图片灯箱沿用现有实现。
- 关注卡翻卡去重：`follow_faces` 复用 `community_catalog.fingerprint` 的 dHash，另加 8×8 RGB 色块，因为 dHash 分不开同姿势的穿衣版与 nude 版（生产样本里这类 alt 距离 1～4）。地址相同即同一张；时长都已知且差 ≤1 秒时 dHash ≤6、最大格差 ≤4；时长未知时 dHash ≤2、格差 ≤3。依据是 2026-09-24 生产 2229 个多成员组的实测：同段视频两份格差 ≤1.3，同站同时长的不同 alt 最小 18.7，不同帖子最小 12.7；同一文件两个归档站 308/309 对 ≤6（绝大多数 0），同帖两站 ≤2.7，已知最近的不同版本 6.3。翻卡按画面去重、不分站；封面计数把不同站点的同一画面并成一个媒体，并完只剩一个时写「N 个来源」。文件内容哈希相同的不论同站跨站都算同一个媒体：哈希由各站连接器的 `content_hash` 从已存原始地址解析（kemono／coomer／pawchive 的 `/data/<h0h1>/<h2h3>/<sha256>`，rule34.xxx `/images/<目录>/<md5>`，paheal `r34i.paheal-cdn.net/<h0h1>/<h2h3>/<md5>`），不发请求，没有缩略图的归档站视频也判得出；fanbox、rule34video、f95zone 的文件名是随机 id 或签名令牌，不参与。同站不按画面合并：2026-09-24 实测同站哈希不同、8×8 色块差 <2 的 147 对里混着 4K／8K 两个文件和局部差分（「Tifa」一帖的差分色块差 1.67、2.0，32×32 网格最大格差 26–27），与跨站真重复的 0.7–2.7 交叠。哈希相同即同一个文件，不看 alt／WIP 版本标签。签名由后台线程补进 `generated/posters/follow-faces/`，不进 ledger。
- F95 讨论图片依据已确认的附件身份在采集与读取投影中排除。网盘资源保留，未取得作品预览时显示资源服务图标；不能仅凭 GIF 扩展名过滤作品。
- 普通多女优卡片叠放前 3 个头像、只显示第一位姓名和真实总人数；JAV 小图是整页版式，混入的非番号作品统一为标题、身份、标签三行固定高度。
- JAV 详情持有 `asset.catalog_title`／`original_title` 与官方 Tag 身份，官方标记用常规字重，身份区收齐到同一内容起点。
- JAV 官方封面重探只在面积更大时替换，失败保留原图。
- 播放器按 YouTube 锁定源码对齐控件、状态、图标形变、设置面板动画与悬停提示，倍速五格到 3.0，窄屏按播放器宽度折叠留黑边，沉浸模式按 Shorts 版式，竖屏用居中 9:16 舞台，播放统计两页共用、按传输方式分口径。
- 图片灯箱在本地照片和关注在线图片间复用同一套 Swiper，在线图片只显示来源、合集序号和浏览器实际解析结果；照片标签进入分页图片墙，点开才按原图比例呈现。
- 两处图片墙（资料页照片、关注在线图片）共用大小与固定比例／瀑布流设置，大小由顶部按钮控制，筛选浮层控制布局。关注图片的「仅显示图片」开关独立保存，隐藏卡片文字与信息角标。瀑布流使用 CSS 多栏、`break-inside:avoid` 和图片 `aspect-ratio:auto 1`：懒加载前保留非零高度，加载后使用天然比例；机制见 [MDN aspect-ratio](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/aspect-ratio)。图片 `alt` 保留给读屏，字色透明避免加载时铺满文件名。
- 缓存型资产路由一律先问缓存，不先解析源文件：`media_engine.file_for()` 里那句存在性检查落在 CloudDrive 挂的网盘上，实测一次 137–402 毫秒，一屏几十张缩略图全部命中缓存也要为这几十次往返等好几秒。缩好之后源文件在不在都不改变响应，`/photo-thumb` 因此先问 `photo_service.cached()`。
- 账本路径在 Windows 只做 `abspath`，不 `resolve()`：PikPak 的 A: 是 WinFsp 映射的网络驱动器，实测（2026-09-13）`resolve()` 一条文件路径 7.5 秒、结果是 UNC 形态，对它 stat 14 秒、open 7 秒，同一文件走盘符 1 毫秒；115 的 B: 不受影响。播放时每个请求都要经过 `file_for()`，这一处决定 PikPak 的 stream-plan 与每个 Range 请求是几十秒还是零点几秒。
- 不兼容片源（HEVC、mp3 以外的音轨、非 MP4 容器）一律按 6 秒片重编码给 HLS，账本没记时长或记成负数时用 ffprobe 报的时长切；探测也拿不到才回 Range。分片重编码链与整片转码相同（CUDA 解码加 NVENC、软件解码加 NVENC、libx264），同一分片并发只起一个 FFmpeg，Range 响应按 1 MiB 读文件、客户端一断开就停读。uvicorn 断开后 `send()` 静默返回、Starlette 的 `FileResponse` 不监听断开，`BufferedFileResponse` 因此自己盯 `http.disconnect`；实测（2026-09-13）不盯的话拖一次进度条就留下一个幽灵读者，把 115 上整部片剩下的几 GB 经 CloudDrive 拉完，新位置排在它后面，直到整部片进缓存才能播。
- 有 B 帧却没有 `ctts` 的 MP4 只是时间戳错乱：容器声明的显示时刻其实是解码顺序，浏览器把倒着走的帧全丢掉（6297 实测整片掉两成，PotPlayer 与 FFmpeg 按解码器输出重排所以本地看着正常）。这类片源不重编码，改为重建一份 `moov`（游程编码的 `ctts`、编辑列表补整体平移、`stco`/`co64` 按头长差平移）存成 `transcode_root` 里的 `.mp4hdr` 边车，`/stream` 用「边车的头 + 原文件那段 mdat」拼出虚拟文件按 Range 发。显示顺序由一趟 `ffprobe -ignore_editlist 1 -show_entries frame=pts` 取得：解码器按显示顺序出帧、每帧的 pts 原样来自它那个样本；`pkt_dts` 记的是出帧时最后喂进去的包，不能用。边车没算出来前照旧走 HLS 转码，同一部片后台只算一次，算不出来就不再试。
- 「只采集」对齐全的行（番号已落库、字段有着落或已在候选表、封面在位）不碰磁盘；文件在不在看目录列表，同目录只列一次；候选 CSV 每 5 秒写盘一次、被打断也在收尾写全；扫描从目录列表自带的大小与时间登记文件，不逐个 stat。账本副本、外部来源换桩、媒体挂载只读的实测（2026-09-13）：本地盘 2553 行 2 秒，115 每秒约 65 行、PikPak 约 35 行，进入首行前的准备 0.4 秒；真实运行每条缺资料的行另加联网时间，联网仍是串行。
- 一个控件在两页出现时，选中态怎么表现也归它，不只是外框和材质：首页与资料页的「全部／没看过／稍后看／已标记」共用 `syncViewGlide` 那块滑动玻璃，填充只由玻璃给，两排各自不铺底。找那一排按结构（`#viewPills,.entityviews`）加「此刻量得出宽度」，不按 id：两排在同一份文档里一直都在，另一页开着的时候只是被祖先收起来，写死 id 会一直取到看不见的那一排。
- 统计与口味两页按登录态 Vercel Analytics／Speed Insights 的当前页面重做，排行与数据源共用父网格的引导线。
- 口味页顶部给出结论与可点入口：浏览与 Peach 两侧的共同信号、可探索标签、待补证据的下一步动作。
- 操作回执复用 Toast；按钮以 Spinner 和 `aria-busy` 标明忙态。后台任务显示可恢复进度，断线自动重连。
- 实体的统称由用户在资料页自选：菜单只列这条实体名下已有的写法，选中的提为规范名、换下的留成别名，扁平投影跟着改；换之前先过一层确认弹层并点名两个写法，成功后发一条可撤销的回执；不收自由文本，撞上另一条实体的规范名只报冲突。
- 名字里的括号都走 `split_composite_aliases.py`：自动那拨只认罗马字复合人名，把 r18.dev 打包的 17 条拆成 37 条别名；`--from-review` 那拨按人工判定清掉 9 条不承载名字的尾巴，旧写法留作别名。备份是 2026-09-04 的两份 `ledger.pre-*.db`。剩下的读音、厂牌消歧和角色出处不拆，清单见 BACKLOG 第 29 条。
- 实体链接可安装：`entity_link` 表、`q_entity` 的 `links` 契约、资料页 favicon 与管理页链接管理成套；死链区分「搬走了」和「没了」，`rediscover_entity_links.py` 从站点索引页上溯找新锚。
- 事务所是实体：57 家各有 `/agencies/<名字>` 页，成员、官网、标签与作品都按 `entity_membership` 算，女优页点得进去，搜名字出这家人的片；原文留在 `metadata.agency`。
- 外链圆标与厂牌标识取站点自己声明的资产，宽扁字标不参加小圆标竞选；`/logo` 的 `variant` 分 `icon`、`logo` 与最清晰的 `large`，大图版式和资料页取 `large`，紧凑版式取 `icon`。头像与标识共用 `nativeImageFit`：按屏幕像素密度折算的源尺寸不足框四成时等比居中且不放大，四周同图模糊补底；框短边小于 64 px 不补底，70 px 紧凑圆框适用。加载、图片回落和版式切换均重新度量。
- 关注的作者头像与来源图标是元数据，由 `follow_assets` 取回落在 `generated/follow-assets/` 再经 `/follow-avatar`、`/source-icon` 给页面：地址只从固定表或固定主机拼、字节先认成图再写盘、到期重取失败继续用旧的并退避一小时；保鲜期与 `/link-mark` 共用设置「头像与站点图标刷新」（`web_settings.metadata_refresh_seconds`）。视频与图片不存到本机。官方头像先认 FANBOX，没有时由 `follow_avatar.profile_avatar_tiers` 取名片上的 X 与 Patreon，`follow_assets.largest_image` 按实际像素留最清楚的那张。
- 厂牌标识由契约位 `has_logo` 决定出不出图：没装标识的厂牌一个 `<img>` 都不发，改用首字母底板，不靠 404 摘。标识 198 张随仓库分发（ADR-0026）。
- 关注检查分两阶段：列表阶段落 partial 行，详情补全按 provider 额度只补新行和未补齐行。「补齐过」由连接器的 `ENRICHED_MARK` 声明、判据登记在 `follow_store._ENRICHED_PREDICATES`。
- 存量行重抓：连接器新学到一个字段（图片宽高、封面）后，旧行不会自己补上：常规检查只看第一页，补齐过的行也不再打详情页。做法固定为两步：把 `ENRICHED_MARK` 换成新字段落库后才有的键并登记判据，让旧行判为未补齐；再 `POST /api/follow/check` 发 `{"older":true,"backfill_all":true,"rewind":true,"background":true}`（可加 `"sources":[id,…]` 只走部分来源），从第 1 页逐页走到站点说没有更多，进度读 `GET /api/follow/check`。`backfill_all`、`rewind` 离开 `older` 会被拒收，不进界面；ledger 的回填游标只进不退。这是长跑任务，重启前按 `peach-batch-jobs` 先查。
- 图片的固有宽高只问文件头：`follow_image_dims.probe_image_dims` 发一个 `Range: bytes=0-65535` 请求，`dims_from_header` 认 PNG／GIF／WebP（VP8、VP8L、VP8X）／JPEG（跳过 EXIF 到 SOF）；判据 `positive_dims` 只有这一份，连接器、`backfill_follow_image_dims.py` 与界面回写（`/api/follow/image-dims`）落库前都经它归一，`FollowStore.set_image_dims` 只补空缺。只有图片视图摆成瀑布流，宽高只为图片卡面预留比例，回填脚本每个条目只问卡面那一张；原文件主机拦脚本（pawchive 的 `file.` 子域挂 ddos-guard）时按缩略图量，详情与灯箱里原图取不到也退回缩略图显示。
- 归档站（kemono、coomer、pawchive）的帖子有两张以上图或视频时，`KemonoConnector._media_items` 把它们列进 `media_items`（交付文件排第一、按路径去重），详情轮播与 `/follow-stream?media=N` 按条目自己站点的主机白名单取；存量行按上一条的 `rewind` 重抓补上。
- `/api/related` 用 Tag IDF 加 MMR 排序并缓存；搜索使用 FTS5 trigram，短查询回退 LIKE 并覆盖规范名、别名和检索词，搜索历史在 reader 写入被拒时降级到页面内存。
- 复核页覆盖元数据、创作者标签、Logo、头像、身份、番号目录、FC2 证据和无法识别；抓取与 AI 结果仍是候选，批准后才写真相字段，元数据候选保留 MetaTube 目录证据且不下载 URL。
- 女优与创作者资料页的头像圆框角上有换头像入口：候选来自图库里同名的其他图和这个人取过的每一张图，另外两条路是本机文件与一个 https 地址。每一张取到的图都按内容哈希进候选缓存，被顶下来的那张留在里面，换回去不重新下载。页面只回递服务端自己列出来的 `ref`，图片地址由服务端按索引拼；手填地址是唯一的例外，它过 `http.public_https_url` 那道公网判据。第四条路是这个人自己作品的画面：一部作品占一格，点开之后底图在封面和九宫格九格之间换，框出方形那一块再装上去（`avatar_picker.asset_artwork` 与 `crop`，图仍走 `/avatar-choice`）。`asset:<id>:cover` 这串谁都拼得出来，所以服务端每次都先核对这部作品确实挂在这个人名下，否则就是一个读任意作品封面的口子。裁出来的是新字节，被裁的封面与抽帧原样留在盘上。第五条路是输入番号取封面（`POST /api/avatar-code-cover` → `avatar_picker.code_cover`），番号不必在馆藏里：本机封面目录优先，没有才走重探封面那一份 `jav_cover_fetch.best_cover`，取到的按番号只存对象、不写证据（写了就冒充成这个人取过的图），之后的 `cover:<番号>` 只读本机。封面格子与框选默认框围着 `avatar_picker.cover_focus` 取景：检出脸就是批处理截头像那一块（`avatar_cover_face.face_square`，要封面边车里有脸宽与 `px`，缺的用 `detect_cover_faces.py --redo` 重建），没脸的封套取 `jav_poster_crop` 的正封，版式判据不在前端另抄一份。
- 外部来源 genre 只在 `peach.genre_taxonomy` 投影，日英来源词共用一套既有词表，非内容分类排除、未收录原文回传登记。查表只有 `resolve_genre` 一处，抓取与复核折叠共用它：各写一份的代价是「表里补了这个词，页面上它仍然停在未收录」。r18dev 取 `categories[].name_ja`（DMM 自己那套词），英文只在日文页取不到时才用，因为英文是 r18 再译的一层，`企画` 在非内容表里而它的英文 `Variety` 不在。
- 一件事只留一个标签名：`catalog_rules.RETIRED_TAGS` 存「账本里已有、但不该再用的写法 → 规范名」，`scripts/rename_retired_tags.py --apply --backup` 是写这一步的唯一入口，实体按 `entities.merge_entity` 并、旧名留作别名。绝大多数退役名来自已关停的 Stash 导入（ADR-0021），产地关掉了改一次名就不会再长出来。`pixiv_tag` 不参与：那是作者打的词，改它等于事后修改来源的原话。规范名取馆藏里通行的那个写法，不取词表里先写下的那个：`合集` 3699 条来自文件名，`混合集` 313 条全部来自 Stash。
- 候选是抓取那一刻的产物，抓取口径改了它们不会自己跟上：`peach.stale_candidates` 按「未收录 genre 里有整串 ASCII 且带字母的词」认出还停在英文那一层的候选（日文原词是假名或汉字；字母这一半挡住 `69` 这类两边写法一样的 genre，否则每跑一次摘一次、永远收敛不了），`scripts/drop_stale_genre_candidates.py --apply` 把它们从候选文件摘掉并留备份，下一趟「只采集」按 `_missing_fields` 重抓。重抓只对 r18dev 有用：`k-mib`（77 行）、`aventertainment`、`javdb` 的 genre 在来源页上本来就是英文，2026-09-16 实测 31 份 k-mib 快照全是 `Ahegao`、`Kiss`、`Tiny Girl` 这一套，没有日文写法可换，这几个只能靠表里直接收录英文写法。
- 未收录的 genre 在复核卡上就地收录：`genre_decision`（迁移 0026）存「规范化来源词 → 中文标签」，标签留空即判它不是内容词。这张表是静态词表可变的那一半，`peach.genre_decisions` 只管读写、映射仍全在 `genre_taxonomy.map_genres`；收录一次之后 `extract_peach_fields` 与 `scrape_codes.py`、`harvest_kmib.py`、`fetch_fc2_metadata.py` 都当它是已知词，已经排在队列里的候选由 `web_review._fold_genre_decisions` 当场折进值里（读队列、人工批准、自动落库三处同一个函数）。收录只改词表，落库仍要用户按那张卡上的「通过」。页面给的候选词表是静态表已投影到的那批中文标签，不是账本里全部标签实体，因为后者大半来自文件名，拿它当建议只会把噪声接着抄下去。2026-09-11 之前写下的候选文件只有 `warnings` 里那句中文提示，`genres_in_warning` 按同一处拼出的格式把原文反解回来，旧队列不必先重抓全库才有按钮可点。
- 补抓按番号发行面分流来源，要求来源认得出所查番号、冷却按连败触发且会过期；无码发行站的片与粘连的版次标记也给得出徽章。
- 「只采集」把来源明确答复「没有」（HTTP 404、所有渠道无候选，即 `jav_cover_fetch.NotFound`）的番号按站记进 `state/library-metadata-misses.json`，7 天内不再问；超时与网络故障不记，「重试未完成项」不看这份记忆。文件记着每站的接入时刻，「封面没有」那条的链上有一站晚于它接入就作废，不必等 TTL 也不必手工删文件。已给过待批候选的来源对这一行不再问，没给过的照问（`_answered_sources`）。没有番号的视频（创作者作品、裸文件）只登记本地海报，不列为问题项。相机文件名派生的旧伪番号（`VIDEO-2022`、`IMG-1734`）由 `scripts/clear_camera_filename_codes.py` 清掉，用户或复核写下的番号不碰。
- reader 的 `/review` 通过严格 Peach CA HTTPS 读取 writer 的归一化 JSON 并原子缓存；决定按钮和所有关注写操作仍锁定。
- macOS Ledger 同步在共享根判为 `offline` 时先经 NetFS 挂载 `peach-sync` 再重判，挂载失败才保留离线结果，不弹阻塞认证框。
- 浏览历史增量采集使用 SQLite backup API 与 `browserexport`，也接受 Google Takeout ZIP；原始 URL 与标题只留本机私有目录，聚合候选不写 ledger。
- 首次设置的可选历史引导转到 `/taste?onboarding=1`，继续使用现有读取与导入入口。指南链接按 [Google 导出说明](https://support.google.com/accounts/answer/3024190?hl=zh-Hans) 和 [browserexport](https://github.com/purarue/browserexport) 官方说明核验（2026-09-06）；沿用 `browserexport==0.4.4`，未新增依赖或解析器。
- 数据管理首屏直接复用实际 `cleanupfieldset` 正文和操作条，只有计数等待取数；资源同步与重复文件网盘操作根据 `/api/sources` 已配置来源显示，离线来源保留入口。资源同步的扫描和执行复核均限于已配置 115／PikPak，空文件夹和按目录清理仍支持本地磁盘。

## 必须复用的成熟实现

| 能力 | 复用实现 | Peach 负责 |
|---|---|---|
| 本机文件夹对话框 | Windows 自带 `powershell.exe` 经 `Add-Type` 调 Shell 的 `IFileOpenDialog`（带地址栏的文件夹选择框）；macOS `osascript` 的 `choose folder` | `src/peach/folder_picker.py` 只拼命令、区分取消与失败、一次只开一个；不为一个对话框引入 tkinter 或 GUI 框架 |
| HTTP | 默认复用全项目共用的 `httpx.Client`/transport；FANBOX 公开 `post.info` 按固定证据复用 `curl_cffi==0.16.2` | 来源策略、DTO、脱敏、站点限定、大小上限；不求解机器人质询 |
| RSS/Atom | `feedparser` | 有界抓取、快照、复核、导入 |
| 追更来源接口 | FANBOX 公开帖子 API（详情只使用用户自己的可选 Cookie 与 Firefox 传输特征）、kemono 系公开 JSON API（`Accept: text/css`，站点自述的抓取路径）、rule34.xxx 官方 dapi（需账号 API key）与官方 tag 补全（公开）、Paheal 标签/详情页、Gofile contents API（需 Premium 账号 API token）、f95zone `latest_data.php`、站内搜索（需登录 cookie）、线程页与站内 masked XHR、simpcity 线程页与站内搜索（需登录 cookie；只请求规范地址，不解 DDoS-Guard 质询） | 连接器边界、凭据隔离、多媒体顺序、文件站目标校验、变体与跨站重复判定、候选复核与批准后的 online asset 投影 |
| XenForo 论坛解析 | gallery-dl `v1.32.11` / `2adf2a8e`（GPL-2.0）的 `extractor/xenforo.py` 只作协议证据：登录先查 cookie 再走账号密码、`article[data-content]` 楼层、`.pageNav` 分页、`data-s9e-mediaembed` 嵌入；cyberdrop-dl `5.6.21`（GPL-3.0，2024-09 起按站方要求下线 SimpCity）只作历史参照。两者都是完整下载器，不引入运行时 | f95zone 与 simpcity 共用一份 `_xenforo_posts` / `_xenforo_thread_title` / `_xenforo_search_threads`（站内搜索：先取会话绑定的 `_xfToken`，再 POST `/search/search`，按标题命中并带回版块标签）；Peach 自己负责 cookie 只发回来源站、末页由分页导航自算（HTTPX 跟随重定向会丢显式 Cookie）、纯讨论楼层过滤与 release 语义。gallery-dl 把 simpcity 登录 cookie 名写死为 `ogaddgmetaprof_user`，而站点前缀已轮换为 `yMziCv8BrCZz1o7_`，所以 Peach 不认 cookie 名、只透传整条 Cookie 头 |
| 文件系统事件 | `watchdog==6.0.0`（Apache-2.0），只订阅 `local` 来源的根；网盘挂载不订阅，递归 watcher 在网络挂载上就是轮询。CloudDrive2 的 webhook 请求形态与「云端路径不进 pathlib」取自 `sqzw-x/amane`（GPL，只借设计，见 `docs/reference-snapshots/amane-watcher.md`） | `src/peach/push_discovery.py` 负责去抖、大小稳定的写完判定、前缀表映射、共享密钥与来源校验；登记本身调 `scan.ingest_path`，与全量扫描同一条 upsert（ADR-0041） |
| HTML 适配器 | Beautiful Soup 或 selectolax | 来源专用选择器和来源记录 |
| 位图 | Pillow | 头像/Logo 质量和来源策略 |
| SVG 光栅化 | `resvg-py==0.5.0`（resvg，MPL-2.0 绑定） | 只用于把站点自己的矢量图标转成位图再交给 Pillow。2026-09-02 实测 threads 的成品 app 图标只以 SVG 形式提供，不光栅化就只能退回位图 favicon。选它而不是 cairosvg：后者在 Windows 上要另装 cairo 原生库，前者是 abi3 轮子，win_amd64 / macosx_11_0_arm64 / macosx_10_12_x86_64 都有官方预编译，两个平台都不必装系统依赖。候选发现、内容比例判定、缓存与失败回退仍在 Peach。厂牌矢量标识的方形归一只在这里借一张探针：`images.bake_square_vector` 用标准库 ElementTree 包一层外层 SVG，产物仍是矢量，栅格化只用来数像素、判该配白底还是深底。 |
| 搜索 | SQLite FTS5 | 索引字段、排序、profile 感知筛选 |
| 相关推荐 | OpenAver `dca4c0c368ea0c2db9cf15e48977de2fc75e7077` 的 Tag IDF + 系列／片商／出演者规则只作固定算法参考（MIT） | 独立实现规范实体评分、MMR 多样性、稳定 seed、解释原因与负反馈边界；不复制上游 UI／源码 |
| 女优姓名对照 | `li-peifeng/Jav-Actors-Mapping` 的固定 revision，仅作私有输入（仓库未声明许可证，不随 Peach 分发） | 精确匹配、冲突复核、别名、来源与真实 ledger 写入 |
| 女优头像候选 | Gfriends 的 GitHub raw 索引与单张媒体（只作外部 Provider，不克隆图库）；r18.dev 人物对象给出的 DMM 官方 `actjpgs` 缩略图只作精确身份绑定的首次头像 | 名字链、质量档位、格式/尺寸/SHA-256 门槛、候选缓存、provenance、健康统计和人工复核；首次头像只在人物主名精确一致、实体已连到同一资产且没有在位头像时安装，不进入高清候选排序 |
| Gfriends 索引读法 | `src/peach/gfriends.py` | 页面与批处理共用这一份：`Filetree.json` 解析、名字链匹配、`quality_key` 排序、raw 地址拼接与本地缓存的保鲜期。**目录前缀是来源优先级，不是清晰度**：上游 README 写成「质量升序」，逐个来源核下来是小而精在前（`0-` 网友投稿、`1-`～`8-` 写真机构与片商官方、`8-` 往后是收录上万但原图两三百像素的大型数据库），所以排第一的是「最该先试的一张」，不是「最好看的一张」；`AI-Fix-` 前缀是上游自己做的放大与去水印，去掉前缀取未处理原件 |
| 「这个地址能不能让 Peach 替人去取」 | `src/peach/http.py` 的 `public_https_url` + `resolves_publicly` | 追更的图片代理与换头像的手填地址共用同一道判据：必须 https、必须公网域名、不收 IP 字面量与用户信息、解析出来的每一个地址都要 `is_global`。Peach 跑在用户自己的机器上，能访问路由器后台、NAS 和本机各个端口，「你给地址我去下」不设边界就是一个替人发请求的跳板 |
| 头像写入 | `src/peach/avatar_provider.install_entity_avatar` | 采集脚本、复核页与换头像共用这一份：`.img` 经临时文件原子替换，`.ct`、`.provenance.json` 与人脸 `.face.json` 四件套一起换。检不出脸要删 sidecar 而不是留着，因为上一张图的脸框会被页面拿去给这一张取景，放大到一个空位置上，而这在界面上与「本来就该这么显示」看不出区别 |
| 厂牌 Logo 候选 | 厂牌官网确认的社交 handle → unavatar URL 解析 → 平台 CDN 单图 | handle 归属、内容缓存、方形归一、精确/感知哈希、provenance、健康统计与变化复核 |
| 厂牌字标名录 | 发行商与发行平台自己的厂牌名录，入口登记在 `harvest_maker_directories.DIRECTORIES`：MGStage `/ppv/makers.php` 十一页 351 家、Prestige `/api/maker` 11 家、KMP `/label` 42 家（大半是 SVG）；另有 jae.tokyo 展会名录 20 家 | slug↔账本对账（四路判据、空罗马字形当不可比）、按形状分三张指定表（方标原样装大位、字标烤方两位共用、方标只管小位）、改地址后靠 provenance 边车重新收人、复核 CSV 与安装闸门。存入口不存图片地址：KMP 的文件名带时间戳，厂牌换一次标识地址就变。不推导 URL、不猜名字：名录给什么用什么 |
| JAV 元数据查询 | 每个站只有一个归属（ADR-0048）：自写解析器持有 r18.dev、DMM／FANZA、一本道、FC2、fc2cmadb、FC2PPV-DB、JAVten、JavArchive、AVBase、JavBus、javdb，片商官网与转载站经 amane 桥（ADR-0043、ADR-0044）；MetaTube SDK `6a5e6128c725187aeaf921d48ed7d9cd9f30671b`（Apache-2.0）只作来源身份与丰富字段模型参考；DMM 的 GraphQL 接口地址、`ppvContent` 与 `legacySearchPPV` 两条查询的取法参照 OpenAver（MIT）`core/scrapers/dmm.py`，cid 匹配与身份核对是 Peach 自己的（ADR-0059） | 只发送规范番号；Peach 管来源链（`metadata_routes`）、`provider_id`／`content_id`、逐字段优先级、原始证据、丰富目录证据、健康统计、候选复核与批准后的 ledger 投影。amane 的 POC 判据、字段缺口与三条路线的前提见 `docs/reference-snapshots/amane-crawlers-poc.md`，采纳结果见下一行 |
| Javinizer-Go 历史快照 | `sources/metadata/javinizer-go/<番号>/<来源>.json`，由 Javinizer-Go v1.5.x（MIT，`dd56998328d078c9baf68ff4fde2e6fcaa2a691a`）在 2026-09 之前取回；二进制与快照留在磁盘，不再有调用路径（ADR-0044） | 只作离线证据：封面层读它的 `cover_url` 与 `content_id`，别名解析读企划名义，账本里 `javinizer:<站>:<字段>` 的 provenance 按 `metadata_policy.HISTORICAL_SOURCES` 认级别。`scrape_codes` 写进同一目录的新快照 `provider` 记解析器名、`provider_version` 记 Peach 版本 |
| amane 刮削站点（官方档 makers、prestige、faleno、dahlia、mgstage；转载站 fc2club、freejavbt、airav、avsox） | amane `79ecfa763cc786318e1964a3d7f4e244a7d5c96d`（v0.16.1，GPL-3.0），经 `tools/amane-bridge/` 薄桥子进程接入（ADR-0043、ADR-0048；`makers` 是 amane 的 `official` 模块）：独立 `pyproject.toml`／`uv.lock` 钉 sha，venv 建在 `<数据根>/tools/amane-bridge/.venv`，桥只用 `amane.crawlers.sites.<站>` 与 `amane.net.*`，不碰 `aggregate` | 许可义务：amane 为 GPL-3.0，Peach 为 AGPL-3.0-or-later，两者以进程边界相接；仓库与分发件只含清单、锁与桥脚本（Peach 自己的文件），amane 源码由用户机器上的 uv 按锁下载，不随 Peach 分发；清单、桥脚本与设置页都写明上游地址与许可。升级是人做的：改 sha → `uv lock --project tools/amane-bridge` → 读上游 diff 核字段语义 → 同批改 `peach.metadata_amane.AMANE_REASONS`／`SITE_CONFIGS` 与本行。已知性质：上游 `WebClient` 以 `verify=False` 发请求，只取公开页面、不带凭据；`amane.crawlers` 包 `__init__` 连带 SQLAlchemy，每次子进程约 0.6～1 秒 import。Peach 管来源链位置、身份核对、失败分档与冷却、候选与结算 |
| 已确认厂牌的目录归位 | Javinizer-Go v1.5.2 organizer（MIT）只作冲突预检、模板化目录和回滚边界的协议参考，不调用它，不让它持有 Peach ledger | `rehome_unknown_jav.py` 只消费人工确认映射；先出逐文件 CSV，拒绝扁平化重名与厂牌冲突，SQLite 备份后移动文件并同步 Peach 路径／实体 provenance |
| FC2 目录元数据与跨号证据 | 已缓存的 fc2cmadb Inertia `article`／评论收获；Javinizer-Go v1.5.2 的 FC2 解析器（MIT）只作官方商品页字段边界的协议参考 | 2026-08-31 登录态实测旧文章仍提供标题、原始标签、日期、时长、卖家、FC2 CDN 封面与 `comments`；Peach 只把无歧义标签翻译成现有词表，标题／标签进入 `/review`，实测 `w1200` 封面经尺寸与解码门槛落生成产物；稳定 pair、合集/分片保护、hash/时长/尺寸佐证、库外 evidence、健康统计和人工复核仍由 Peach 管，不依赖 FC2-Leak-Detector/JavSP，也不把镜像候选直写 ledger |
| 缺索引 MP4 重建 | untrunc（anthwlock，GPL-2.0，用户自行解压到 `<数据根>/tools/untrunc/`，也认 `PEACH_UNTRUNC` 与 PATH），按 `-n -s -dst` 借一部同编码器的完整片子当参照切 `mdat`；不随 Peach 分发，「运行信息」给下载入口 | `src/peach/mp4recover.py` 挑参照（同目录按文件名挨得最近的先试，最多 4 部）、验收（解码错误不超过 3 行、音视频时长差不超过 5%）、换回原路径并把坏原件改名成同目录的 `.文件名.peach-original` 留着；缺整个 `moov` 的片子在任何播放器里都打不开，所以结果替换原文件，不像缺 `ctts` 那样另存头。2026-09-23 实测 115 上 5 部：同日期、同分辨率的邻居参照能整部或 73%～100% 切回，参照分辨率不对时每帧报宏块错误，找不到同编码参数的参照就修不了 |
| 媒体探测/转码 | Peach 管理的 FFmpeg/ffprobe；Windows 已实测 FFmpeg 9.0.1 full build 的 CUDA/NVDEC、`scale_cuda` 与 NVENC，现有二进制启用 GPL/version3。CI 复用 `FedericoCarboni/setup-ffmpeg@v3`（MIT）并固定 FFmpeg 9.0.1；Gyan 官方 x64 full build 的 7z 为 165,742,351 字节，Python 3.12/3.14 的 Windows runner 共用同一版本。默认 `release` 会访问 Gyan 易失的 `release-version` 端点，2026-09-19 实测返回空响应并让两组 Windows 测试在执行前失败；固定版本改从 GyanD/codexffmpeg 的精确 GitHub release 资产下载。 | 任务策略和 Media Engine 编排：容器与内部编码分别检查，MP4/M4V 的 H.264 8-bit 与兼容音轨可直出；其余容器中的 H.264 8-bit 优先只换 MP4 封装；其余 Windows 输入依次尝试 CUDA→H.264 NVENC、软件解码→NVENC、原 `libx264` 回退，macOS 保持封装复制或软件转码。2026-09-05 的 JBS-023 原片为 MPEG-4 Part 2/AAC，12 秒样本经既有 FFmpeg 流程在 2.42 秒输出 H.264/AAC 并通过画面解码；兼容性依据为 MDN Web video codec guide 与 ffprobe 官方 stream 文档。真实 CloudDrive POC 中，H.264/AAC 的 30 秒片段封装耗时 0.64 秒，1080p HEVC 的 30 秒 CUDA/NVENC 转码耗时 1.60 秒；不新增 Python 依赖，不改生产、原媒体或 ledger。 |
| HTML5/HLS/DASH 播放 | Video.js 8.24.1 + 内置 VHS（Apache-2.0，本地固定版本） | 流方案、授权、稳定时长、回退顺序和统计面板；详情不兼容片源复用 HlsSegmentService 与 FFmpeg 按六秒编码 H.264/AAC，独立缓存、绝对时间轴及会话取消；JBS-023 首段 0.67 秒、十分钟处 1.96 秒，YRH-097 首段 1.01 秒，无整片预转码 |
| 播放器设置与影院布局 | Video.js 8.24.1 的 `playbackRate`、既有 QualityLevel、原生 tooltip 与控制栏插槽；YouTube `e937390a` 实际 DOM／CSS／JS 提供可复现的几何、状态、动画和图形证据 | Peach 在现有 DOM 上组合氛围模式、播放速度、真实清晰度和影院模式，并复用 59 px 两排控制栏、40→111 px 横向音量、4→6 px 进度动画、右侧共享胶囊、整行悬停的 274 px 设置菜单和视口级全屏；普通视图 `contain` 保全片源，全屏用 `cover` 铺满视口，接受非等比例片源的边缘裁切。全屏命中同时使用 Video.js／原生类和 `isFullscreen()` 同步的 `data-peach-fullscreen`，并覆盖 `body.vjs-full-window` 回退，不能再靠单个 CSS 类推断运行态；标准、WebKit、Gecko 等浏览器专用伪类必须放进 forgiving `:is(...)` 或拆成独立规则，不能在普通 selector list 混写后让某浏览器因未知伪类废掉整组声明。要求图形精准的设置项、radio 选中勾、菜单箭头、中央 bezel 与 loading 只 vendoring 当前锁定版本的 SVG path／spinner 结构，音量 hover 与滑轨中心沿用上游外层伪元素和 50% 几何，tooltip 仅补 Peach 两排控制栏需要的显式层级与越界可见；不复制播放器控制逻辑、不迁移到 Video.js 10 Menu，也不引入重复现有质量选择的插件 |
| 播放器时刻预览 | Video.js 原生进度控件 + Peach 自己的 `/timeline?id=&s=`（10×10 接触印相），取不到时退到既有 `/poster?id=&c=0…8` 九宫格切片 | 时间轴图由 `peach.timeline_sheets` 按每 10 或 30 秒一帧预先铺好，只覆盖 `location='local'`：网盘上的每抽一帧都要回源拉一次，实测 115 单文件抽九帧约 285 MB，两万部按每 10 秒一帧算流量以 TB 计。没铺到的片子和在线视频退回九宫格，那九格是全片九等分、只给近似时刻。抽帧与拼图命令与九宫格脚本共用 `peach.frame_capture`，不另起一份裸 ffmpeg 调用。`videojs-vtt-thumbnails` 与 `videojs-sprite-thumbnails` 都要求另建 sprite/VTT 契约并多一层运行时依赖，而格子位置的换算在 Peach 这边是一行整除，所以不引入 |
| 外挂字幕 sidecar | 浏览器原生 `TextTrack` 与 [WebVTT 规范](https://www.w3.org/TR/webvtt1/)；配对判据复用 `catalog_rules` 的 `VERSION_TAIL_TOKENS` 与 `release_code_from_filename`。两份本机参考项目只作行为证据：sakuramediabe `src/service/transfers/imports/import_service.py` 加 `src/common/movie_numbers.py` 的 `subtitle_matches_movie_number`（限同目录、纯番号匹配、不回退到同名匹配），NeoAVDC `src/main/media/organizeMedia.ts` 加 `src/main/number/parseNumber.ts` 的 `SUBTITLE_EXTS`／`isSubtitleFile`（`.srt .ass .sub .vtt .ssa`，按视频主名前缀跟随）。Peach 的三条判据正是这两者的并集加顺序 | `subtitles.py` 只做三件事：同目录配对（exact／suffix／code／orphan，跨目录一律不算）、`asset_subtitle` 幂等登记、srt/ass/ssa → WebVTT。转换不外包：`pysubs2` 会为一件几十行的事引入运行时依赖，而已经在管的 FFmpeg 要为每次取字幕起一个子进程、失败只给退出码，说不出「这份字幕的编码认不出来」，而编码恰是这个库最常踩的一项（GBK／Big5／Shift_JIS 各有）。`gb18030` 明确不用：它几乎吞下任何字节，放进来就再也报不出「认不出编码」。内封字幕轨不在这条里，现有 `probe.py` 只取 `v:0`，没有任何流信息落库 |
| 分卷文件命名 | [Plex 官方命名](https://support.plex.tv/articles/naming-and-organizing-your-movie-media-files/)的 `cd/disc/disk/dvd/part/pt + 数字` 与 [Kodi 官方 File Stacking](https://kodi.wiki/view/File_stacking)只作行为证据；运行时复用当前树的 `part_marker`，不新增扫描器依赖 | 兼容馆藏已有的裸数字和 A–H 后缀；仅连续、唯一标记自动合卡，保留每个 asset 和播放会话，不拼接或改写媒体 |
| 照片灯箱轮播 | Swiper 14.2.0（MIT，本地固定版本，按需加载 CSS／JS）的 Thumbs / Keyboard / Zoom 模块 | 构造轮播前必须同时等到样式与脚本就绪，并保留 scoped 的单 slide 结构样式防止首载竞态重叠；Swiper 管轮播、键盘、缩放变换与缩略图，Peach 管图集来源与顺序、当前缩略图居中、相对原图百分比、适应窗口／原大小语义、缩略图缓存与计费口径。图片墙本身是 CSS 网格，不经过 Swiper。 |
| 导航排序 | 浏览器原生 HTML Drag and Drop | 桌面鼠标直接拖动、落点提示、上下移动按钮作为键盘与触屏回退、`localStorage` 持久化；不为单列排序引入额外运行时依赖 |
| 单列拖动排序 | `web/js/ui-components.js` 的 `wireDragReorder()` | 侧栏顺序与播放列表队列共用这一份：`dragstart` 标记被拖行，`dragover` 按指针落在行的上半还是下半给出落点线，`drop` 把整份新顺序交给调用方落库。落点线、抓手和键盘焦点样式都在共用件里，每加一处可拖列表不再各写一份 |
| 图标 | 固定版本的本地 Lucide 子集；Health Icons 24 px outline（CC0）用于领域图标；Phosphor regular 填充字形（MIT）只用在描边说不清的地方（字母表 Aa、播放列表） | 标签、状态和交互设计 |
| 资源文本中间省略 | Vercel Geist `MiddleTruncate` 行为契约 + 浏览器原生 `ResizeObserver`、`Intl.Segmenter`、Canvas 测量 | 文件名、路径、URL、ID 等资源标识用 `data-middle-truncate`；标题、说明、人名、标签等语义文本保留末尾省略；页面源测试登记全部末尾省略选择器，新增截断未先分类会失败 |
| 定时轮询 | APScheduler 3.11.3（MIT，固定稳定版；3.x `BackgroundScheduler` / interval trigger） | 只在 ledger writer 启动、持久频率、首次延迟、单实例、手动/自动互斥、运行状态与来源错误汇总 |
| 本地文件事件 | watchdog + 定期对账 | 媒体身份和漏报修复 |
| 过渡期元数据/媒体 | Stash GraphQL、CommunityScrapers、Stash 任务系统 | 适配、对账、退出门槛 |
| 局域网发现 | Python zeroconf | 服务生命周期和真实客户端验收 |
| 生成产物跨机同步 | Syncthing 2.1.x，Windows send-only → Mac receive-only | 目录划分、忽略规则、方向固定与「Mac 不发布正式产物」的边界 |
| Windows 托盘 | pystray 0.19.5（LGPLv3）、Pillow、Win32 Per-Monitor V2 DPI | Peach 服务归属、后台更新检查、菜单动作、品牌图标 |
| Windows 文件夹选择与证书子进程 | 系统 IFileOpenDialog、SetThreadDpiAwarenessContext（Windows 10+）、Python 标准库 CREATE_NO_WINDOW | 选择器所在 PowerShell STA 线程设置 Per-Monitor V2 并恢复原上下文；OpenSSL 保留退出码与错误输出。没有新增依赖；托盘的进程 DPI 不会传给选择器子进程。 |
| macOS 菜单栏 | `pyobjc-framework-Cocoa==12.2.2`（MIT）提供 AppKit / PyObjCTools / objc | 附件应用策略、18 pt template 图、服务归属与菜单动作 |
| 人脸取景 | `opencv-python-headless==5.0.0.93`（Apache-2.0）的 `cv2.FaceDetectorYN` + opencv_zoo 定版模型 `face_detection_yunet_2023mar.onnx`（sha256 `8f2383e4…52fa4`，232 KB，放 `peach-data/tools/yunet/`，不进 Git）；MetaTube SDK `6a5e6128c725187aeaf921d48ed7d9cd9f30671b` 的主脸聚类只作算法参考 | 头像／封面离线脚本共用 `peach.face_detect`，主脸选择、归一化焦点与 sidecar。**一张图检三个尺度，分数取中位数**：YuNet 是定尺寸输入，同一张脸在不同送检长边上的分数能差出一倍：题材 `xenoblade` 那张竖图里的正脸在长边 320 上 0.63、640 上 0.70、1280 上只剩 0.27，同图罩在躯干的误检反过来（320 上没有，1280 上 0.65），只在最大那一档检一次就把取景判给了躯干。`detect` 按 320/640/1280 各检一次（只往下缩），重叠 0.35 以上的框算同一张脸的几次读数，框取读数最高那次、分取中位数，某一档认不出记 0（三档缩成同一尺寸时只检一次，不补 0）。误检多半只在一个尺度上高：封面 `SRN-104` 罩住整个身体的框读 0.85/0.31/0.49，同图真脸 0.66/0.89/0.88。代价是检出耗时 1.66 倍（20 张封面 0.42 秒）、1204 张本地样本里 60 张换了取景，其中 9 张退回「没有脸」、4 张从「没有脸」变成认得出。**主脸不是最大的那张**：`main_face` 先筛掉分数落后最好那张 0.1 以上的框，再在剩下的里取最大。只按面积挑会被「大而勉强」的误检抢走（`performer-8218` 那张 600×1000 人像上，罩在胸口的框 0.427×0.313 分 0.798 压过 0.202×0.170 分 0.928 的脸，圆头像于是取景在胸口）；只按分数挑会被背景里那张小而清晰的脸抢走（`performer-8540` 右上角 0.066×0.052 分 0.925）。954 张封面按这条重算，47 张换了主脸，每一张的新框分数都更高（`451HHH-029` 从画面中缝的 0.813 换到左上主体的 0.925）。**Haar 级联已不可用**：OpenCV 5 把它移出了 Python wheel（`cv2.CascadeClassifier` 不存在、`cv2/data/` 只剩 `__init__.py`），两个脚本一直抛 AttributeError，954 张封面 0 个 sidecar，取景从未生效。YuNet 同属 OpenCV，不是替代品，换掉的只是检出器这一层：Haar 在 512 张头像上检出 313、46 张封面上检出 24，YuNet 首轮 12 张封面检出 11，且带置信度，不必再靠位置规则丢假阳性。Pigo v1.4.6（MIT）512 张检出 488，但存在无脸误报且无 Python 部署优势，仍不引入。 |
| 人脸比对 | `opencv-python-headless==5.0.0.93`（Apache-2.0）的 `cv2.FaceRecognizerSF` + opencv_zoo 定版模型 `face_recognition_sface_2021dec.onnx`（sha256 `0ba9fbfa…34e79`，与 LFS 指针的 oid 一致，37 MB，放 `peach-data/tools/sface/`，不进 Git） | `peach.face_match` 提特征、算余弦，阈值用 SFace 官方的 0.363；补头像后继在图库同名多张时拿候选与单人封面截到的脸比（ADR-0056）。检脸与关键点复用 `peach.face_detect` 的 YuNet，取模型走同一条 `fetch_model`。当前树与 Git 历史里没有人脸识别实现；不引入 `face_recognition`／dlib（要编译、体积大）和 InsightFace（模型许可限非商用、需 onnxruntime），SFace 在已钉的 OpenCV 里现成可用，不新增依赖。2026-09-24 本库只读实测：认定的 14 位分数在 0.365～0.692；同名多人的 `ゆうか`、`まどか`、`えりか` 三位共 42 张候选，最高 0.293，没有一张过线。FC2 封面的脸常被贴纸、口罩或马赛克挡住，YuNet 照样给 0.85 以上的分，这类参照上的分数可信度低一截。 |
| 头像水印检出 | `opencv-python-headless==5.0.0.93`（Apache-2.0）的 `cv2.dnn.TextDetectionModel_DB` + opencv_zoo 定版模型 `text_detection_en_ppocrv3_2023may.onnx`（sha256 `03f550c6…66587`，2.4 MB，放 `peach-data/tools/ppocr/`，不进 Git） | `peach.avatar_watermark` 检出站点水印，`scripts/scrub_avatar_watermarks.py` 复核与移除。**先自己写过一版启发式，实测不够用**：MSER 加几何、字高一致与明暗同向过滤，干净图上假阳性能压到零，那 14 张里总共抓到 1 处水印，半透明的一个字符都抓不到，而头发和织物纹理产出的字符状连通块跟真文字在单张图上无从分辨。换 DB 模型后同一批图 6 处实心水印全中、零假阳性。**门槛按实测数据定**：真水印分数几乎都在 0.97 以上（`PRIVATE.com` 0.994、`TEAMSKEET.COM` 0.986），衣服花纹上的假阳性 0.71 到 0.81，`MIN_SCORE` 卡在两群中间的 0.9；再加框宽占图宽 ≥ 4% 挡掉碎块，加「框要整体落在距边 15% 带内」的位置先验挡掉裙子花纹和脸上的框。**半透明水印它给不出框**（`NUBILES.NET`、`MATTIEDOLL.DEVIANTART.COM`），这一层补不上，所以流程是半自动的：检出是候选，人看标注图确认，漏的自己补框。移除优先裁边不 inpaint：620 张实测 16 张纯裁切、1 张裁切加修补、6 张只能修补，裁切不伪造任何像素。 |
| 正封取景 | `opencv-python-headless==5.0.0.93`（Apache-2.0）的 `cv2.Sobel` 求列向梯度；NeoAVDC `c7a430c64013c97a0213cd8a57e2ff5696793a86`（MIT）与 sakuramediabe `7e40ef87c7518c1dc2b6c8c299170ad7395fec6d`（GPL-3.0，只作算法边界参考，不引入代码与运行时）的封套几何实测值 | `peach.jav_poster_crop` 给出正封那一块的取景框（折痕列到源图右下角、满高），`scripts/poster_crop_boxes.py` 批量写边车。**产物是坐标不是图片**：封面原样保存（`jav_cover_fetch` 的约定），框写进 `<番号>.poster.json`，和人脸取景的 `.face.json` 同目录、同命名风格。**判据是正封的形状，不是折痕在全宽里的位置**：正封是印刷面，DVD 135×190mm 宽高比 0.711，本机实测 1% 分位 0.684、中位 0.704、99% 分位 0.725；折痕的相对位置则随背面留白与书脊厚度飘。所以只在「切出来的正封宽高比落在 0.68～0.76」那几十列里找峭壁，再加一道「峰值要到全图最强列梯度的 35%」挡住平缓横图。**窗里够强的边不止一条时按形状挑，不按谁更强**：书脊有左右两条边，厚一点的书脊两条都落在这个窗口里，而左边那条常常更强，因为它挨着封底的留白，右边那条挨着正封的画面，按最强的切会把整条书脊留在框里。所以强度到窗内最强边七成的都算候选，相邻列归并成一条边，再取切出来的正封最贴近 0.704 的那条；本机 67 张因此改判（ABP-968 书脊 39 列，左缘 0.718、右缘 0.703）。**峰是斜坡最陡的那一列，不是斜坡尽头**：折痕在梯度上是一道有宽度的斜坡，书脊最后一两列还压在峰的右边，按峰切会在正封左缘留下一条竖线，所以选定之后再往右走到梯度落回窗内中位数为止，最多走源图宽的 1%；本机实测位移中位 2 列、90% 分位 3 列，切出来的正封宽高比 0.667～0.749、中位 0.704。**两份外部量得的数只作参照，不作判据**：NeoAVDC 量 DMM/JavBus 得出折痕在全宽约 52.5%，与本机结果对得上，但它是结果，拿它反过来卡位置，封套一宽一窄就落空；sakuramediabe 的「左右两峰关于中线对称」会误收，KBI-036 的背面分栏线与正封内部一道强边恰好关于中线对称，按它切会切进正封 52 像素、削掉一截大标题。**本机 1014 张封面实测**：命中折痕 637 张，回退先验 46 张，不裁 331 张（韩国 MIB 90、FC2 130、16:9 官方剧照 111）。**16:9 只认居中拼图**：PASN 与 MOON FORCE 的封面是「剧照 | 正封 | 剧照」拼成的一张，正封宽 0.704 倍高、正好居中；认它靠拼接缝覆盖的行数（至少 75%），不靠列梯度强弱，本机 149 张 16:9 里命中 3 张，其余最高 0.61。欧美片的编号和厂牌番号同形，番号那一关拦不住，靠宽高比这一关拦下。**算不准时人可以自己框**：详情页标题旁那枚裁剪键写的是同一份边车，`method` 记 `manual`、`source` 记 `user:crop`，四条边都可能动（算出来的那几档永远满高贴右缘）。手工框不跟算法版本作废，因为它后面没有算法；封面被更大的那张换掉时按 `px` 对不上作废，和算出来的那几档同一条判据。「恢复默认」是按折痕判据重算一遍，不是还原图片，图从来没变过。 |
| 115 文件清单 | `p115client==0.0.9.6.5.1`（MIT） | 只在显式 SHA-1 对账脚本中安装，Peach 负责 ledger 事务、备份与写入门槛 |
| 智能体用量/配额 | Provider 官方配额接口；T3 Code/CodexBar 提供本地历史 | 任务路由、脱敏、过期快照标记 |
| 视频出处/片尾证据 | 现有 FFmpeg 抽帧 + Windows.Media.Ocr WinRT Provider（Windows PowerShell 5.1 固定适配器） | 有界首尾采样、缓存、来源/Full version 分类、健康统计与人工复核 |
| 参考产品行为 | 当前线上交互 + 有版本的公开 DOM/CSS/JS；取不到源码时用精确截图测量 | 证据登记、无障碍、Peach 差异、回归检查 |
| 浏览器历史解析 | `browserexport==0.4.4`（已替换 `taste_history.py` 自写的 Chrome/Firefox/Zen/Safari SQLite 解析） | Python 3.14 依赖解析通过；POC 在本机 7 个 Chrome/Firefox/Zen profile 上与 Peach 逐库计数完全一致，macOS 的 Safari／Zen／Firefox／Chrome 路径发现有独立测试。首个消费者是 `/taste` 的本机读取与导出导入；Peach 保留 SQLite backup、Takeout、私有原始存储、域名分析和 candidate 生成，并在 Windows 自己关闭只读连接以避开依赖的文件句柄滞留。跨主机同步不由该依赖提供，仍须显式导出、传输和按来源去重合并。 |
| 批处理进程锁 | 候选 `portalocker==4.3.0` 的 `PidFileLock`；生产仍是 `src/peach/jobs.py::PidFileLock` | Python 3.14 解析通过，现成覆盖 PID 写入、锁持有者、原子替换、陈旧文件与释放清理。替换时 Peach 只保留任务归属和错误文案映射；落地前不算已进入生产的依赖。 |
| Rule34Video 媒体页解析 | `yt-dlp==2026.8.19`（已部分替换自写解析） | 对真实视频 4533145 无写入提取成功，取得 4 个格式、31 个标签、缩略图与时间。Peach 仍负责作者分页、合集/超多 model 排除、来源分组和跨站去重。 |
| Rule34.xxx / Paheal 高清封面 | 固定参考 gallery-dl `86047cf67a12bdb6ff1085774f8ad9fc347e8da9`（GPL-2.0，只作协议行为证据，不引入运行时）；运行时复用现有 FFmpeg | booru URL 明确支持 `sample_url`/`preview_url`/`file_url` 回退，Paheal 抽取器只取得原始 `file_url`。真实 POC 中 Rule34.xxx 历史 preview 为 250×141、同哈希 sample 为 1920×1080；Paheal 页面只有低清 poster/og:image，原视频可生成 1280×720 JPEG。视频缩略图工具 ffmpegthumbnailer 默认取 10% 位置，Peach 不再引入 GPL 运行时；直接复用 FFmpeg `blackframe` 导出的 `lavfi.blackframe.pblack`，在开头 30 秒选第一张黑色像素低于 98% 的帧，并用版本化缓存键淘汰旧黑帧。Peach 继续负责 URL 白名单、同源代理、按需双并发抽帧、缓存与低清失败回退，不新增依赖、不改 ledger。 |
| FANBOX 正文解析 | PixivUtil2 `v20251112` / `e537e96` 的公开正文模型（BSD-2-Clause，只复用数据模型，不引入整套下载器） | Peach 的独立规范化 DTO 已覆盖 image/text/file/article/video/entry、`fileMap`、`embedMap`、`urlEmbedMap` 和旧 HTML 正文，并保留正文顺序、稳定去重、可播放媒体与文件页边界；许可证依据写在实现头部。PixivUtil2 是完整下载器而非可嵌入解析库，因此不引入整套依赖；传输继续固定 `curl_cffi==0.16.2`。真实公开帖 12228983 只读 POC 得到 article、6 图和 Gofile `OS2Qz9`。 |

依赖的第一个消费者及其隔离测试必须在同一改动落地，否则不引入依赖。
Python、npm 与 GitHub Actions 的版本由 `.github/dependabot.yml` 每周检查；固定前端文件由
`package-lock.json` 和 `scripts/vendor_web_dependencies.mjs` 重建并核对来源、许可证与 SHA-256。

## 已删除旧实现与当前继任者

| 已删除/旧名称 | 当前实现 | 规则 |
|---|---|---|
| `rm-web.py` / `rm-web.html` | `src/peach/api.py`、`src/peach/web_contract.py`、`web/index.html` | 不得恢复旧 HTTP server |
| `rm-javlookup.py` | `scripts/scrape_codes.py` | 扩展来源适配器，不再分叉刮削器 |
| `rm-probe.py` | `src/peach/media_probe.py`（入库时探本机与 115）、`scripts/probe.py`（历史、重探与计流量来源） | 探测与失败记 -1 只有 `media_probe` 一份，保留续跑语义 |
| `rm-sheets.py` | `scripts/sheets.py` | 共用 FFmpeg/任务原语，不再新建抽帧管线 |
| `rm-ledger.py`、`scripts/ledger.py` | `peach init`／`peach scan`（`src/peach/cli.py`、`src/peach/scan.py`）+ repository/migrations | 摄取与建库只有 `peach` 一个入口，不放回旧 CLI；Stash 回灌随 ADR-0021 退役 |
| `rm-status.py`、`scripts/status.py` | `peach status`（`src/peach/cli.py`） | 状态命令只读，并且只有一个入口：打包入口转发全部子命令，不再单独发一个脚本 |
| `rm-suggest.py`、`scripts/suggest.py` + `moods.json` | `scripts/taste_history.py` + 馆藏页筛选 | 排序与心情筛选留在应用端口，不放回旧 CLI |
| 各写库脚本私有的 `--database`／`--backup-dir`、自写 backup 与只读连接 | `src/peach/scripting.py`（`open_readonly`、`add_ledger_write_args`、`open_for_write`、`counts_of`、`verify_after_write`、`USER_AGENT`、`RateLimiter`） | 真实写入的参数只有 `--db`／`--apply`／`--backup` 一套；`--apply` 必须同时给 `--backup`，备份走 `peach.migrations.sqlite_backup`，脚本不再各写一份 |
| `rm-trafficwatch.py` | `scripts/traffic_watch.py` | 只停止任务拥有的进程树 |
| `rm-sha1.py` | `scripts/sync_sha1_115.py` | 复用 Provider 哈希，不盲目重算网盘媒体 |
| `import_performer_portraits.py`（原 `agent/claude/performer-portraits`） | `scripts/audit_performer_portraits.py` + `scripts/localize_performer_names.py` | 一次性导入已执行完并记在 STATUS；后继只产 CSV，不写头像文件 |
| `normalize_code_suffix.py`（原 `agent/claude/code-suffix`） | `catalog_rules.jav_display_metadata` + `scripts/audit_jav_display.py` + `scripts/audit_code_creators.py` | 紧凑番号只随发行证据恢复；版本后缀投影为徽章，原始文件身份不丢失；全库审计只读 |
| `dedupe_performer_creator.py`（原 `agent/claude/dedupe-identity`） | `scripts/merge_duplicate_identities.py` | 后继的判据已扩到跨 kind、同 kind 与真子集三轮，旧脚本判据更窄 |

## 当前替换队列

本地库导入复用 Kodi/Jellyfin NFO 协议（2026-09-06 核对 [Kodi](https://kodi.wiki/view/NFO_files/Movies)、[Jellyfin](https://jellyfin.org/docs/general/server/metadata/nfo/)），XML 解析复用 Python 3.12+ 标准库 ElementTree（PSF，无新增依赖），图片复用项目固定版 Pillow。只适配影片、单集与音乐视频的字段；整剧、音乐专辑、播放记录及远端图片引用保留在原文件，不作为影片资料套用。拒绝 DTD、超大输入与越目录图片引用。同名边车优先，`movie.nfo` 和通用海报只用于单影片目录；正片和图片同属一组连号（`(1).mp4` 配 `(1).jpg`…`(119).jpg`）时同名图是图集的一张，不当海报。真实 JavBoss NFO 与同番号 R18 JSON 的只读 POC 已取得：本地保留原标题、演员和词表未收录的自定义标签；已知内容词统一投影为 Peach 中文标签，明确的画质、促销、发行属性与演员编成丢弃。远端能补厂牌、导演、发行商、时长和图片出处；NFO 与远端人物主名精确一致时还补 DMM id、假名、罗马字与首次头像，不替换演员真值。网络复用现有 R18 JSON 入口、SourceTransport、头像缓存与封面解析器；独立包无需另装 Go。本适配不新增站点 HTML 解析器。候选按资产 ID 与路径定位，批准时复核目标；时长证据不覆盖媒体探测时长。

已完成：共享 Media/Job/HTTP 边界、feedparser、Pillow、Beautiful Soup、FTS5、可安全导入的批处理脚本和按任务范围终止进程。

1. Video.js 已接管详情播放；`MediaEngine.stream_plan` 已让 115/PikPak 原生 MP4 使用 HLS 临时短片段，仍需补自适应码率、多路清单和生产验收。CloudDrive 的虚拟盘固定块预取仍属于来源层成本。
2. 番号元数据查询收敛成两套（ADR-0044），每个站只有一个归属（ADR-0048）：已有自写解析器的站只问自写那份，其余经 amane 桥；来源扩展先定归属，再登记进 `metadata_policy.SOURCE_SPECS` 与 `metadata_routes.ROUTES`，不为同一站写第二份解析器。
3. `status.py` 已并入 `peach status`，`suggest.py` 已由 `taste_history.py` 与馆藏页取代，`ledger.py` 已由 `peach init`／`peach scan` 取代。只剩 `sync_sha1_115.py` 还没有备份闸门（`tests/test_script_policy.py` 的例外表已记账）。
4. Peach 不做 token/成本日志扫描器，也不绑定 T3 Code 私有 RPC；使用其界面、CodexBar 和官方实时配额入口。
5. 「模仿/参考/对齐」不等于允许凭记忆近似。先取得并登记可复现证据；否则标记 `未取得`，不得作为忠实复刻发布。2026-08-17 的 YouTube 详情与 Shorts 动作栏参考已登记在 `docs/HANDOFF.md`，Peach 只复用可测量的层级、尺寸和状态语义。
6. Web UI 组件优先复用 `web/js/ui-components.js` 和 `.claude/skills/peach-web-ui/SKILL.md` 的语义矩阵。Peach 不引入 Geist React 运行时，只复用已锁定证据中的 Note／Progress／Switch／Tooltip／Collapse／Menu／Fieldset／Scroller／覆盖式滚动条（`attachOverlayScrollbar`，滑块不占宽度；`.geist-scroller` 只给两端渐隐，两者可叠加）／Empty State／Search Input／Spinner／Loading Dots 与 Dialog motion 语义、ARIA 和版式层级；整页异步重绘复用导航代际隔离，没有消费者的 Vercel 后台筛选器不照搬。
7. JAV 封面固定参考 Javinizer-Go `dd56998328d078c9baf68ff4fde2e6fcaa2a691a`（MIT）的 DMM
   modern `awsimgsrc.dmm.com/dig/...` 映射与尺寸门槛；Prestige 公开 API 的查询模型参考 MDCX
   `58e3f930f2e864fceb8a53ceef818716e2a6413d`（GPL-3.0，只作协议证据，不复制代码）。Peach 先离线复用
   `sources/metadata/javinizer-go/` 下的历史快照，再汇总 DMM 新旧 CDN、MGS `EnlargeImage`、Prestige `packageImage` 与历史成功
   URL，仍由 Range 量尺寸、像素面积最大者胜出和仅更大才原子升级。2026-08-31 真实 POC 中 `ABW-232`
   的 Prestige 官方图为 1024×690、DUGA 为 1000×674、MGS 为 840×563、DMM mono 为 800×539。
   批量流程不请求社区来源，历史快照里的社区站记录只借厂牌；既有库采集在官方渠道落空时经
   `peach.community_catalog` 查 AVBase、JavBus 与 javdb（后两家是 `peach.sources` 契约下的站；AVBase 搜索页 `/works?q=` 的 `__NEXT_DATA__`，
   2026-09-14 实测可取；资料取商品号认得出这个番号的那条店铺条目，名寄せ的作品标题可能来自收录本作的
   合集），封面按 dHash 先求两个图源一致（取景不同时再用 OpenCV ORB 特征点，相似变换内点 ≥60
   算同一张），只有一个图源时照用并留空 `verified_by`，
   遇验证页不绕过（ADR-0030、ADR-0032）。DUGA Web API 需代理店应用 ID，未配置前
   只复用成功日志的精确 URL。MDC-NG 公共仓库只证明 Amazon 日本渠道存在，后端匹配逻辑未公开，故只留
   POC 候选。该流程不新增依赖、不写 ledger，操作步骤见 `peach-jav-cover-workflow`。

- 对外请求的 UA 统一取 `peach.user_agent.USER_AGENT`（与用户这台机器的 Chrome 同大版本，ADR-0060）；HTTPX、来源连接器、FFmpeg 抽帧与脚本共用。复用现有 transport、限速和证书校验，无新增依赖；标准 UA 不保证站点放行。FANBOX 浏览器传输使用已安装 curl_cffi 的 Chrome 150 配置。Cloudflare 后面的来源经 `peach.browser_transport` 驱动本机 Chrome／Edge（CDP，自写 80 行 WebSocket 客户端，不加依赖）导航取页，做法参照 OpenAver 的隐藏 WebView2（ADR-0065）。
- 整张作品封面不装成头像：单人作品关联不证明画面中的人物身份，`cover_fallback` 显式标记身份未核实，采集脚本的安装闸门拒绝这类来源。图库给不出唯一人像时，补头像后继（`peach.avatar_followup`）从单人作品封面截脸周围一块方图（`peach.avatar_cover_face`，YuNet 脸框放大 2.4 倍），按脸宽像素挑封面，最差是缩略图；其余检得出脸的封面各截一张进候选缓存（至多 8 张），挑图弹层里一点就换。面具、眼罩照样算脸，检不出的不降门槛去捞：低分框多落在手和身体上。来源记 `cover-face` 与 `identity_verified: false`。图库同名多张时先按脸认人（`peach.face_match`，ADR-0056；一张参照截错人时，两张不同照片与另一张参照三方互证也算，ADR-0057；没有参照时两家目录的两张不同照片彼此过线且占多数也算，ADR-0062；没过尺寸门槛的小图也作证，只是不当胜者，ADR-0066），认不出才截封面；封面也截不出时装认得准的那张小图，标 `gallery_small`，之后可换。整张封面装的旧头像和截过的脸遇到更宽的脸自动替换，图库装的与人挑的不碰。头像选择器的作品组按封面像素面积排序。
- 复核页面上下文复用原生 CSS sticky、主导航 `--topH` 与既有滚动/尺寸调度，分类及筛选栏合为同一吸附区，分组标题按实测栏高接续吸附。仅吸附时显示通栏背景，全选本组紧邻标题；桌面、手机、换组、尺寸变化及返回顶部均用隔离候选验证。卡片以 flex 分开标题、既有 Scroller、当前信息和操作；只有资料滚动，当前信息过长时可聚焦滚动阅读。多选计数共用 `selectiondockcount`，保留首页的文字口径；不新增依赖，不改变候选与提交协议。
- 复核分类复用 `selectFieldHtml`、`wireSelectField` 和现有 `list-filter` 图标；图标只在筛选入口显示，选项保留文字与选中标记。按当前候选数据提供字段及来源选项，批量决定复用既有协议。字段次级分类采用具名 Listbox 分区，依据见 `reference-snapshots/vercel-review-actions.md`。人工复核与馆藏、关注、标签、垃圾文件和回收站共用 `selectiondock` 浮窗布局，保留各自操作与提交协议；复核卡片内作品样本选择仍属于单条候选，不混入页面级多选。没有新增依赖。Shift 连选使用原生 `mousedown.preventDefault()` 防止文字选区；实际浏览器验证覆盖亮暗主题、宽屏和 390px。

反馈控件复用：`noteHtml`、`progressHtml`、`gaugeHtml`、`projectBannerHtml` 与 `wireContextCard` 集中在共享 UI 模块；信息卡片复用原生 Popover 和现有锚定菜单定位，不添加浮层依赖。`BackgroundJob.update(job_id)` 报告浏览记录、口味分析和逐行来源解析的阶段与计数，`followJobProgress` 统一读取文字和总量，查询不重新执行任务。浏览记录解析继续使用 browserexport；本地临时浏览器数据库验证计数及隐私字段。证据见 `reference-snapshots/vercel-geist-note-progress-switch-analytics.md`。

### 文件检查与确认反馈

资源核对复用 `web_resource_sync` 的目录枚举、离线跳过、写前复验与 BackgroundJob，涵盖 local、
115、PikPak。展示复用 `frontend/` 构建链、Fieldset、Note、Toast 与 confirmModal；确认失败留在弹层，
危险动作初始聚焦取消，忙态阻止重入与关闭。无新增依赖，不引入另一套对话框库。
真实截图的 487 项／643 个缓存作为无写入渲染样本；配置历史及性能建议依据在 OPERATIONS。
