# 复用清单

这是 Codex 与 Claude 共用的实现查找表。新增、恢复或重写代码前必须按
`.claude/skills/peach-reuse-first/SKILL.md` 先查本文件、当前树、Git 历史和成熟外部实现。

## 复用决策门槛

CloudDrive 引导复用现有 `settings_file`、`platform.root_online`、`scan_location` 和 Preact
配置 island；来源仍为 `local`、`115`、`pikpak`。外部挂载由已安装的 CloudDrive 负责，
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
  它和 browser_cookie3 均不进入正式依赖。Javinizer-Go、HTTPX、curl_cffi、Pillow 和现有候选缓存是正式基础；
  各脚本的请求节拍应复用 `scripting.RateLimiter`／`HostLimiter`，不为同一职责再装一套框架。

- 采集 GUI 复用 Preact island、CredentialStore、HTTPX、Pillow 和 BackgroundJob；
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
- 物理资源垃圾候选的跨类型证据、人工复核和回收站语义；空目录清理复用 Python 标准库自底向上的 `os.walk` 与只删空目录的 `Path.rmdir`，Peach 只负责在线来源、根目录保护和 CloudDrive 并发消失边界；
- 私有获取来源、出处引用和发现关键词；
- 创作者级视觉采样语义；
- 推理 Provider 与 Agent Provider 的能力契约；
- 任务归属、进度、取消、成本和证据规则。

下面这些是基础设施而不是产品行为，所以要单独记下被拒绝的候选和不可替代约束，免得下一轮又从「这看起来该有现成库」开始。

| 自研实现 | 被拒绝的候选 | 不可替代约束 |
|---|---|---|
| `mp4index.py` 有界 MP4 关键帧索引 | PyAV、`pymp4`、Bento4 | PyAV 需要 demux，`pymp4` 依赖旧 Construct，Bento4 是额外二进制；都不能证明在云盘文件上保留「只读 moov/stss/stts、避免整片流量」的约束。 |
| `certs.py` 固定项目 CA 与短期叶证书（编码继续调用 OpenSSL） | mkcert、cryptography | mkcert 会接管本机 CA 安装/私钥，不能保持跨设备固定项目 CA；cryptography 只替换证书编码且增加原生依赖，不能删除 Peach 的 Apple 398 天与 CA 生命周期策略。 |
| `migrations.py` SQLite 迁移 | Alembic | Alembic 会引入 SQLAlchemy/Mako/greenlet；现有范围只需顺序 SQL、校验和、备份与 PyInstaller 资源定位，没有 ORM 消费者。 |
| Gofile API 直接 HTTP | 社区 wrapper | 官方没有维护中的 Python SDK；社区 wrapper 只是薄封装，不能绕过 Premium `contents` 权限，也不能减少 Peach 的 Bearer 隔离与媒体规范化。 |
| `netwatch.py`、streaming/segments、sync、versioning/Windows update | 通用替代实现 | 分别是无 PyObjC 的系统通知、FFmpeg/Starlette 上的会话策略、单 writer ledger 规则和 Git/PyInstaller 更新契约；通用替代会保留同量 policy 或扩大依赖。 |

保留自研不是永久豁免：约束改变或候选实现更新时重新跑 POC，不因本表结论跳过外部检索。

## 必须复用的成熟实现

| 能力 | 复用实现 | Peach 负责 |
|---|---|---|
| 本机文件夹对话框 | Windows 自带 `powershell.exe` 经 `Add-Type` 调 Shell 的 `IFileOpenDialog`（带地址栏的文件夹选择框）；macOS `osascript` 的 `choose folder` | `src/peach/folder_picker.py` 只拼命令、区分取消与失败、一次只开一个；不为一个对话框引入 tkinter 或 GUI 框架 |
| HTTP | 默认复用全项目共用的 `httpx.Client`/transport；FANBOX 公开 `post.info` 按固定证据复用 `curl_cffi==0.16.2` | 来源策略、DTO、脱敏、站点限定、大小上限；不求解机器人质询 |
| RSS/Atom | `feedparser` | 有界抓取、快照、复核、导入 |
| 追更来源接口 | FANBOX 公开帖子 API（详情只使用用户自己的可选 Cookie 与 Firefox 传输特征）、kemono 系公开 JSON API（`Accept: text/css`，站点自述的抓取路径）、rule34.xxx 官方 dapi（需账号 API key）与官方 tag 补全（公开）、Paheal 标签/详情页、Gofile contents API（需 Premium 账号 API token）、f95zone `latest_data.php`、站内搜索（需登录 cookie）、线程页与站内 masked XHR | 连接器边界、凭据隔离、多媒体顺序、文件站目标校验、变体与跨站重复判定、候选复核与批准后的 online asset 投影 |
| HTML 适配器 | Beautiful Soup 或 selectolax | 来源专用选择器和来源记录 |
| 位图 | Pillow | 头像/Logo 质量和来源策略 |
| SVG 光栅化 | `resvg-py==0.5.0`（resvg，MPL-2.0 绑定） | 只用于把站点自己的矢量图标转成位图再交给 Pillow。2026-09-02 实测 threads 的成品 app 图标只以 SVG 形式提供，不光栅化就只能退回位图 favicon。选它而不是 cairosvg：后者在 Windows 上要另装 cairo 原生库，前者是 abi3 轮子，win_amd64 / macosx_11_0_arm64 / macosx_10_12_x86_64 都有官方预编译，两个平台都不必装系统依赖。候选发现、内容比例判定、缓存与失败回退仍在 Peach。 |
| 搜索 | SQLite FTS5 | 索引字段、排序、profile 感知筛选 |
| 相关推荐 | OpenAver `dca4c0c368ea0c2db9cf15e48977de2fc75e7077` 的 Tag IDF + 系列／片商／出演者规则只作固定算法参考（MIT） | 独立实现规范实体评分、MMR 多样性、稳定 seed、解释原因与负反馈边界；不复制上游 UI／源码 |
| 女优姓名对照 | `li-peifeng/Jav-Actors-Mapping` 的固定 revision，仅作私有输入（仓库未声明许可证，不随 Peach 分发） | 精确匹配、冲突复核、别名、来源与真实 ledger 写入 |
| 女优头像候选 | Gfriends 的 GitHub raw 索引与单张媒体（只作外部 Provider，不克隆图库） | 名字链、质量档位、格式/尺寸/SHA-256 门槛、候选缓存、provenance、健康统计和人工复核 |
| 厂牌 Logo 候选 | 厂牌官网确认的社交 handle → unavatar URL 解析 → 平台 CDN 单图 | handle 归属、内容缓存、方形归一、精确/感知哈希、provenance、健康统计与变化复核 |
| 厂牌字标名录 | 发行平台自己的厂牌名录：MGStage `/ppv/makers.php` 十一页 351 家（`harvest_mgstage_makers.py`），jae.tokyo 展会名录 26 家 | slug↔账本对账（四路判据、空罗马字形当不可比）、烤方、两位共用、复核 CSV 与安装闸门。不推导 URL、不猜名字：名录给什么用什么 |
| JAV 元数据查询 | Javinizer-Go v1.5.1 单来源 JSON CLI（MIT）；MetaTube SDK `6a5e6128c725187aeaf921d48ed7d9cd9f30671b`（Apache-2.0）只作来源身份与丰富字段模型参考 | 只发送规范番号；Peach 管 source profile、`provider_id`／`content_id`、逐字段优先级、原始证据、丰富目录证据、健康统计、候选复核与批准后的 ledger 投影 |
| 已确认厂牌的目录归位 | Javinizer-Go v1.5.1 organizer 只作冲突预检、模板化目录和回滚边界参考，不让它持有 Peach ledger | `rehome_unknown_jav.py` 只消费人工确认映射；先出逐文件 CSV，拒绝扁平化重名与厂牌冲突，SQLite 备份后移动文件并同步 Peach 路径／实体 provenance |
| FC2 目录元数据与跨号证据 | 已缓存的 fc2cmadb Inertia `article`／评论收获；Javinizer-Go v1.5.1 的 FC2 解析器只作官方商品页字段边界参考 | 2026-08-31 登录态实测旧文章仍提供标题、原始标签、日期、时长、卖家、FC2 CDN 封面与 `comments`；Peach 只把无歧义标签翻译成现有词表，标题／标签进入 `/review`，实测 `w1200` 封面经尺寸与解码门槛落生成产物；稳定 pair、合集/分片保护、hash/时长/尺寸佐证、库外 evidence、健康统计和人工复核仍由 Peach 管，不依赖 FC2-Leak-Detector/JavSP，也不把镜像候选直写 ledger |
| 媒体探测/转码 | Peach 管理的 FFmpeg/ffprobe；Windows 已实测 FFmpeg 9.0.1 full build 的 CUDA/NVDEC、`scale_cuda` 与 NVENC，现有二进制启用 GPL/version3 | 任务策略和 Media Engine 编排：非原生容器先探测，H.264 8-bit 优先只换 MP4 封装；其余 Windows 输入依次尝试 CUDA→H.264 NVENC、软件解码→NVENC、原 `libx264` 回退，macOS 保持封装复制或软件转码。真实 CloudDrive POC 中，H.264/AAC 的 30 秒片段封装耗时 0.64 秒，1080p HEVC 的 30 秒 CUDA/NVENC 转码耗时 1.60 秒；不新增依赖，不改原媒体或 ledger。 |
| HTML5/HLS/DASH 播放 | Video.js 8.24.0 + 内置 VHS（Apache-2.0，本地固定版本） | 流方案、授权、稳定时长、回退顺序和统计面板 |
| 播放器设置与影院布局 | Video.js 8.24.0 的 `playbackRate`、既有 QualityLevel、原生 tooltip 与控制栏插槽；YouTube `e937390a` 实际 DOM／CSS／JS 提供可复现的几何、状态、动画和图形证据 | Peach 在现有 DOM 上组合氛围模式、播放速度、真实清晰度和影院模式，并复用 59 px 两排控制栏、40→111 px 横向音量、4→6 px 进度动画、右侧共享胶囊、整行悬停的 274 px 设置菜单和视口级全屏；普通视图 `contain` 保全片源，全屏按用户明确要求改用 `cover` 铺满视口，接受非等比例片源的边缘裁切。全屏命中同时使用 Video.js／原生类和 `isFullscreen()` 同步的 `data-peach-fullscreen`，并覆盖 `body.vjs-full-window` 回退，不能再靠单个 CSS 类推断运行态；标准、WebKit、Gecko 等浏览器专用伪类必须放进 forgiving `:is(...)` 或拆成独立规则，不能在普通 selector list 混写后让某浏览器因未知伪类废掉整组声明。用户要求精准图形的设置项、radio 选中勾、菜单箭头、中央 bezel 与 loading 只 vendoring 当前锁定版本的 SVG path／spinner 结构，音量 hover 与滑轨中心沿用上游外层伪元素和 50% 几何，tooltip 仅补 Peach 两排控制栏需要的显式层级与越界可见；不复制播放器控制逻辑、不迁移到 Video.js 10 Menu，也不引入重复现有质量选择的插件 |
| 播放器时刻预览 | Video.js 原生进度控件 + Peach 既有 `/poster?id=&c=0…8` 九宫格切片 | 本地媒体用已有接触表提供近似时刻缩略图；在线视频只显示时刻。`videojs-vtt-thumbnails` 与 `videojs-sprite-thumbnails` 都要求另建 sprite/VTT 契约，本项目不为已有能力新增依赖或重复抽帧 |
| 分卷文件命名 | [Plex 官方命名](https://support.plex.tv/articles/naming-and-organizing-your-movie-media-files/)的 `cd/disc/disk/dvd/part/pt + 数字` 与 [Kodi 官方 File Stacking](https://kodi.wiki/view/File_stacking)只作行为证据；运行时复用当前树的 `part_marker`，不新增扫描器依赖 | 兼容馆藏已有的裸数字和 A–H 后缀；仅连续、唯一标记自动合卡，保留每个 asset 和播放会话，不拼接或改写媒体 |
| 照片灯箱轮播 | Swiper 14.2.0（MIT，本地固定版本，按需加载 CSS／JS）的 Thumbs / Keyboard / Zoom 模块 | 构造轮播前必须同时等到样式与脚本就绪，并保留 scoped 的单 slide 结构样式防止首载竞态重叠；Swiper 管轮播、键盘、缩放变换与缩略图，Peach 管图集来源与顺序、当前缩略图居中、相对原图百分比、适应窗口／原大小语义、缩略图缓存与计费口径。瀑布流本身继续用 CSS `column-count`，不经过 Swiper。 |
| 导航排序 | 浏览器原生 HTML Drag and Drop | 桌面鼠标直接拖动、落点提示、上下移动按钮作为键盘与触屏回退、`localStorage` 持久化；不为单列排序引入额外运行时依赖 |
| 图标 | 固定版本的本地 Lucide 子集；Health Icons 24 px outline（CC0）用于领域图标；Phosphor regular 填充字形（MIT）只用在描边说不清的地方（字母表 Aa、播放列表） | 标签、状态和交互设计 |
| 资源文本中间省略 | Vercel Geist `MiddleTruncate` 行为契约 + 浏览器原生 `ResizeObserver`、`Intl.Segmenter`、Canvas 测量 | 文件名、路径、URL、ID 等资源标识用 `data-middle-truncate`；标题、说明、人名、标签等语义文本保留末尾省略；页面源测试登记全部末尾省略选择器，新增截断未先分类会失败 |
| 定时轮询 | APScheduler 3.11.3（MIT，固定稳定版；3.x `BackgroundScheduler` / interval trigger） | 只在 ledger writer 启动、持久频率、首次延迟、单实例、手动/自动互斥、运行状态与来源错误汇总 |
| 本地文件事件 | watchdog + 定期对账 | 媒体身份和漏报修复 |
| 过渡期元数据/媒体 | Stash GraphQL、CommunityScrapers、Stash 任务系统 | 适配、对账、退出门槛 |
| 局域网发现 | Python zeroconf | 服务生命周期和真实客户端验收 |
| 生成产物跨机同步 | Syncthing 2.1.x，Windows send-only → Mac receive-only | 目录划分、忽略规则、方向固定与「Mac 不发布正式产物」的边界 |
| Windows 托盘 | pystray 0.19.5（LGPLv3）、Pillow、Win32 Per-Monitor V2 DPI | Peach 服务归属、后台更新检查、菜单动作、品牌图标 |
| macOS 菜单栏 | `pyobjc-framework-Cocoa==12.2.2`（MIT）提供 AppKit / PyObjCTools / objc | 附件应用策略、18 pt template 图、服务归属与菜单动作 |
| 人脸取景 | `opencv-python-headless==5.0.0.93`（Apache-2.0）的 `cv2.FaceDetectorYN` + opencv_zoo 定版模型 `face_detection_yunet_2023mar.onnx`（sha256 `8f2383e4…52fa4`，232 KB，放 `peach-data/tools/yunet/`，不进 Git）；MetaTube SDK `6a5e6128c725187aeaf921d48ed7d9cd9f30671b` 的主脸聚类只作算法参考 | 头像／封面离线脚本共用 `peach.face_detect`，主脸选择、归一化焦点与 sidecar。**主脸不是最大的那张**：`main_face` 先筛掉分数落后最好那张 0.1 以上的框，再在剩下的里取最大。只按面积挑会被「大而勉强」的误检抢走（`performer-8218` 那张 600×1000 人像上，罩在胸口的框 0.427×0.313 分 0.798 压过 0.202×0.170 分 0.928 的脸，圆头像于是取景在胸口）；只按分数挑会被背景里那张小而清晰的脸抢走（`performer-8540` 右上角 0.066×0.052 分 0.925）。954 张封面按这条重算，47 张换了主脸，每一张的新框分数都更高（`451HHH-029` 从画面中缝的 0.813 换到左上主体的 0.925）。**Haar 级联已不可用**：OpenCV 5 把它移出了 Python wheel（`cv2.CascadeClassifier` 不存在、`cv2/data/` 只剩 `__init__.py`），两个脚本一直抛 AttributeError，954 张封面 0 个 sidecar，取景从未生效。YuNet 同属 OpenCV，不是替代品，换掉的只是检出器这一层：Haar 在 512 张头像上检出 313、46 张封面上检出 24，YuNet 首轮 12 张封面检出 11，且带置信度，不必再靠位置规则丢假阳性。Pigo v1.4.6（MIT）512 张检出 488，但存在无脸误报且无 Python 部署优势，仍不引入。 |
| 115 文件清单 | `p115client==0.0.9.6.5.1`（MIT） | 只在显式 SHA-1 对账脚本中安装，Peach 负责 ledger 事务、备份与写入门槛 |
| 智能体用量/配额 | Provider 官方配额接口；T3 Code/CodexBar 提供本地历史 | 任务路由、脱敏、过期快照标记 |
| 视频出处/片尾证据 | 现有 FFmpeg 抽帧 + Windows.Media.Ocr WinRT Provider（Windows PowerShell 5.1 固定适配器） | 有界首尾采样、缓存、来源/Full version 分类、健康统计与人工复核 |
| 参考产品行为 | 当前线上交互 + 有版本的公开 DOM/CSS/JS；取不到源码时用精确截图测量 | 证据登记、无障碍、Peach 差异、回归检查 |
| 浏览器历史解析 | `browserexport==0.4.4`（已替换 `taste_history.py` 自写的 Chrome/Firefox/Zen/Safari SQLite 解析） | Python 3.14 依赖解析通过；POC 在本机 7 个 Chrome/Firefox/Zen profile 上与 Peach 逐库计数完全一致，macOS 的 Safari／Zen／Firefox／Chrome 路径发现有独立测试。首个消费者是 `/taste` 的本机读取与导出导入；Peach 保留 SQLite backup、Takeout、私有原始存储、域名分析和 candidate 生成，并在 Windows 自己关闭只读连接以避开依赖的文件句柄滞留。跨主机同步不由该依赖提供，仍须显式导出、传输和按来源去重合并。 |
| 批处理进程锁 | `portalocker==4.3.0` 的 `PidFileLock`，**仍是候选，尚未替换 `jobs.PidFileLock`** | Python 3.14 解析通过，现成覆盖 PID 写入、锁持有者、原子替换、陈旧文件与释放清理。Peach 只保留任务归属和错误文案映射。替换落地前不得声明依赖已进入生产。 |
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
| `rm-probe.py` | `scripts/probe.py` | 可复用策略移入 `src/peach`，保留续跑语义 |
| `rm-sheets.py` | `scripts/sheets.py` | 共用 FFmpeg/任务原语，不再新建抽帧管线 |
| `rm-ledger.py` | `scripts/ledger.py`（扫描摄取，兼 ADR-0021 留存的 stash 导入入口） + repository/migrations | 新产品读取进入 repository，不放回旧 CLI |
| `rm-status.py`、`scripts/status.py` | `peach status`（`src/peach/cli.py`） | 状态命令只读，并且只有一个入口：打包入口转发全部子命令，不再单独发一个脚本 |
| `rm-suggest.py`、`scripts/suggest.py` + `moods.json` | `scripts/taste_history.py` + 馆藏页筛选 | 排序与心情筛选留在应用端口，不放回旧 CLI |
| 各写库脚本私有的 `--database`／`--backup-dir`、自写 backup 与只读连接 | `src/peach/scripting.py`（`open_readonly`、`add_ledger_write_args`、`open_for_write`、`counts_of`、`verify_after_write`、`USER_AGENT`、`RateLimiter`） | 真实写入的参数只有 `--db`／`--apply`／`--backup` 一套；`--apply` 必须同时给 `--backup`，备份走 `peach.migrations.sqlite_backup`，脚本不再各写一份 |
| `rm-trafficwatch.py` | `scripts/traffic_watch.py` | 只停止任务拥有的进程树 |
| `rm-sha1.py` | `scripts/sync_sha1_115.py` | 复用 Provider 哈希，不盲目重算网盘媒体 |
| `import_performer_portraits.py`（原 `agent/claude/performer-portraits`） | `scripts/audit_performer_portraits.py` + `scripts/localize_performer_names.py` | 一次性导入已执行完并记在 STATUS；后继只产 CSV，不写头像文件 |
| `normalize_code_suffix.py`（原 `agent/claude/code-suffix`） | `catalog_rules.jav_display_metadata` + `scripts/audit_jav_display.py` + `scripts/audit_code_creators.py` | 紧凑番号只随发行证据恢复；版本后缀投影为徽章，原始文件身份不丢失；全库审计只读 |
| `dedupe_performer_creator.py`（原 `agent/claude/dedupe-identity`） | `scripts/merge_duplicate_identities.py` | 后继的判据已扩到跨 kind、同 kind 与真子集三轮，旧脚本判据更窄 |

## 当前替换队列

已完成：共享 Media/Job/HTTP 边界、feedparser、Pillow、Beautiful Soup、FTS5、可安全导入的批处理脚本和按任务范围终止进程。

1. Video.js 已接管详情播放；`MediaEngine.stream_plan` 已让 115/PikPak 原生 MP4 使用 HLS 临时短片段，仍需补自适应码率、多路清单和生产验收。CloudDrive 的虚拟盘固定块预取仍属于来源层成本。
2. Javinizer-Go 已接管番号元数据查询适配；来源扩展只加入 Peach policy 白名单/profile 与健康统计，优先启用其现有 scraper，不在 Peach 分叉站点解析器。
3. `status.py` 已并入 `peach status`，`suggest.py` 已由 `taste_history.py` 与馆藏页取代。剩余的是 `ledger.py`：读取逻辑继续移到 repository/application 端口，摄取入口本身按 ADR-0021 保留。它和 `sync_sha1_115.py` 目前都还没有备份闸门（`tests/test_script_policy.py` 的例外表已记账）。
4. Peach 不做 token/成本日志扫描器，也不绑定 T3 Code 私有 RPC；使用其界面、CodexBar 和官方实时配额入口。
5. 「模仿/参考/对齐」不等于允许凭记忆近似。先取得并登记可复现证据；否则标记 `未取得`，不得作为忠实复刻发布。2026-08-17 的 YouTube 详情与 Shorts 动作栏参考已登记在 `docs/HANDOFF.md`，Peach 只复用可测量的层级、尺寸和状态语义。
6. Web UI 组件优先复用 `web/js/ui-components.js` 和 `.claude/skills/peach-web-ui/SKILL.md` 的语义矩阵。Peach 不引入 Geist React 运行时，只复用已锁定证据中的 Note／Progress／Switch／Tooltip／Collapse／Menu／Fieldset／Scroller／覆盖式滚动条（`attachOverlayScrollbar`，滑块不占宽度；`.geist-scroller` 只给两端渐隐，两者可叠加）／Empty State／Search Input／Spinner／Loading Dots 与 Dialog motion 语义、ARIA 和版式层级；整页异步重绘复用导航代际隔离，没有消费者的 Vercel 后台筛选器不照搬。
7. JAV 封面固定参考 Javinizer-Go `dd56998328d078c9baf68ff4fde2e6fcaa2a691a`（MIT）的 DMM
   modern `awsimgsrc.dmm.com/dig/...` 映射与尺寸门槛；Prestige 公开 API 的查询模型参考 MDCX
   `58e3f930f2e864fceb8a53ceef818716e2a6413d`（GPL-3.0，只作协议证据，不复制代码）。Peach 先离线复用
   Javinizer-Go 原始快照，再汇总 DMM 新旧 CDN、MGS `EnlargeImage`、Prestige `packageImage` 与历史成功
   URL，仍由 Range 量尺寸、像素面积最大者胜出和仅更大才原子升级。2026-08-31 真实 POC 中 `ABW-232`
   的 Prestige 官方图为 1024×690、DUGA 为 1000×674、MGS 为 840×563、DMM mono 为 800×539。
   AVBase 已变为 Cloudflare 验证页，批量流程不再请求也不绕过；DUGA Web API 需代理店应用 ID，未配置前
   只复用成功日志的精确 URL。MDC-NG 公共仓库只证明 Amazon 日本渠道存在，后端匹配逻辑未公开，故只留
   POC 候选。该流程不新增依赖、不写 ledger，操作步骤见 `peach-jav-cover-workflow`。
