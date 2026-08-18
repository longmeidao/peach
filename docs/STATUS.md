# Peach 当前状态

最后核验：2026-08-18

## 运行态

- 生产入口：Windows 当前用户 Startup 中的 `Peach.lnk`，启动 `R:\peach-app\dist\Peach\Peach.exe`（无参数托盘模式）。当前版本 `0.6.1`。
- HTTP：`0.0.0.0:80`；HTTPS：`192.168.50.162:443`。`peach.local` 是唯一正式局域网名称，发布为 `192.168.50.162`。
- mDNS 使用 Python zeroconf 的全合格网卡监听；生产显式固定发布地址，避免隧道网卡误选。没有发布 `lmd-dst.local`。
- Stash 仍运行于 `127.0.0.1:9999`，只作为过渡期可替换适配器。
- Python：3.14.7；FFmpeg/ffprobe 由 `R:\peach-data\tools\ffmpeg` 管理，不再依赖 Stash 私有目录。
- 真实 ledger：`R:\peach-data\database\ledger.db`，迁移 `0000`–`0015` 已应用，零待处理。复核表迁移前备份：`R:\peach-data\database\ledger.pre-0015-20260817-173639.db`；黄金视频删除前备份：`R:\peach-data\database\ledger.pre-golden-delete-20260817-124921.db`；创作者清理前备份：`R:\peach-data\database\ledger.pre-0014-20260817-134153.db`；时长纠正前备份：`R:\peach-data\database\ledger.pre-duration-fix-20260818-103252.db`；完整性 `ok`。
- PID 只是观测值，不是配置；每次停止或重启前必须重新核对命令行、父子关系和端口归属。

## 已核验代码与部署能力

- FastAPI 是唯一 Web server，提供首页、稳定 JSON 契约、标准 Range/HEAD、缩略图、海报、头像和 Logo。旧 `BaseHTTPRequestHandler`、动态 legacy loader 和启动时即席修表已删除。
- Ledger 是资产、身份、行为和知识真相。规范女优/厂牌/创作者/标签/系列使用 `entity`、`asset_entity`、`entity_external_ref`；扁平字段只作兼容投影。
- `MediaEngine` 统一管理本地文件和 Stash 公开协议适配器。浏览器本地 MP4/WebM/Ogg 直出；115/PikPak 已知时长的原生 MP4 由 `/api/stream-plan` 选择 6 秒 HLS 临时片段，AVI 等由 `TranscodeService` 缓存为 H.264/AAC MP4，原文件不改写。
- 真实 CloudDrive 作品 4289 已通过 `video/mp4`、1 KiB `206 Partial Content`、缩略图和海报检查；盘符可见性以 Peach `/stream` 为最终证据。
- SQLite FTS5 trigram 已覆盖 81,873 个资产；三字符以上走 FTS，短查询回退 LIKE。
- `FeedAdapter` 已支持显式、有界 RSS/Atom 发现、条件请求和不可变快照；尚未配置真实订阅，也不会启动时自动写 ledger。
- AI Provider 已拆为推理与 Agent 两层。`/api/providers` 无副作用且不泄露凭据；OpenCode Go 模型清单只在显式访问时拉取，当前不发推理请求。
- Windows 托盘已部署：单击打开 Peach，右键提供状态、重启、日志、版本/更新和退出；Per-Monitor V2 DPI 在创建窗口前启用，更新检查在后台线程执行并使用非模态通知。
- Windows 品牌资源已统一为附件生成的 `1024x1024` 正方形蜜桃图：`resources/peach-logo.png`、`resources/peach.ico`；Web favicon、托盘图标和 EXE 内嵌图标共用该资源。PyInstaller 打包产物为 `dist/Peach/Peach.exe`，桌面和 Startup 的 `Peach.lnk` 均按 FlowLens 的 `exe,0` 方式指向它；该 exe 只打包托盘自身，服务进程仍由项目 venv 承担，不是可移动的独立发行版。
- 版本唯一来源为 `src/peach/__init__.py::__version__`。本批把实体作品、艺人/标签索引和广告卡片改为有界增量构建，去除代表图 N+1 查询与后续翻页重复总数统计；详情播放器复用本地 Video.js 8.23.9，并按 pre-1.0 SemVer 升至 `0.5.6`。没有 Git remote 时只报告本地开发版，不伪造更新能力。
- 本地 CA HTTPS 已部署。CA 包含 critical `CA:TRUE` 和签名用途并通过 OpenSSL 链验证。macOS/iOS 只安装 `peach-local-ca.crt`；不得传播任何私钥。
- 项目代码、运行数据、本地媒体已分离为 `R:\peach-app`、`R:\peach-data`、`R:\media`。旧空 Inbox 和 `Resources/Tools` 兼容表面已移除。

## 界面与交互现状

- 首页、详情、标签管理（字母表/标签云）、女优墙、厂牌/创作者/系列资料页、统计、沉浸模式均为同一无构建单页表面，桌面与手机共享数据契约。
- 女优/厂牌/创作者/系列名称用于导航；只有内容标签直接叠加筛选。「换一批」是动作，不是筛选状态。
- 共演作品在卡片上叠放前 3 位女优头像并列出前 2 个名字，超出部分写「等 N 人」；契约每条卡片下发至多 `CARD_PERFORMERS`（当前 6）位并给出 `performer_total`。详情页逐行列出全部出镜者，每行带自己的头像，标签只写在第一行；超过 8 位时其余默认收起，一次点击展开，收起的行始终留在 DOM 里。沉浸模式的归属行同样列出前 3 位。
- 卡片身份女优优先；头像本身进入女优资料页。缺失厂牌 Logo 显示首字母，不用任意作品图冒充。
- 「喜欢/为什么喜欢」写 profile 级 `asset_preference`；原因非空会隐含喜欢，但 AI 不能直接改写用户原文。「稍后看」独立写 `watch_queue`。
- 详情反馈是 Like、不喜欢、看过、稍后看、回收站五个 Lucide 图标；默认首页排除竖屏，竖屏入口保留完整竖屏集合。
- 长卡连续 hover 5 秒才放大并显示 ±10 秒和详情控制；短卡立即显示稍后看。沉浸模式使用经源码核验的 200 ms TikTok 滚动时序。
- 参考 Beeg 的控件和表面层均已登记当前 CSS/JS hash。当前源码证明普通标签为透明底加 15% 白色内描边，厂牌为 5% 白色叠层加 10% 内描边；frost 只用于被选中的浮层，不再笼统套到所有胶囊。49 vh 页首光晕按实测像素重建，不复制许可不明的 Beeg 位图。
- 当前厂牌 Logo 覆盖 28/114，仍有 86 个待补；女优头像质量评分和联网高清头像仍是后续任务。
- 公共资料页 URL 已改为 `/performers/{name}`、`/studios/{name}`、`/creators/{name}`、`/series/{name}`；旧 `/entity/{kind}/{name}` 已删除。内部 JSON 兼容端点仍为 `/api/entity`。
- 收起详情或导航离开时会暂停视频、清空 `src`、调用 `load()` 并移除元素，不再留下后台播放/下载。详情打开时筛选栏取消 sticky，避免上滚遮住详情顶部。
- 标签统一使用同一圆角和内边距 token；厂牌/来源保留独立身份样式。选中框改为内描边，不会被卡片边缘或 hover 样式裁掉。
- 顶栏提供显式多选模式；`Ctrl`/⌘ 单项切换，`Shift` 在当前可见网格中连续范围选择。选中标记位于右上角，不覆盖来源徽标；回收站卡片会灰化并显示独立「回收站」标记。
- 详情身份按名称去重，标签可逐项隐藏或手动添加；隐藏只写 profile 覆盖，不破坏原始来源断言。高潮按钮使用 Health Icons 的 CC0 领域图标和独立暖粉强调色。
- 已完成首轮界面文案审计：删除标题复述、实现状态说明、随机示例占位符和模型自我声明；删除保护、隐私边界、流量成本及陌生状态说明继续保留。
- 侧栏、抽屉和粘性栏使用 Beeg 当前源码实测的透明层与 blur 数值；页面背景不再是纯黑，侧栏不再是纯灰。本轮没有为了装饰引入动画库，后续动效必须先复用审计并只表达状态/连续性。
- 详情中的本地来源图标已补齐 `stroke: currentColor` 和 `fill: none`，不再因 SVG 默认黑色而不可见。标签添加使用弹窗完成搜索、最近使用、全部标签、已选状态和键盘操作；侧栏入口简化为「艺人」「标签」，并删除装饰性分隔线。
- 首页创作者头像已移除常驻黑框，只在 hover/选中时显示状态描边。女优/厂牌/创作者/系列资料页打开后隐藏首页人物、厂牌和筛选栏；资料区取消巨型外框，桌面头像为 160 px，并在资料下展示真实标签与关联艺人。厂牌资料优先使用 Logo，只有缺失时才使用实体图，不再用代表作品截图冒充厂牌头像。
- 实体资料页标签只筛选当前实体作品，不再跳回首页做全局筛选；当前标签写入资料页查询参数，便于返回和分享。首页状态标签已精简为「全部、没看过、稍后看、已标记」，与右侧内容标签之间恢复语义分隔线。搜索框显示随机推荐关键词，不加「试试：」；空输入聚焦后按 Enter 会直接搜索当前推荐词。
- 大结果集不再按总数一次构建：实体页每批 48、首页 60、艺人索引 120、标签索引 180、疑似广告 DOM 每批 60。实体与首页第二页起跳过全量总数统计；无限滚动有单请求锁，快速切换会丢弃迟到响应，顶部聚合复用 30 秒会话缓存。
- 详情播放器使用本地固定版本 Video.js 8.23.9，提供 ±10 秒、画中画和播放统计。远端原生 MP4 优先走 HLS 片段，HLS 失败仍回退标准 HTTP Range；不再把浏览器的开放区间伪截成 32 MiB。item 29297 的权威总时长固定为 28,639.916 秒（`7:57:19`），不再随缓存增长。
- 详情全屏覆盖播放器的 `76vh`/固定比例限制，视频按播放器尺寸渲染；加载或等待时显示基于 VHS/媒体请求的实际速度估算。沉浸模式使用全视口 `object-fit:cover`，初次加载和切换下一条时显示 spinner 与速度，按钮采用 Shorts 取证的 tonal 圆角层级。
- 本批修复顶部品牌图与正文 Logo 不一致、竖屏推荐条固定在首批作品中间、竖屏卡片按实际宽高显示、卡片 hover 蓝色边框、半透明层过透、详情关闭时导航仍残留、ambient 上下断层和详情按钮 hover；搜索历史迁移到共享 `search_history` 表。
- 回收站有独立入口 `peach.local/trash`（后端 `/trash` 走 SPA，前端 `restoreRoute` 直接进 `state=trash`）。
- 回收站的两条删除路径此前从未真正执行过，已修复：`media.py` 漏 `from functools import lru_cache` 导致整个包 import 失败；`ASSET_REFERENCE_TABLES` 从未定义，`/api/batch` 的 `delete` 必然 `NameError`；`/api/trash/empty` 只加了 dispatch 分支、`w_empty_trash` 没有函数体。现已统一到 `purge_assets()` 并补齐数据层测试。之前「API 写读删已复核」的说法不成立，属于未验证即结论。
- 管理界面新增 `/review` 人工复核页，分为创作者标签、厂牌 Logo、女优头像、媒体失败四层；候选通过 `review_decision` 留痕，创作者标签只有点击「通过」后才写入 `asset_tag/asset_entity`，其余候选默认不改真相字段。
- HLS 除开头一两段外全部失败过，2026-08-18 已修复。`-copyts` 保留原始时间轴后，FFmpeg 把 `-t` 当成绝对结束时刻而不是片段时长，每段的 `-t` 都约等于一个片段长，起点超过它的片段一律「已经过期」，FFmpeg 以退出码 0、空 stderr 写出 0 字节，服务端只能报一句没有内容的 `ffmpeg failed`。实测 asset 6562（6,332 秒）：片段 0、1 返回 200，片段 2 与 300 都是 503；片段缓存目录里 6562、29914、19490 三个资产也都只留下 `0.ts` 与 `1.ts`。所以症状不只是拖不动，播到约 20 秒就会断。修法是保留 `-copyts`、把 `-t 时长` 换成绝对终点 `-to 起点+时长`；删掉 `-copyts` 同样能出片，但首个 PTS 会退回 0.069，每段都自称从 0 开始，正是当初引入 `-copyts` 要解决的拖动跳位。隔离实例实测片段 2、300、633 全部返回 200（47.2 MB、41.1 MB、69.3 MB），手工核验片段 300 首个 PTS 为 2997.995，绝对位置与跨段连续性都对。生产托盘已于 2026-08-18 重启并复验：asset 6562 的片段 2、300 与 asset 29914 的片段 5 均返回 200。
- 同批把静默失败改为自陈：FFmpeg 退出码 0、stderr 全空却写出 0 字节时，错误信息带上 `returncode`、字节数与 `ss`/`to`，不再只说 `ffmpeg failed`。上面那个缺陷能藏这么久，正是因为日志里那句话什么都没说。
- 远端 MP4 已改为默认标准 Range，HLS 转为按需（`/api/stream-plan?mode=hls`），见 ADR-0016。起因是 asset 22716（115 的 HEVC 重制 MP4）在详情页黑屏：分片全部 200、数据进了缓冲、时间轴照走，但 `videoWidth=0`、解码 0 帧、无 error 事件。`-c copy` 把 HEVC 原样装进 MPEG-TS，而 Chromium 的 MSE 不支持 TS 里的 HEVC；同一浏览器实测 `video/mp2t; codecs="hvc1…"` 为 `false`、`video/mp4; codecs="hvc1…"` 为 `true`，直接 Range 播同一文件解码 997 帧、拖动后继续出帧。文件名含 `HEVC` 的 115 视频有 248 条、PikPak 2 条，此前全部受影响。生产重启后复验 22716：默认计划为 `range`，`mode=hls` 仍给出 76 段计划，播放列表返回 200；详情页取到 `/stream?id=22716`、`readyState=4`、`1920×1080`，当前帧平均亮度 147.1、非黑像素 99.3%。
- HLS 分片改为关键帧对齐：`peach.mp4index` 从 MP4 `moov/stss` 直接读关键帧表（实测 0.01 秒，`moov` 在尾部也能定位），播放列表报真实时长；时间戳改用 `-copyts` 保持跨段连续；片段缓存写入磁盘并按最后访问时间淘汰；FFmpeg 并发加信号量闸门。读不出关键帧的片源直接回退标准 Range，`/api/stream-plan` 也只在计划成立且带 session 时才宣告 HLS。
- 厂牌 Logo 来源改为厂牌自己的社交账号头像（`scripts/fetch_studio_avatar_candidates.py`）。已确认 13 个 handle 并**逐张看图核对品牌归属**后落盘：Deep's、Hunter、Alice JAPAN、E-BODY、Glory Quest、K M Produce、TMA、Aroma Planning、M's Video Group、DAHLIA、Milu、Das、Muku；其中 Das 与 Muku 由 `scripts/find_studio_socials.py` 穿过官网年龄门后取得，Deep's 也由官网独立复证；映射表 `R:\peach-data\generated\studio-x-handles.csv`，候选 `studio-logo-social-candidate-20260817.csv`，图片 `generated\studio-logos\`。其余 76 个未取得，留空待查。长条形 Logo 补自身底色填成正方形而不是丢弃。
- Logo 归属的判据是图不是 handle：`@ms_harapekori` 看不出与 M's Video Group 的关系，看图确认是对的；`@OFFICEKS` 能取到 400×400 但图只有色块无品牌文字，而同名公司有多家，因此判为未取得。`@bazooka`、`@bibibi_25` 同理被排除。
- 复核层已加固：候选按前缀取最新批次（不再写死日期）、缺主键的行跳过并计数（不再退化成行号）、只有 `status=candidate` 的 creator 候选可批准、批准的 creator/tags 以候选文件为权威（请求体只作确认）、未勾选整条通过受 `REVIEW_APPLY_LIMIT=500` 约束、写入改为 `executemany` 并在完成后 `cache_bust()`。`vision_creator_review` 已纳入统计标签覆盖和 Top 标签口径。`/api/review` 走缓存，创作者预览由一次分组查询取代 42 次三重 LEFT JOIN。候选目录改由 `PeachSettings.candidate_root` 提供，测试不再读真实 `generated` 目录。

## 数据与批处理

- 真实资产 81,847 条，其中视频 24,967 条。迁移后的完整性检查为 `ok`，外键违规为 0。
- 已核对并删除 `asce/The.Great.Escape.S04` 正常向剧集：13 个视频、13 个字幕、16 个派生图，同步清理 26 条 ledger 资产。原因是旧导入器把集合目录 `asce` 投影为创作者，再把创作者板上的低置信标签批量传播。`0009` 已移除 `asce` 假创作者及其 `vision_creator` 断言，保留其他独立来源标签。
- 番号刮削已处理 1,104 个非 FC2 番号，715 条取得数据；所有 330 个 FC2 在三来源样本中零命中，因此默认跳过。
- 创作者视觉板已处理 30 张，27 位创作者写入 27,295 条 `vision_creator` 标签，覆盖 4,518 个视频；置信度固定为 0.6，区别于逐条证据。
- `find_ads.py` 只生成候选，不删除。当前 82 条、约 1.5 GB；77 条确认、5 条存疑。`BNST033.mp4` 已从错误待删结论中排除。
- 115 时长修复后，未知时长不再写 0，而写失败值 `-1`；`--redo zero|failed|all` 可重试。
- 2026-08-15 的 115 接触表批次已正常结束：处理 982、失败 34、耗时 3.19 小时，锁文件已释放；托盘重启没有中断该任务。剩余量继续以文末自动区块的实时口径为准。
- 115/PikPak 抽帧主要成本是 CloudDrive 块预取流量：实测九帧接触表约为 115 285 MB、PikPak 163 MB。PikPak 全量抽帧约 773 GB，暂不启动。
- `RM-TrafficWatch` 常驻心跳已改用 `pythonw.exe` 隐藏运行。默认 200 GB 守卫统计代理流量；直连来源需显式 `--count-direct`。
- 番号目录冒充创作者的清理器 `scripts/audit_code_creators.py` 已就绪，尚未对生产 ledger 执行。2026-08-18 在 ledger 副本上的 dry-run：命中 44 个，其中 31 个判为番号、2 个判为站点作品号、11 个判为存疑。副本 `--apply` 实测删创作者关系 121 条、删实体 33 个、补 `code` 96 条、清扁平字段 121 条，完整性 `ok`、外键违规 0；`banbi_555`、`raikun325`、`luckydog22` 等真实上传者与全部 pixiv 画师未被触及。要对生产执行必须 `--apply --backup`。
- 目录创作者审计覆盖全部 66,252 条历史关系：58,803 条为仅目录候选、6,621 条缺少路径交叉核验、745 条 TokyoDolls 错挂「捅主任」已解除、83 条「足交仙人」已按文件名/水印证据归到 `suzuq`。逐项和汇总 CSV 位于 `R:\peach-data\review\creator-attribution-*-20260815.csv`；没有删除媒体或标签。
- `DiskGuard` 已进入主线并接入 `probe.py`、`sheets.py`、`creator_boards.py`：默认每 20 秒复查系统盘实际余量，触线后停止领取新任务、保留已完成结果并返回退出码 3。CloudDrive 当前缓存上限 50 GiB、策略 LRU；本轮核验时没有上述旧代码长任务在运行。
- 机械识别批次已接手：读取 42 个未处理创作者板，生成 `R:\peach-data\generated\creator-tags-candidate-20260817.csv`；仅输出 `candidate/skip`，未写入 ledger。现有 `creator-tags-review.csv` 的 `applied` 记录不重复处理，聚合目录和广告板保留 `skip`。
- Logo/头像机械候选已导出：`studio-logo-candidate-20260817.csv` 含 86 个缺失厂牌，`performer-avatar-candidate-20260817.csv` 含 20 个 `no_avatar/avatar_rejected` 女优；均只保留来源候选，不写真相字段。
- 115 抽帧 worker 已接入 `resolve_case_insensitive`：小样本通过后完成 33 条 9 帧批次，31 条成功登记 snapshot、2 条仍失败（asset `12510`、`18349`），未伪报成功；日志 `R:\peach-data\logs\sheets-20260817-171917.log`。
- 这 2 条失败已于 2026-08-18 用 FFmpeg 直接复现定因，两条是不同问题，都不是路径或色彩元数据：
  - `18349`（`B:\xxr\1(14)(1).mp4`）：ledger 记的是 `752.24` 秒、`1280×720`，ffprobe 实测为 `110.87` 秒、`1920×1072`，只有 `size` 98,246,962 两边一致。`make_sheet` 按 ledger 时长算的 9 个采样点里有 8 个落在文件末尾之后，只抽到 1 帧，触发 `len(captured) < 2` 判失败。t=61.8 秒实测能抽出 11,405 字节的帧，片源可用；要修的是 ledger 的时长与分辨率，不是抽帧代码。
  - `12510`（`捅主任` 目录下的 `好色™ Tv.mp4`）：FFmpeg 报 `stream 0, missing mandatory atoms, broken header`，`profile`、`pix_fmt` 均为 `unknown`、`level=-99`，解码器建不起来，任何时间戳都抽不出帧。片源本身损坏，不再重试。
- 两条都已按上述结论收尾（备份 `R:\peach-data\database\ledger.pre-duration-fix-20260818-103252.db`）：
  - `18349` 由 `probe.py --asset 18349` 重探改正，`duration` 752.24 → 110.866667、分辨率 1280×720 → 1920×1072、`fps` 25 → 30，情境层随之由「短/720P」变为「速食/2K」。随后 `sheets.py --asset 18349` 重抽成功，产物 `snapshots\cloud\115\45\4519ff7e5d496e1b.jpg` 为 1440×804（3×3 九帧、120,876 字节）并已登记 `snapshot_path`。写入前后 asset 81,770、video 24,890、asset_tag 88,542、entity 8,286 均不变，`integrity_check` 为 `ok`、外键违规 0，只有这一行的事实字段发生变化。
  - `12510` 经 `/api/review/decision` 写入 `review_decision`（`category=media_failure`、`status=rejected`），note 记录了 FFmpeg 原始报错，`applied_assets` 为 0，不动任何真相字段。`/review` 媒体失败层的待办由 2 条降为 1 条，即这条已判定的坏片源。
- `probe.py` 与 `sheets.py` 都新增了 `--asset`：按 id 点名处理，绕过各自的批量筛选，计费来源与 `online` 边界照旧生效。`probe` 的 `--redo` 只认 0 和 -1，够不着 `18349` 这种「看着正常但是错的」时长；`sheets` 点名时还会绕过「产物已存在」短路，否则重抽会被上一次的错结果短路掉。两者都有测试。
- 由此暴露的代码缺陷已修：`scripts/sheets.py` 的 `make_sheet` 改为返回「是否成功 + 原因」，一帧都解不出记 `broken_source`、解得出一部分记 `duration_mismatch`，另有 `tile_failed`、`no_duration`、`exception`。worker 逐条写 `[fail] asset <id> <原因> <路径>`，批次结束再打一行原因分布。之前只累加失败计数，两种完全不同的故障在日志里长得一样。
- 番号体系女优身份已回填真实 ledger（备份 `ledger.pre-performer-merge-20260815.db`）：556 位中 496 位改为日文规范名，写入 980 条别名（罗马字、假名、曾用名）、496 条外部引用，缓存高清头像 498 张（14 → 512）。完整性 `ok`、外键违规 0、资产数 81,847 不变；实体 606 → 604。
- 名字取自 r18 `combined=` 端点的罗马字精确回配（425 位），av-wiki 的 URL slug 回配补 63 位，javdb 多番号交集补 6 位，双源确认 9 位。r18 记录的是拍摄当时的艺名，av-wiki 用于纠正到现用艺名，旧名一律降为别名。
- 头像来自 Gfriends 图库（10.7 万张、51 个质量分档目录），门槛为长边 ≥500 且短边 ≥300。竖构图人像不能套方图的短边 512 门槛，否则会拒掉 `0-Hand-Storage`(334×501) 与 `8-GRAPHIS`(360×508) 这些最优来源。5 位所有候选都不过门槛，宁缺毋滥。
- 撞名两组已按用户授权合并：`橋本ありな`/`新ありな` 与 `黒川さりな`/`百永さりな` 各自是同一人的新旧艺名各成一个实体。合并由 `peach.entities.merge_entity` 执行，保留作品多的一侧，四种旧称全部留作别名。
- 番号版本后缀已规范化并落库（备份 `ledger.pre-code-suffix-20260815.db`）：226 条文件名带 `-C`/`-CH`/`-UC`/`-U`/`-4K` 后缀，补齐 21 条缺失 `code`、新增 215 条标签，「中文字幕」由 18 条升到 223 条。`-C` 经证实是同一作品的另一个版本而非分卷：`abw-104.mp4` 与 `abw-104-C.mp4` 同为 12,725 秒、6.12 GB 对 9.80 GB。
- 画质后缀（`-4K`/`-FHD`）刻意不打标签，画质由 probe 从流信息推导；与现有 `code` 冲突的 2 条只报告不覆盖；UUID 文件名按整串形态排除，否则 `DCE7230C-730E-…` 会被解析成 `DCE-7230`。
- 待打标创作者板按路径结构先做了聚合筛查：56 张 pending 中 9 张是平台/群组目录（1,504 条），已标 `skip` 并记录证据；`Myfans` 下含至少 4 位不同创作者，`RiaKurumi` 实为女优且作品分属三个厂牌。其余 47 位为单一创作者，已完成 `ukiru`(343 条)、`EddyS__z`(204 条) 两位的 candidate。
- 2026-08-17 身份合并批次（备份 `ledger.pre-dupmerge-20260817.db`）：`merge_entity` 实现与测试回到主线后，按 `performer-identity-20260815.csv` 的核对结论执行——5 对同人合并（白咲碧、立花美涼、前田かおり、小花のん、丘咲エミリ，保留资产多的一侧，重复串旧写法全部留作别名）、25 位 `XX XX` 重复串 canonical_name 去重、2 个非人名 entity 删除（`画像を拡大する` 是网站 UI 文本、`Kuchiku * Reverse Bunny` 是服装词）。完成后 FK 违规 0、完整性 `ok`、performer 实体 604→597。首批执行曾留下 5 条外键孤儿行（merge_entity 原实现依赖 FK 级联，sqlite 连接默认 FK 关闭），已随代码修复一并清理。

## 验证基线

- 当前主分支基线：全量隔离 `unittest` 227 项通过，2026-08-18 于主目录当前工作区实测（入口只有 `& .\scripts\test.ps1`，不接受「只跑本批相关」的缩水口径）；版本、托盘、迁移、mDNS、媒体转码、Provider、DiskGuard、语义路由、标准 Range、Video.js、稳定时长、详情播放释放、多选、实体资料、分页性能边界、搜索历史，以及回收站的还原/彻底删除/清空与删不掉文件的降级均有测试。
- 前一生产版本已分别通过 HTTP/HTTPS health、`peach.local` 解析、真实 CloudDrive Range、桌面 1280×720 和手机 390×844 检查。本次 HLS 代码已切换生产托盘；真实资产 `31222/MIDE-981-C.mp4` 的中段 HLS 片段在严格 CA HTTPS 下返回 `200`、约 9.7 MB，响应后的临时文件已清理。尚未完成浏览器 seek 和手机 HLS 视觉验收。
- 浏览器验收不得写真实喜欢、反馈或播放数据；需要交互写入时使用隔离 ledger 副本。
- 并行 worktree 测试必须设置 `PYTHONPATH=<当前工作树>\src` 并核对 `peach.__file__`，否则 editable install 可能误加载主目录旧代码。
- 2026-08-18 重启生产托盘并复验：HTTP `/healthz` 与项目 CA 严格校验的 HTTPS `/healthz` 都返回 `0.6.1`、`db=available`，`peach.local` 解析为 `192.168.50.162`，80/443 由新托盘子进程监听。注意 Windows 上的 `curl --cacert` 走 schannel 会因「revocation status is unknown」失败，那是 schannel 对私有 CA 的吊销检查限制，不是链校验失败；改用 Python `ssl.create_default_context(cafile=...)`（`check_hostname`、`CERT_REQUIRED` 均开）可完成同等严格校验并返回 200。不得因 schannel 失败就改用 HTTP 成功来声称 HTTPS 通过。
- 本批已重启生产托盘。HTTP 与 HTTPS `/healthz` 均返回 `0.6.1`；HTTPS 使用项目 CA 严格校验，`peach.local` 解析为 `192.168.50.162`，80/443 分别由新托盘子进程监听。生产只读 Range 对 item 29297 返回 `206`、精确 `bytes 0-1048575/4590823524`；HLS plan/中段片段对 item 31222 已在 HTTPS 下通过；桌面与 390×844 的旧 direct 播放验收仍未替换为 HLS seek 验收。
- 本批在隔离服务、真实 ledger 只读条件下完成桌面默认视口与 390×844 手机验收：Prestige 总数 248 时首批只构建 48 张、追加后 96 张；桌面和手机均无横向溢出。女优页标签筛选前后头像 URL 保持不变并只重建作品区；标签页手机完成态为 169 项，四种旧模糊时长标签为 0。浏览器控制台错误/警告为 0。
- 详情播放释放和 sticky 遮挡在隔离 ledger 浏览器中验收；生产浏览器只做无写入首页/样式检查，未污染真实播放、喜欢或反馈数据。
- 2026-08-17 批代码改动（merge_entity 回归主线、sheets 色彩元数据重试、media 大小写不敏感匹配）模块级 `unittest` 全部通过：`test_entity_merge` 4 项、`test_scripts` 16 项、`test_media` 9 项等。注意：实测在工具管道里直跑 `python -m unittest discover` 全量会挂起或整会话输出消失（test_jobs 模块极快退出时竞态最明显），模块级独立运行全部通过；唯一可信入口仍是 `& .\scripts\test.ps1`。

## 下一批工作

1. 创作者板的机械识别已做完：`creator-tags-review.csv` 里 42 条 pending 全部产出 candidate（34 candidate、8 skip，见 `creator-tags-candidate-20260817.csv`），没有未覆盖的板。剩下的是用户在 `/review` 页面逐条复核，点「通过」才写 `asset_tag/asset_entity`。注意天花板：全库 7,622 条无标签视频里创作者板最多覆盖约 2,800 条，其余既无创作者也无有效番号（384 个 FC2 + 约 330 个 `WX` 业余码，三源实测零命中）。
2. 首尾帧额外抽样：识别水印、出处和 `full version available`，生成带证据的「不完整版/剪辑版」候选。首个回归样本为 115 的 `04_Stepsistercaughtmejerkingoff,deepthroat,throatpie.mp4` 片尾。
3. 补齐女优身份剩余缺口：38 位查不到日文名（多数本名已是日文，无需改动）、15 位图库未收录、5 位所有候选不过质量门槛。头像质量权重的后续档位（人脸感知裁图、清晰关键帧）仍未实现。
4. 通过官方/公开来源补齐 86 个厂牌 Logo，保留来源和质量门槛。Logo 与头像的取源方向相反：头像应取整理好的图库，Logo 是品牌标识，官网与维基才是权威来源。
5. PikPak 抽帧已可走直连：代理策略组「📦 PikPak 视频」切到 DIRECT 后实测九帧 64.2 秒、30.5 MB（走代理时为 13.7 秒、163 MB），慢约 4.7 倍但流量少约 5 倍且不占代理预算。创作者采样 88 板据此约 2.7 GB。
6. 115 抽帧失败的大小写部分已修复：`peach.media.resolve_case_insensitive` 与 `FilesystemBackend.file_for`、`scripts/sheets.py`、`scripts/probe.py` 的 worker 均已接入；2026-08-17 重跑 33 条九帧，31 成功、2 失败。这 2 条的原因已查清（见上一节）：`18349` 是 ledger 时长记错、`12510` 是片源头损坏。2026-08-18 已全部收尾：`sheets.py` 区分失败原因、`probe.py`/`sheets.py` 新增 `--asset`、`18349` 重探重抽成功、`12510` 判为坏片源并留痕，详见上一节。`sheets.py` 遇 `prim:reserved` 非法色彩元数据的重试已完成并有测试。
7. HLS `stream-plan` 和按需 TS 片段已接入现有 Video.js 内置 VHS。片段时间窗的绝对终点问题已修并已切生产（见上节）；自适应码率、多路清单、首帧/seek 的桌面与手机验收仍未完成。CloudDrive 约 100 MiB 固定块预取仍是来源层成本，服务端分片只能避免整部 MP4 Range，不会消除来源层块预取。
8. 配置并评估 Stash CommunityScrapers/元数据 Provider，确认缺口后才写新来源适配器。
9. 配置可复核的真实追更源，之后再接 APScheduler；AI 结果继续只作为候选。
10. Codex 侧封装技能：`.claude/skills/` 下的六个技能目前只有 Claude 会按 description 自动触发，
    Codex 只能靠 `AGENTS.md` 索引表主动读。由 Codex 接手时确认当前版本的技能机制与目录约定，
    封装成 Codex 侧可自动触发的形式并指向同一份 `SKILL.md`；机制不存在或确认不了就写 `未取得`，
    保留索引表回退。规范见 `docs/adr/0015-agent-context-layering.md`。

## 批处理进度（自动生成）

<!-- job-status:start -->

<!-- 由 scripts/job_status.py 生成，勿手改；数字现算于账本与产物 -->
<!-- generated 2026-08-18T08:58Z -->

- 最近自动交接：`claude` / `SessionEnd` / `other`，2026-08-18T08:58:50+00:00。
- 资产 81769 条，其中视频 24889 条。
- 待抽帧（可抽 / 缺时长待 probe / 合计）：
  - `local`：3 / 1 / 4
  - `115`：11 / 139 / 150
  - `pikpak`：4751 / 5445 / 10196
  PikPak 的策略组已可切 DIRECT：2026-08-15 实测走代理时 9 帧 163 MB / 13.7 秒，走直连时 30.5 MB / 64.2 秒——慢约 4.7 倍但流量少约 5 倍且不占代理预算。全量抽帧仍是 773 GB 量级（代理口径），按创作者采样 88 板直连约 2.7 GB。115 一直走直连，同样动作约 285 MB 一张接触表。
- 无内容标签视频 7537 条（占视频 30%）。
- `asset_tag` 来源分布：`vision_creator` 27004、`pixiv_tag` 19753、`name` 19319、`stash` 15450、`r18` 2496、`performer` 1887、`follow` 1376、`r18:performer` 1204、`javbus:performer` 49。
- 番号 1457 个，其中 1158 个有厂牌（79%）。

| 产物 | 行数 | 生成时间 | 说明 |
| --- | ---: | --- | --- |
| `code-scrape.csv` | 1104 | 08-14 16:17 | 番号刮削结果 |
| `name-clean.csv` | 287 | 08-14 16:18 | 文件名净化清单 |
| `ad-candidates.csv` | 82 | 08-14 22:53 | 广告候选（confidence 分级） |
| `disposal-candidates.csv` | 54 | 08-14 22:53 | 待处置候选（含「保留」判定） |
| `creator-tags-review.csv` | 86 | 08-15 18:35 | 创作者标签待审 |

<!-- job-status:end -->
